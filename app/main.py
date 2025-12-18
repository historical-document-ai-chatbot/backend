import os
from dotenv import load_dotenv
load_dotenv()
import firebase_admin
from app.api.routes import health_router, docs_router
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException

# Initialize Firebase Admin SDK
try:
    firebase_admin.initialize_app()
    print("Firebase App initialized!")
except ValueError:
    print("Firebase App already initialized.")

# Create FastAPI app instance
app = FastAPI(title="Historical Docs Chatbot Backend")

# Get a client for the Firestore database
db = firestore.client()


# Include routes without prefix
app.include_router(health_router, prefix="", tags=["health"])
app.include_router(docs_router, prefix="", tags=["docs"])

# Root endpoint
@app.get("/")
def root():
    return {"message": "Backend is running. Connect your frontend to /health and other endpoints."}

@app.get("/api/newspapers")
def get_newspaper_list():
    """
    Fetches a list of all newspaper documents.
    This version just returns the IDs and key metadata.
    """
    try:
        # Get all documents from the 'newspapers' collection
        docs_stream = db.collection("newspapers").stream()

        # We will collect just the IDs and key metadata
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
        # Return an error if something goes wrong
        raise HTTPException(status_code=500, detail=str(e))



# Get a specific newspaper's full JSON
@app.get("/api/newspaper/{doc_id}")
def get_newspaper_document(doc_id: str):
    """
    Fetches the full JSON data for a single document
    based on its ID (e.g., 'star_of_chile_1904-08-06').
    """
    try:
        # Get a specific document from the 'newspapers' collection
        doc_ref = db.collection("newspapers").document(doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            # If the ID doesn't exist, return a 404 error
            raise HTTPException(status_code=404, detail="Document not found")
        else:
            # Return the entire document's data as JSON
            return doc.to_dict()
    except Exception as e:
        # Catch other potential errors
        raise HTTPException(status_code=500, detail=str(e))