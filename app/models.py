from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel


# Create your models here.
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserModel(BaseModel):
    id: int
    username: str
    email: str

class Message(BaseModel):
    message: str