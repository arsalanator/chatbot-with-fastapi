# from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from database import Base

# class User(Base):
#     __tablename__ = "users"
    
#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True, nullable=False)
#     username = Column(String, index=True, nullable=False)
#     hashed_password = Column(String, nullable=False)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
#     # Relationship to chat sessions
#     chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

# class ChatSession(Base):
#     __tablename__ = "chat_sessions"
    
#     id = Column(Integer, primary_key=True, index=True)
#     session_id = Column(String, unique=True, index=True, nullable=False)  # UUID for external reference
#     title = Column(String, nullable=False)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
#     # Relationships
#     user = relationship("User", back_populates="chat_sessions")
#     messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

# class ChatMessage(Base):
#     __tablename__ = "chat_messages"
    
#     id = Column(Integer, primary_key=True, index=True)
#     session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
#     role = Column(String, nullable=False)  # 'user' or 'assistant'
#     content = Column(Text, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
    
#     # Relationship
#     session = relationship("ChatSession", back_populates="messages")


import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, index=True)
    hashed_password = Column(String)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)  # To store both plain strings and serialized lists/dicts
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession")
