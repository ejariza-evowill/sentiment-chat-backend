from app.utils.databaseManager import get_db
from app.models import User, UserCreate, Message, UserModel
from app.config import EMAIL_REGEX
from fastapi.responses import JSONResponse
from fastapi import APIRouter
from fastapi import Depends
from typing import List
import re

router = APIRouter(tags=["User"], prefix="/api")

@router.get("/user/all", response_model=List[UserModel], name="Get all Users")
def get_user(db = Depends(get_db)):
    users = db.query(User).all()
    users_list = [{"id": user.id, "username": user.username, "email": user.email} for user in users]
    return users_list

@router.post("/user", status_code=201, response_model= Message , name="Create User",
             responses={
                 400: {"model": Message}, 
                 409: {"model": Message}
                 })
def create_user(user: UserCreate,db = Depends(get_db)):
    # Check if the username contains only alphanumeric characters
    if not user.username.isalnum():
        return JSONResponse(status_code=400, content={"message":"Username must contain only alphanumeric characters"})

    # Check the email format with regex
    if not re.match(EMAIL_REGEX, user.email):
        return JSONResponse(status_code=400, content={"message":"Invalid email format"})
    
    # Check if the username is already taken
    if db.query(User).filter(User.username == user.username).first():
        return JSONResponse(status_code=409, content={"message":"Username already taken"})
    
    # Check if the email is already taken
    if db.query(User).filter(User.email == user.email).first():
        return JSONResponse(status_code=409, content={"message":"Email already taken"})

    # Create the new user
    new_user = User(username=user.username, email=user.email, password=user.password)
    
    # Add the user to the database
    db.add(new_user)
    db.commit()
    print(new_user.username)
    return {'message': 'User created successfully'}
