from app.models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="module")
def db():
    # Create a new session and add the user
    session = SessionLocal()
    
    user1 = User(username="test", email="test@test.test", password="testpassword")
    session.add(user1)
    session.commit()
    
    return session

def test_unique_email(db):
    # Try to add a user with the same email
    try:
        user2 = User(username="user", email="test@test.test", password="password")
        db.add(user2)
        db.commit()
        pytest.fail("Should have raised an exception for duplicate email")
    except Exception as e:
        assert "UNIQUE constraint failed: users.email" in str(e)
    finally:
        db.rollback()
        db.close()

def test_unique_username(db):
    # Try to add a user with the same username
    try:
        user = User(username="test", email="unique@test.com", password="password")
        db.add(user)
        db.commit()
        pytest.fail("Should have raised an exception for duplicate username")
    except Exception as e:
        assert "UNIQUE constraint failed: users.username" in str(e)
    finally:
        db.rollback()
        db.close()
    
