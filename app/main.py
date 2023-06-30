from app.utils.databaseManager import init_database
from app.routes import user, chat
from fastapi import FastAPI
from app.config import DATABASE_URL


app = FastAPI()

#Configuring and initializing the database
init_database(DATABASE_URL)

# Include the routers
app.include_router(user.router)
app.include_router(chat.router)