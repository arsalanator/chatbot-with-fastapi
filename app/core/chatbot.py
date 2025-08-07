import openai
import os
import json
from dotenv import load_dotenv
from app.models import ChatMessage  # Ensure this is the correct import
from sqlalchemy.orm import Session

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def ask_chatgpt(prompt: str, chat_history=None, session_id=None, db: Session = None, model="gpt-3.5-turbo"):
    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    if chat_history:
        messages.extend(chat_history)

    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    bot_reply = response.choices[0].message.content.strip()

    # ✅ Save to DB if session_id and db are provided
    message_model = None
    if session_id and db:
        message_model = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=str(bot_reply)  # Or json.dumps(...) if storing structured response
        )
        db.add(message_model)
        db.commit()
        db.refresh(message_model)

    return bot_reply, message_model
