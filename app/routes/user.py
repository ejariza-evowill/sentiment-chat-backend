import re
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from app.config import EMAIL_REGEX, REFRESH_TOKEN_SECRET
from app.models import (Message, Session,
                        User, UserCreate, UserLogin, UserModel)
from app.utils.databaseManager import get_db
from app.utils.SessionTokenManager import (create_access_token,
                                           create_refresh_token,
                                           get_payload_from_token)

router = APIRouter(tags=["User"], prefix="/api")


def authenticate_user(request: Request, db=Depends(get_db)):
    # Get the username from the access token
    try:
        access_token = request.cookies.get("access_token")
        payload = get_payload_from_token(access_token)
        username = payload.get("sub")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    if not username:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    # Query the database to get the user by username
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    session = db.query(Session).\
        filter(Session.username == user.username).\
        first()

    if not session:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    # Check if the access token has expired
    if session.access_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=401, detail="Token expired, please login again")

    return user


@router.get("/user/all", response_model=List[UserModel], name="Get all Users")
def get_user(db=Depends(get_db), user: User = Depends(authenticate_user)):
    users = db.query(User).all()
    users_list = [{"id": user.id, "username": user.username,
                   "email": user.email} for user in users]
    return users_list


@router.post("/user", status_code=201, response_model=Message,
             name="Create User",
             responses={
                 400: {"model": Message},
                 409: {"model": Message}
             })
def create_user(user: UserCreate, db=Depends(get_db)):
    # Check if the username contains only alphanumeric characters
    if not user.username.isalnum():
        return JSONResponse(
            status_code=400,
            content={"detail":
                     "Username must contain only alphanumeric characters"}
        )

    # Check the email format with regex
    if not re.match(EMAIL_REGEX, user.email):
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid email format"}
        )

    # Check if the username is already taken
    if db.query(User).filter(User.username == user.username).first():
        return JSONResponse(
            status_code=409,
            content={"detail": "Username already taken"}
        )

    # Check if the email is already taken
    if db.query(User).filter(User.email == user.email).first():
        return JSONResponse(
            status_code=409,
            content={"detail": "Email already taken"}
        )

    # Create the new user
    new_user = User(username=user.username,
                    email=user.email,
                    password=user.password)

    # Add the user to the database
    db.add(new_user)
    db.commit()
    print(new_user.username)
    return {'detail': 'User created successfully'}


@router.post("/login", response_model=Message, name="User Login")
def user_login(userData: UserLogin, response: Response, db=Depends(get_db)):
    username, password = userData.username, userData.password

    # Check if the user exists
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=401, detail="Incorrect username or password")

    # Check if the password is correct
    if not user.password == password:
        raise HTTPException(
            status_code=401, detail="Incorrect username or password")

    # Generate access and refresh tokens
    access_token, access_token_expires = create_access_token(
        {"sub": user.username})
    refresh_token, refresh_token_expires = create_refresh_token(
        {"sub": user.username})

    # Save the tokens in the database
    session = db.query(Session).filter(
        Session.username == user.username).first()
    if session:
        session.access_token = access_token
        session.refresh_token = refresh_token
        session.access_token_expires = access_token_expires
        session.refresh_token_expires = refresh_token_expires
    else:
        new_session = Session(
            username=user.username,
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires=access_token_expires,
            refresh_token_expires=refresh_token_expires
        )
        db.add(new_session)

    db.commit()

    # Set the access token in the response cookie
    response.set_cookie(key="access_token", value=access_token,
                        httponly=True, expires=access_token_expires)
    response.set_cookie(key="refresh_token", value=refresh_token,
                        httponly=True, expires=refresh_token_expires)

    return {"detail": "Login successful"}


@router.post("/logout", response_model=Message, name="User Logout")
def user_logout(response: Response,
                user: User = Depends(authenticate_user),
                db=Depends(get_db)):

    # Delete the session from the database
    session = db.query(Session).filter(
        Session.username == user.username).first()
    if session:
        db.delete(session)
        db.commit()

    # Delete the access and refresh tokens from the response cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"detail": "User logged out successfully"}


@router.post("/refresh", response_model=Message, name="Refresh Token")
def refresh_token(response: Response, request: Request, db=Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    try:
        payload = get_payload_from_token(
            refresh_token, secret=REFRESH_TOKEN_SECRET)
        username = payload.get("sub")
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"detail": str(e)}
        )

    if not username:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid Credentials"}
        )

    # Query the database to get the user by username
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid Credentials"}
        )

    # Check if the user has a session
    session = db.query(Session).filter(
        Session.username == user.username).first()
    if not session:
        return JSONResponse(
            status_code=401,
            content={"detail": "Session not found, please login again"}
        )

    # Check if the refresh token has expired
    if session.refresh_token_expires < datetime.utcnow():
        return JSONResponse(
            status_code=401,
            content={"detail": "Token expired, please login again"}
        )

    # Check if the refresh token is not the same as the one in the database
    if not session.refresh_token == refresh_token:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid Credentials, please login again"}
        )

    # Generate new access and refresh tokens
    access_token, access_token_expires = create_access_token(
        {"sub": user.username})

    # Save the tokens in the database
    session.access_token = access_token
    session.access_token_expires = access_token_expires
    db.commit()

    # Set the access token in the response cookie
    response.set_cookie(key="access_token", value=access_token,
                        httponly=True, expires=access_token_expires)

    return {"detail": "Token refreshed successfully"}
