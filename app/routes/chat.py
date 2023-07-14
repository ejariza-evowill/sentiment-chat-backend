from fastapi import APIRouter

router = APIRouter(tags=["Chat"], prefix="/api")

@router.get("/chat")
def get_chat():
    return {"chat": "This is a chat"}