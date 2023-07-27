from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL
from app.models import Base
from app.routes import chat, email, user
from app.utils.databaseManager import init_database

app = FastAPI()

#Configuring and initializing the database
init_database(DATABASE_URL)

# Include the routers
app.include_router(user.router)
app.include_router(chat.router)
app.include_router(email.router)
