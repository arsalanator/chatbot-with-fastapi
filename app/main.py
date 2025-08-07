from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
from datetime import datetime, timedelta
import jwt
import bcrypt
import uuid
import json

from app.database import get_db, engine
import app.models as models
import app.schemas as schemas
from .routers import auth, chat, websocket

from typing import List
from .database import manager
# from app.chatbot import ask_chatgpt

# Create tables
models.Base.metadata.create_all(bind=engine)


# REFACTORED
app = FastAPI(title="Chatbot API", version="1.0.0")

# # CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the chatbot router
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/chat", tags=["Chatbot"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSockets"])


# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)