from fastapi import FastAPI
from app.api.routes import health_router, docs_router

app = FastAPI(title="Historical Docs Chatbot Backend")

# Include routes without prefix
app.include_router(health_router, prefix="", tags=["health"])
app.include_router(docs_router, prefix="", tags=["docs"])

# Root endpoint
@app.get("/")
def root():
    return {"message": "Backend is running. Connect your frontend to /health and other endpoints."}