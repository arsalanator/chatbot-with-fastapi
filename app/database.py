# # from sqlalchemy import create_engine
# # from sqlalchemy.ext.declarative import declarative_base
# # from sqlalchemy.orm import sessionmaker
# # import os

# # # Database URL - uses PostgreSQL in production, SQLite for development
# # DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chatbot_user:chatbot_pass@localhost:5432/chatbot_database")


# # # For SQLite (alternative for local development without Docker)
# # # DATABASE_URL = "sqlite:///./chatbot.db"

# # engine = create_engine(DATABASE_URL)
# # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Base = declarative_base()

# # def get_db():
# #     db = SessionLocal()
# #     try:
# #         yield db
# #     finally:
# #         db.close()


# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# import os

# # Use SQLite by default; fallback to environment variable if set
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")

# # Set `connect_args` only for SQLite
# connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# # Create SQLAlchemy engine
# engine = create_engine(DATABASE_URL, connect_args=connect_args)

# # Create session
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Base class for models
# Base = declarative_base()

# # Dependency for DB session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()



from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect

DATABASE_URL = "sqlite:///./chatbot.db"  # Relative path
# For absolute path: sqlite:////full/path/to/chatbot.db

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, user_id: int, session_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        self.active_connections[user_id][session_id] = websocket

    def disconnect(self, user_id: int, session_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].pop(session_id, None)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int, session_id: str):
        if user_id in self.active_connections and session_id in self.active_connections[user_id]:
            await self.active_connections[user_id][session_id].send_text(message)

manager = ConnectionManager()