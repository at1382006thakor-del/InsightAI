import uvicorn
import os
import sys

# Ensure backend folder is in the python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Launching InsightAI REST API on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
