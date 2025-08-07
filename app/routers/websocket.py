from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app import models, schemas
import uuid
from typing import List
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from app.database import get_db
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user
from app.core.chatbot import ask_chatgpt
import jwt
import json
import os 
from app.database import manager

from dotenv import load_dotenv
load_dotenv() 

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)


router = APIRouter()

@router.websocket("/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str,
    db: Session = Depends(get_db)
):
    # Verify token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
    except jwt.PyJWTError:
        await websocket.close(code=1008)
        return
    
    # Verify session ownership
    session = db.query(models.ChatSession).filter(
        models.ChatSession.session_id == session_id,
        models.ChatSession.user_id == user_id
    ).first()
    if not session:
        await websocket.close(code=1008)
        return
    
    await manager.connect(websocket, user_id, session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Save user message
            user_message = models.ChatMessage(
                session_id=session.id,
                role="user",
                content=message_data["content"]
            )
            db.add(user_message)
            db.commit()
            
            # Get chat history
            messages = db.query(models.ChatMessage).filter(
                models.ChatMessage.session_id == session.id
            ).order_by(models.ChatMessage.created_at).all()
            
            chat_history = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            # Generate and save bot response
            bot_response = ask_chatgpt(message_data["content"], chat_history[:-1])
            
            bot_message = models.ChatMessage(
                session_id=session.id,
                role="assistant",
                content=bot_response
            )
            db.add(bot_message)
            session.updated_at = datetime.utcnow()
            db.commit()
            
            # Send bot response via WebSocket
            response_data = {
                "id": bot_message.id,
                "role": "assistant",
                "content": bot_response,
                "created_at": bot_message.created_at.isoformat()
            }
            await manager.send_personal_message(
                json.dumps(response_data), user_id, session_id
            )
            
    except WebSocketDisconnect:
        manager.disconnect(user_id, session_id)


@router.websocket("/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str,
    db: Session = Depends(get_db)
):
    # Verify token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
    except jwt.PyJWTError:
        await websocket.close(code=1008)
        return
    
    # Verify session ownership
    session = db.query(models.ChatSession).filter(
        models.ChatSession.session_id == session_id,
        models.ChatSession.user_id == user_id
    ).first()
    if not session:
        await websocket.close(code=1008)
        return
    
    await manager.connect(websocket, user_id, session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Save user message
            user_message = models.ChatMessage(
                session_id=session.id,
                role="user",
                content=message_data["content"]
            )
            db.add(user_message)
            db.commit()
            
            # Get chat history
            messages = db.query(models.ChatMessage).filter(
                models.ChatMessage.session_id == session.id
            ).order_by(models.ChatMessage.created_at).all()
            
            chat_history = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            # Generate and save bot response
            bot_response = ask_chatgpt(message_data["content"], chat_history[:-1])
            
            bot_message = models.ChatMessage(
                session_id=session.id,
                role="assistant",
                content=bot_response
            )
            db.add(bot_message)
            session.updated_at = datetime.utcnow()
            db.commit()
            
            # Send bot response via WebSocket
            response_data = {
                "id": bot_message.id,
                "role": "assistant",
                "content": bot_response,
                "created_at": bot_message.created_at.isoformat()
            }
            await manager.send_personal_message(
                json.dumps(response_data), user_id, session_id
            )
            
    except WebSocketDisconnect:
        manager.disconnect(user_id, session_id)