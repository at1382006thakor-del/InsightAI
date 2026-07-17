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

def local_query_parser(user_msg: str) -> tuple[Optional[str], Optional[dict], str]:
    msg = user_msg.lower()
    
    # 1. Total sales / revenue
    if any(k in msg for k in ["total sales", "total revenue", "overall revenue", "how much revenue", "sales revenue", "profit"]):
        sql = "SELECT SUM(revenue) as total_revenue, SUM(profit) as total_profit, COUNT(sale_id) as total_orders FROM sales WHERE sales.dataset_id = :dataset_id"
        explanation = "I analyzed the database and calculated the overall sales performance metrics (Revenue, Profit, and Orders)."
        return sql, None, explanation
        
    # 2. Sales / Revenue by category
    elif "category" in msg or "categories" in msg:
        sql = """
        SELECT products.category as category, SUM(sales.revenue) as revenue, SUM(sales.profit) as profit 
        FROM sales 
        JOIN products ON sales.product_id = products.product_id 
        WHERE sales.dataset_id = :dataset_id AND products.dataset_id = :dataset_id
        GROUP BY products.category 
        ORDER BY revenue DESC
        """
        chart_config = {
            "type": "bar",
            "xKey": "category",
            "yKey": "revenue"
        }
        explanation = "Here is the breakdown of sales revenue and profit across different product categories."
        return sql, chart_config, explanation

    # 3. Sales / Revenue by region
    elif "region" in msg or "regions" in msg:
        sql = """
        SELECT region, SUM(revenue) as revenue, SUM(profit) as profit 
        FROM sales 
        WHERE dataset_id = :dataset_id 
        GROUP BY region 
        ORDER BY revenue DESC
        """
        chart_config = {
            "type": "bar",
            "xKey": "region",
            "yKey": "revenue"
        }
        explanation = "Here is the breakdown of sales revenue by geographic region."
        return sql, chart_config, explanation

    # 4. Top products
    elif "top product" in msg or "best selling product" in msg or "popular product" in msg or "top products" in msg or "products" in msg:
        sql = """
        SELECT products.name as product_name, SUM(sales.revenue) as revenue, SUM(sales.quantity) as quantity_sold 
        FROM sales 
        JOIN products ON sales.product_id = products.product_id 
        WHERE sales.dataset_id = :dataset_id AND products.dataset_id = :dataset_id
        GROUP BY products.name 
        ORDER BY revenue DESC 
        LIMIT 5
        """
        chart_config = {
            "type": "bar",
            "xKey": "product_name",
            "yKey": "revenue"
        }
        explanation = "Here are the top 5 products based on generated revenue."
        return sql, chart_config, explanation

    # 5. Monthly trend / timeline / time series
    elif any(k in msg for k in ["trend", "monthly", "timeline", "over time", "time-series", "daily", "date"]):
        sql = """
        SELECT order_date as date, SUM(revenue) as revenue, SUM(profit) as profit 
        FROM sales 
        WHERE dataset_id = :dataset_id 
        GROUP BY order_date 
        ORDER BY order_date ASC
        """
        chart_config = {
            "type": "line",
            "xKey": "date",
            "yKey": "revenue"
        }
        explanation = "Here is the sales revenue trend over time."
        return sql, chart_config, explanation

    # 6. Customer segments
    elif "segment" in msg or "segments" in msg or "customer type" in msg or "customer" in msg or "customers" in msg:
        sql = """
        SELECT customers.segment as segment, SUM(sales.revenue) as revenue, COUNT(sales.sale_id) as orders 
        FROM sales 
        JOIN customers ON sales.customer_id = customers.customer_id 
        WHERE sales.dataset_id = :dataset_id AND customers.dataset_id = :dataset_id
        GROUP BY customers.segment
        ORDER BY revenue DESC
        """
        chart_config = {
            "type": "bar",
            "xKey": "segment",
            "yKey": "revenue"
        }
        explanation = "Here is the breakdown of sales revenue by customer segment."
        return sql, chart_config, explanation

    # Default natural explanation
    explanation = f"I am ready to assist you. Ask me about total sales, sales by category, regional sales, top products, customer segments, or monthly trends to query your database."
    return None, None, explanation

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
    
    text_reply = None
    sql = None
    chart_config = None

    if api_key:
        if api_key.startswith("sk-or-") or api_key.startswith("sk-"):
            # OpenRouter flow
            try:
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                
                messages = [{"role": "system", "content": DB_SCHEMA_PROMPT}]
                history = chat_repo.get_messages(conversation_id)
                for h in history[:-1]:
                    role = "user" if h.sender == "user" else "assistant"
                    messages.append({"role": role, "content": h.message})
                messages.append({"role": "user", "content": f"User Question: {user_msg}"})
                
                payload = {
                    "model": "google/gemini-2.5-flash",
                    "messages": messages,
                }
                
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    res_json = response.json()
                    text_reply = res_json["choices"][0]["message"]["content"]
                    sql, chart_config, clean_explanation = parse_llm_response(text_reply)
                    text_reply = clean_explanation
                else:
                    print(f"OpenRouter returned status {response.status_code}: {response.text}")
            except Exception as e:
                print(f"OpenRouter request exception: {str(e)}")
        else:
            # Native Gemini flow
            try:
                client = genai.Client(api_key=api_key)
                history = chat_repo.get_messages(conversation_id)
                contents = []
                for h in history[:-1]:
                    role = "user" if h.sender == "user" else "model"
                    contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=h.message)]
                        )
                    )
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
                sql, chart_config, clean_explanation = parse_llm_response(text_reply)
                text_reply = clean_explanation
            except Exception as e:
                print(f"Native Gemini request exception: {str(e)}")

    # If API keys are not configured or both API routes failed, use smart local QA parser fallback
    if text_reply is None:
        sql, chart_config, clean_explanation = local_query_parser(user_msg)
        text_reply = clean_explanation
        if sql:
            text_reply += "\n\n*(InsightAI local analysis engine: generated query from your question)*"

    final_reply = text_reply
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
