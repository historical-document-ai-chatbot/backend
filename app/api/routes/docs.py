
from fastapi import APIRouter

router = APIRouter()

@router.get("/docs-info")
def docs_info():
    return {"message": "This is the docs endpoint. Add more routes here later."}