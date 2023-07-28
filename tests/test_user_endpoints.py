import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient
from freezegun import freeze_time

from app.config import TEST_DATABASE_URL, ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE
from app.main import app
from app.models import Base, User, Session
from app.utils.databaseManager import get_db
from app.utils.SessionTokenManager import create_access_token, create_refresh_token

engine = create_engine(TEST_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_testing():
    engine = create_engine(TEST_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# Create a test client for the FastAPI app and override the get_db dependency
app.dependency_overrides[get_db] = get_db_testing

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    # Create a new session and add the user
    session = SessionLocal()
    return session

@pytest.fixture(autouse=True)
def setUp_db(request):
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def tearDown_db():
        Base.metadata.drop_all(bind=engine)
    db = SessionLocal()

    user1 = User(username="test", email="test@test.test", password="testpassword")
    db.add(user1)
    db.commit()
    db.close()
    request.addfinalizer(tearDown_db)


def test_create_user():
    path = app.url_path_for("Create User")

    #Successful user creation
    response = client.post(
        path,
        json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "newpassword"
        }
    )
    assert response.status_code == 201
    assert response.json() == {"detail": "User created successfully"}
    
    #Username already taken
    response = client.post(
        path,
        json={
            "username": "newuser",
            "email": "other@test.com",
            "password": "newpassword"
        }
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "Username already taken"}

    #Email already taken
    response = client.post(
        path,
        json={
            "username": "otheruser",
            "email": "test@test.test",
            "password": "newpassword"
        }
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "Email already taken"}

    #Invalid email format
    response = client.post(
        path,
        json={
            "username": "otheruser",
            "email": "newuser",
            "password": "newpassword"
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid email format"}

    #Username must contain only alphanumeric characters
    response = client.post(
        path,
        json={
            "username": "otheruser!",
            "email": "other@test.com",
            "password": "newpassword"
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username must contain only alphanumeric characters"}

def test_get_all_users():
    #Getting path for endpoints
    get_users = app.url_path_for("Get all Users")
    login = app.url_path_for("User Login")

    #Trying to get all users without logging in
    response = client.get(get_users)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}

    #Logging in
    response = client.post(login, json={"username": "test", "password": "testpassword"})
    assert response.status_code == 200
    access_token = response.cookies.get("access_token")
    assert access_token
    refresh_token = response.cookies.get("refresh_token")
    assert refresh_token

    #Setting cookies
    client.cookies["access_token"] = access_token
    client.cookies["refresh_token"] = refresh_token

    #Getting all users
    response = client.get(get_users)
    assert response.json() == [
        {
            "id": 1,
            "username": "test",
            "email": "test@test.test"
        }
    ]

def test_login_logout(db):
    #Getting path for endpoints
    login = app.url_path_for("User Login")
    logout = app.url_path_for("User Logout")

    #Logging in with wrong password
    response = client.post(login, json={"username": "test", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

    #Logging in with wrong user
    response = client.post(login, json={"username": "wronguser", "password": "testpassword"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

    #Logging in 
    response = client.post(login, json={"username": "test", "password": "testpassword"})
    assert response.status_code == 200
    now = datetime.now(timezone.utc)
    access_token = response.cookies.get("access_token")
    assert access_token
    refresh_token = response.cookies.get("refresh_token")
    assert refresh_token

    userSession = db.query(Session).filter(Session.username == "test").first()

    #Comparing tokens
    assert access_token == userSession.access_token
    assert refresh_token == userSession.refresh_token

    #Logging out
    response = client.post(logout)
    assert response.status_code == 200
    assert response.json() == {"detail": "User logged out successfully"}

    #Checking if the tokens have been deleted
    assert not response.cookies.get("access_token")
    assert not response.cookies.get("refresh_token")

    #Checking if the session has been deleted
    userSession = db.query(Session).filter(Session.username == "test").first()

    assert not userSession

def test_expiration_token(db):
    #Getting path for endpoints
    login = app.url_path_for("User Login")
    get_users = app.url_path_for("Get all Users")
    refresh = app.url_path_for("Refresh Token")
    logout = app.url_path_for("User Logout")

    #Logging in
    response = client.post(login, json={"username": "test", "password": "testpassword"})
    assert response.status_code == 200
    access_token = response.cookies.get("access_token")
    assert access_token
    refresh_token = response.cookies.get("refresh_token")
    assert refresh_token

    #Setting cookies
    client.cookies["access_token"] = access_token
    client.cookies["refresh_token"] = refresh_token

    with freeze_time(datetime.now(timezone.utc)+timedelta(hours=ACCESS_TOKEN_EXPIRE, seconds=1)):
        #Trying to get all users with expired access token
        response = client.get(get_users)
        assert response.status_code == 401
        assert response.json() == {"detail": "Signature has expired"}

    with freeze_time(datetime.now(timezone.utc)+timedelta(hours=REFRESH_TOKEN_EXPIRE, seconds=1)):
        #Trying to get all users with expired refresh token
        response = client.get(get_users)
        assert response.status_code == 401
        assert response.json() == {"detail": "Signature has expired"}

        #Trying to refresh the tokens with expired refresh token
        response = client.post(refresh)
        assert response.status_code == 401
        assert response.json() == {"detail": "Token expired, please login again"}

        #Trying to logout with expired refresh token
        response = client.post(logout)
        assert response.status_code == 401
        assert response.json() == {"detail": "Signature has expired"}

def test_refresh_token(db):
    #Getting path for endpoints
    login = app.url_path_for("User Login")
    get_users = app.url_path_for("Get all Users")
    refresh = app.url_path_for("Refresh Token")

    #Logging in
    response = client.post(login, json={"username": "test", "password": "testpassword"})
    assert response.status_code == 200
    access_token = response.cookies.get("access_token")
    assert access_token
    refresh_token = response.cookies.get("refresh_token")
    assert refresh_token
    
    #Setting cookies
    client.cookies["access_token"] = access_token
    client.cookies["refresh_token"] = refresh_token

    with freeze_time(datetime.now(timezone.utc)+timedelta(hours=ACCESS_TOKEN_EXPIRE, seconds=1)):
        #Trying to get all users with expired access token
        response = client.get(get_users)
        assert response.status_code == 401
        assert response.json() == {"detail": "Signature has expired"}

        #Refreshing the tokens
        response = client.post(refresh)
        assert response.status_code == 200
        access_token = response.cookies.get("access_token")
        assert access_token

        #Setting cookies
        client.cookies["access_token"] = access_token

        #Trying to get all users with refreshed tokens
        response = client.get(get_users)
        assert response.status_code == 200
        assert response.json() == [
            {
                "id": 1,
                "username": "test",
                "email": "test@test.test"
            }
        ]
