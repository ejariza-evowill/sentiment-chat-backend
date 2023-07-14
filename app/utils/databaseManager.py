from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

SessionLocal = None


def init_database(DATABASE_URL):
    global SessionLocal

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

def get_db():
    global SessionLocal
    
    if SessionLocal is None:
        init_database()

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()