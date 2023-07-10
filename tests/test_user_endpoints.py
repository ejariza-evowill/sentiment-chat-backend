import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.config import TEST_DATABASE_URL
from app.main import app
from app.models import Base, User
from app.utils.databaseManager import get_db


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
    assert response.json() == {"message": "User created successfully"}
    
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
    assert response.json() == {"message": "Username already taken"}

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
    assert response.json() == {"message": "Email already taken"}

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
    assert response.json() == {"message": "Invalid email format"}

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
    assert response.json() == {"message": "Username must contain only alphanumeric characters"}

def test_get_all_users():
    response = client.get(app.url_path_for("Get all Users"))
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "username": "test",
            "email": "test@test.test"
        }
    ]

