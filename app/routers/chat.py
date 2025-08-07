from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app import models, schemas
import uuid
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user
from app.core.chatbot import ask_chatgpt

router = APIRouter()

@router.post("/sessions", response_model=schemas.ChatSessionResponse)
def create_chat_session(
    session: schemas.ChatSessionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_session = models.ChatSession(
        title=session.title,
        user_id=current_user.id,
        session_id=str(uuid.uuid4())
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/sessions", response_model=List[schemas.ChatSessionResponse])
def get_chat_sessions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(models.ChatSession).filter(
        models.ChatSession.user_id == current_user.id
    ).order_by(models.ChatSession.updated_at.desc()).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=schemas.ChatSessionResponse)
def get_chat_session(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.session_id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session

@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.session_id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Delete associated messages
    db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session.id).delete()
    db.delete(session)
    db.commit()
    return {"message": "Chat session deleted successfully"}

# Chat message endpoints
@router.post("/sessions/{session_id}/messages", response_model=schemas.ChatMessageResponse)
def send_message(
    session_id: str,
    message: schemas.ChatMessageCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify session ownership
    session = db.query(models.ChatSession).filter(
        models.ChatSession.session_id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Save user message
    user_message = models.ChatMessage(
        session_id=session.id,
        role="user",
        content=message.content
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Get chat history for context
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session.id
    ).order_by(models.ChatMessage.created_at).all()
    
    chat_history = [{"role": msg.role, "content": msg.content} for msg in messages]
    
    # Generate bot response
    # bot_response = ask_chatgpt(message.content, chat_history[:-1])  # Exclude the just-added message
    reply, saved_message = ask_chatgpt(message.content, chat_history=None, session_id=session_id, db=db)
    bot_response = reply

    # Save bot response
    bot_message = models.ChatMessage(
        session_id=session.id,
        role="assistant",
        content=bot_response
    )
    db.add(bot_message)
    
    # Update session
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot_message)
    
    return bot_message

@router.get("/sessions/{session_id}/messages", response_model=List[schemas.ChatMessageResponse])
def get_chat_messages(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.session_id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session.id
    ).order_by(models.ChatMessage.created_at).all()
    
    return messages

@router.delete("/sessions/{session_id}/messages/{message_id}")
def delete_message(
    session_id: str,
    message_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.session_id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    message = db.query(models.ChatMessage).filter(
        models.ChatMessage.id == message_id,
        models.ChatMessage.session_id == session.id
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db.delete(message)
    db.commit()
    return {"message": "Message deleted successfully"}