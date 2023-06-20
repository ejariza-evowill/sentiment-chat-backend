from fastapi import APIRouter

router = APIRouter()

@router.get("/user")
def get_user():
    return {"username": "testuser"}