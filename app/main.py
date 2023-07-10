from fastapi import FastAPI

from app.config import DATABASE_URL
from app.routes import user, chat
from app.utils.databaseManager import init_database


app = FastAPI()

#Configuring and initializing the database
init_database(DATABASE_URL)

# Include the routers
app.include_router(user.router)
app.include_router(chat.router)