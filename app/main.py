from fastapi import FastAPI

app = FastAPI()

# Import the routers
from app.routes import user, chat

# Include the routers
app.include_router(user.router)
app.include_router(chat.router)