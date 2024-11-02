import enum
from typing import Any, Type, TypeVar
import uuid

from pydantic import BaseModel
from sqlalchemy import TIMESTAMP, Column, Float, String, Integer, ForeignKey, JSON, Enum, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from app.utils.logger import logger
from sqlalchemy.dialects import postgresql

Base = declarative_base()


class MessageRole(enum.Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

    @classmethod
    def as_pg_enum(cls):
        return postgresql.ENUM(
            'system', 'user', 'assistant', 'function',
            name='message_role',
            create_type=True
        )


class ResponseStatus(enum.Enum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    IN_PROGRESS = "in_progress"

    @classmethod
    def as_pg_enum(cls):
        return postgresql.ENUM(
            'completed', 'cancelled', 'failed', 'incomplete', 'in_progress',
            name='response_status',
            create_type=True  # Important: don't create type in SQLAlchemy
        )


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    object_type = Column(String, default="realtime.session")
    model = Column(String, default="llama3.1")
    modalities = Column(JSON, default=["text", "audio"])  # Array of strings
    instructions = Column(String, default="")
    voice = Column(String, default='alloy')
    input_audio_format = Column(String, default='pcm16')
    output_audio_format = Column(String, default='pcm16')
    input_audio_transcription = Column(JSON, default={
        'model': 'whisper-1',
        'language': 'en',
    })
    turn_detection = Column(JSON, nullable=True, default={
        "type": "server_vad",
        "threshold": 0.5,
        "prefix_padding_ms": 300,
        "silence_duration_ms": 500
    })
    tools = Column(JSON)  # Array of tools
    tool_choice = Column(String, default="auto")
    temperature = Column(Float, default=0.7)
    max_response_output_tokens = Column(String, default="inf")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    conversations = relationship("Conversation", back_populates="session")
    rate_limits = relationship(
        "RateLimit", 
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin"  # For better performance when loading related rate limits
    )

    def __repr__(self):
        logger.info("🔍 File: models.py, Line: 45, Function: __repr__, Value:", f"Session(id={self.id})")
        return f"Session(id={self.id})"


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    object_type = Column(String, default="realtime.conversation")
    session_id = Column(String, ForeignKey('sessions.id'))

    # Relationships
    session = relationship("Session", back_populates="conversations")
    items = relationship("ConversationItem", back_populates="conversation")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        logger.info("🔍 File: models.py, Line: 60, Function: __repr__, Value:", f"Conversation(id={self.id})")
        return f"Conversation(id={self.id})"


class ConversationItem(Base):
    __tablename__ = 'conversation_items'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey('conversations.id'))
    role = Column(MessageRole.as_pg_enum())
    content = Column(JSON)  # Can store both text and audio content
    audio_start_ms = Column(Integer, nullable=True)
    audio_end_ms = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="items")

    def __repr__(self):
        logger.info("🔍 File: models.py, Line: 77, Function: __repr__, Value:", f"ConversationItem(id={self.id})")
        return f"ConversationItem(id={self.id})"


class Response(Base):
    __tablename__ = 'responses'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    object_type = Column(String, default="realtime.response")
    status = Column(ResponseStatus.as_pg_enum())
    conversation_id = Column(String, ForeignKey('conversations.id'))

    # Usage statistics
    total_tokens = Column(Integer)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    input_token_details = Column(JSON)
    output_token_details = Column(JSON)

    # Status details
    status_details = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        logger.info("🔍 File: models.py, Line: 98, Function: __repr__, Value:", f"Response(id={self.id})")
        return f"Response(id={self.id})"


class RateLimit(Base):
    __tablename__ = 'rate_limits'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # 'requests', 'tokens'
    limit = Column(Integer, nullable=False)
    remaining = Column(Integer, nullable=False)
    reset_seconds = Column(Float, nullable=False)
    session_id = Column(String, ForeignKey('sessions.id'), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    session = relationship("Session", back_populates="rate_limits")

    def __repr__(self):
        logger.info("🔍 File: models.py, Line: 130, Function: __repr__, Value:", 
                   f"RateLimit(id={self.id}, name={self.name}, remaining={self.remaining}/{self.limit})")
        return f"RateLimit(id={self.id}, name={self.name}, remaining={self.remaining}/{self.limit})"


model_t = TypeVar('T', bound=BaseModel)

def to_pydantic(db_object: Any, pydantic_model: Type[model_t]) -> model_t:
    return pydantic_model(**db_object.__dict__)