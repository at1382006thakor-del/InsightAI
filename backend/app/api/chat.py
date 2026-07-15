from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
import re
import json

from ..database.connection import get_db
from ..database.models import User, Conversation, Message
from ..repositories.chat_repository import ChatRepository
from ..repositories.dataset_repository import DatasetRepository
from ..services.auth_service import get_current_user
from ..services.ai_service import get_gemini_api_key

router = APIRouter(prefix="/chat", tags=["AI Conversational Assistant"])

# Prompt setup for SQL translation
DB_SCHEMA_PROMPT = """
You are a senior data analyst assistant. You write clean, read-only SQL SELECT queries to answer user questions about sales transaction logs.
The database schema consists of three tables:
1. sales: sale_id (int), order_date (date), customer_id (int), product_id (int), quantity (int), price (float), discount (float), revenue (float), profit (float), region (varchar), dataset_id (string)
2. products: product_id (int), name (varchar), category (varchar), stock (int), price (float), dataset_id (string)
3. customers: customer_id (int), name (varchar), city (varchar), state (varchar), segment (varchar), dataset_id (string)

Rules:
1. Always join tables on customer_id / product_id:
   - To query customer name/segment/city/state, JOIN customers ON sales.customer_id = customers.customer_id
   - To query product name/category, JOIN products ON sales.product_id = products.product_id
2. Always filter queries by active dataset using: `sales.dataset_id = :dataset_id` (and products.dataset_id = :dataset_id / customers.dataset_id = :dataset_id in joins).
3. If the user asks for a chart or time-series path, write the SQL query AND output a JSON block matching this structure at the very end of your response inside a ```json block:
   {
     "type": "line" | "bar",
     "xKey": "string (matching select column key)",
     "yKey": "string (matching numeric select column key)"
   }
4. Write SQL SELECT statements only. Never write INSERT, UPDATE, DELETE, DROP, ALTER, or write-based commands.
5. If the question does not require data aggregations, do not output any SQL code. Just answer naturally.
"""

def parse_llm_response(text_response: str) -> tuple[Optional[str], Optional[dict], str]:
    """Extracts SQL code block, JSON chart configuration block, and natural language text from Gemini response."""
    sql_match = re.search(r"```sql\s*(.*?)\s*```", text_response, re.DOTALL | re.IGNORECASE)
    json_match = re.search(r"```json\s*(.*?)\s*```", text_response, re.DOTALL | re.IGNORECASE)
    
    sql = sql_match.group(1).strip() if sql_match else None
    
    chart_config = None
    if json_match:
        try:
            chart_config = json.loads(json_match.group(1).strip())
        except Exception:
            pass

    # Clean text by removing code blocks
    clean_text = re.sub(r"```sql.*?```", "", text_response, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r"```json.*?```", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
    clean_text = clean_text.strip()
    
    return sql, chart_config, clean_text

@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ChatRepository(db)
    return repo.list_conversations(current_user.id)

@router.post("/conversations")
def create_conversation(
    payload: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ChatRepository(db)
    title = payload.get("title", "New Discussion")
    return repo.create_conversation(current_user.id, title)

@router.delete("/conversations/{id}")
def delete_conversation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ChatRepository(db)
    repo.delete_conversation(id)
    return {"success": True}

@router.get("/conversations/{id}/messages")
def get_conversation_messages(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = ChatRepository(db)
    return repo.get_messages(id)

@router.post("")
def chat_message(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation_id = payload.get("conversation_id")
    user_msg = payload.get("message", "").strip()

    if not conversation_id or not user_msg:
        raise HTTPException(status_code=400, detail="conversation_id and message are required fields.")

    chat_repo = ChatRepository(db)
    dataset_repo = DatasetRepository(db)
    
    # Save user message to database
    chat_repo.save_message(conversation_id, "user", user_msg)

    # 1. Fetch active dataset to scope SQL queries
    active_ds = dataset_repo.get_active_dataset()
    if not active_ds:
        # Fallback if no dataset is active: answer directly
        reply = "There are no active datasets loaded in your workspace. Please upload and clean a CSV or Excel dataset first."
        msg = chat_repo.save_message(conversation_id, "assistant", reply)
        return msg

    api_key = get_gemini_api_key()
    if not api_key:
        # Fallback if no Gemini key is saved
        reply = "Gemini API key is not configured. Please save your GEMINI_API_KEY in configuration settings to activate chat Q&A."
        msg = chat_repo.save_message(conversation_id, "assistant", reply)
        return msg

    # 2. Call Google Gemini to draft SQL / answer
    try:
        client = genai.Client(api_key=api_key)
        
        # Build conversation context history
        history = chat_repo.get_messages(conversation_id)
        contents = []
        for h in history[:-1]: # exclude the latest user message which we will prompt explicitly
            role = "user" if h.sender == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=h.message)]
                )
            )
            
        # Append latest user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"User Question: {user_msg}")]
            )
        )
        
        config = types.GenerateContentConfig(
            system_instruction=DB_SCHEMA_PROMPT
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )
        text_reply = response.text
    except Exception as e:
        reply = f"AI completions failed: {str(e)}"
        msg = chat_repo.save_message(conversation_id, "assistant", reply)
        return msg

    # 3. Parse LLM response code blocks
    sql, chart_config, clean_explanation = parse_llm_response(text_reply)

    final_reply = clean_explanation
    final_chart_data = {}

    # 4. If SQL is generated, execute securely
    if sql:
        # Strict Security Checks: Reject any modification keywords
        lower_sql = sql.lower()
        blocked_keywords = ["insert", "update", "delete", "drop", "alter", "create", "truncate", "grant"]
        if any(kw in lower_sql for kw in blocked_keywords):
            final_reply = "I cannot execute modify-based query actions for security reasons."
        else:
            try:
                # Parameterized execute scoping transactions by active dataset UUID
                result = db.execute(text(sql), {"dataset_id": active_ds.id})
                rows = [dict(r._mapping) for r in result.all()]
                
                # If we have chart config, structure the data payload for Recharts
                if chart_config and rows:
                    final_chart_data = {
                        "type": chart_config.get("type", "bar"),
                        "xKey": chart_config.get("xKey"),
                        "yKey": chart_config.get("yKey"),
                        "data": rows
                    }
                else:
                    # Append rows as formatted text summary at bottom
                    if rows:
                        rows_summary = "\n".join([str(row) for row in rows[:5]])
                        final_reply += f"\n\n**Query Results (showing top 5 rows):**\n```\n{rows_summary}\n```"
                    else:
                        final_reply += "\n\n(No matching records found in active dataset)."
            except Exception as e:
                final_reply += f"\n\n*(Failed to execute generated query: {str(e)})*"

    # 5. Save assistant response and chart payload to database
    assistant_msg = chat_repo.save_message(
        conversation_id=conversation_id,
        sender="assistant",
        message=final_reply,
        chart_metadata=final_chart_data
    )

    return assistant_msg
