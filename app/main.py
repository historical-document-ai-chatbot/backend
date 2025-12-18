import os
from dotenv import load_dotenv

# 1. Load env vars FIRST
load_dotenv()

import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException

# 2. Add these imports for Pydantic
from pydantic import BaseModel
from typing import List, Optional

from app.api.routes import health_router, docs_router
from app.services.chat_service import generate_response
from fastapi.middleware.cors import CORSMiddleware

# --- DUAL-MODE AUTHENTICATION ---
# 1. Define the path to the local key
cred_path = "app/serviceAccountKey.json"

# 2. Check if we are local or in cloud
if os.path.exists(cred_path):
    # LOCAL MODE: Use the JSON file
    cred = credentials.Certificate(cred_path)
    try:
        firebase_admin.initialize_app(cred)
        print("Initialized Firebase with Local Certificate.")
    except ValueError:
        pass  # Already initialized
else:
    # CLOUD MODE: Use Default Application Credentials (ADC)
    # Cloud Run automatically injects credentials for the service account
    try:
        firebase_admin.initialize_app()
        print("Initialized Firebase with Cloud Identity.")
    except ValueError:
        pass  # Already initialized

app = FastAPI(title="Historical Docs Chatbot Backend")
db = firestore.client()

app.include_router(health_router, prefix="", tags=["health"])
app.include_router(docs_router, prefix="", tags=["docs"])


# --- DATA MODELS ---
# Later we can move them to app/schemas.py
class ChatMessage(BaseModel):
    sender: str
    content: str
    id: Optional[str] = None
    timestamp: Optional[str] = None
    type: Optional[str] = None


class ChatRequest(BaseModel):
    newspaper_id: str
    message: str
    history: List[ChatMessage] = []


# --- ROUTES ---


@app.get("/")
def root():
    return {"message": "Backend is running."}


@app.get("/api/newspapers")
def get_newspaper_list():
    try:
        docs_stream = db.collection("newspapers").stream()
        newspaper_list = []
        for doc in docs_stream:
            data = doc.to_dict()
            newspaper_list.append(
                {
                    "id": doc.id,
                    "name": data.get("newspaper_name", "Unknown Name"),
                    "date": data.get("date", "Unknown Date"),
                }
            )
        return newspaper_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/newspaper/{doc_id}")
def get_newspaper_document(doc_id: str):
    try:
        doc_ref = db.collection("newspapers").document(doc_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    try:
        # 1. Fetch Root Document
        doc_ref = db.collection("newspapers").document(request.newspaper_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Newspaper not found")

        newspaper_data = doc.to_dict()

        # 2. Call Gemini Service
        response_text = generate_response(
            newspaper_data=newspaper_data,
            chat_history=[msg.dict() for msg in request.history],
            user_message=request.message,
        )

        return {"response": response_text}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))