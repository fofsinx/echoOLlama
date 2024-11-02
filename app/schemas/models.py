from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union, Literal
from uuid import uuid4

from pydantic import BaseModel, Field
from pydantic.main import IncEx

from app.schemas.constants import DefaultValues, ObjectTypes


class BaseModelM(BaseModel):
    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        data.pop('created_at', None)
        data.pop('updated_at', None)
        return data

    class Config:
        fields = {'created_at': {'exclude': True}, 'updated_at': {'exclude': True}}


model_t = TypeVar('T', bound=BaseModelM)


# Enums
class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ResponseStatus(str, Enum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    IN_PROGRESS = "in_progress"


# Base Models
class TimestampedModel(BaseModelM):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IdentifiedModel(BaseModelM):
    id: str = Field(default_factory=lambda: str(uuid4()))

    class Config:
        from_attributes = True


class BaseDBModel(IdentifiedModel, TimestampedModel):
    pass


# Rate Limit Models
class RateLimitBase(BaseModelM):
    name: str
    limit: int
    remaining: int
    reset_seconds: float


class RateLimitCreate(RateLimitBase):
    session_id: str


class RateLimit(RateLimitBase, BaseDBModel):
    session_id: str


# Session Models
class SessionBase(BaseModelM):
    object_type: str = ObjectTypes.SESSION
    model: str = DefaultValues.MODEL
    modalities: List[str] = Field(default_factory=lambda: DefaultValues.MODALITIES.copy())
    instructions: str = ""
    voice: str = DefaultValues.VOICE
    input_audio_format: str = DefaultValues.AUDIO_FORMAT
    output_audio_format: str = DefaultValues.AUDIO_FORMAT
    input_audio_transcription: Dict[str, str] = Field(default_factory=dict)
    turn_detection: Dict[str, Union[str, float, int]] = Field(
        default_factory=lambda: DefaultValues.TURN_DETECTION.copy()
    )
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: str = DefaultValues.TOOL_CHOICE
    temperature: float = DefaultValues.TEMPERATURE
    max_response_output_tokens: str = DefaultValues.MAX_TOKENS


class SessionCreate(SessionBase):
    pass


class SessionSchema(SessionBase, BaseDBModel):
    rate_limits: List[RateLimit] = Field(default_factory=list)


# Conversation Models
class ConversationItemBase(BaseModelM):
    role: MessageRole
    content: Dict[str, Any]
    audio_start_ms: Optional[int] = None
    audio_end_ms: Optional[int] = None


class ConversationItemCreate(ConversationItemBase):
    conversation_id: str


class ConversationItem(ConversationItemBase, BaseDBModel):
    conversation_id: str


class ConversationBase(BaseModelM):
    object_type: str = ObjectTypes.CONVERSATION
    session_id: str


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase, BaseDBModel):
    items: List[ConversationItem] = Field(default_factory=list)


# Response Models
class ResponseBase(BaseModelM):
    object_type: str = ObjectTypes.RESPONSE
    status: ResponseStatus
    conversation_id: str
    total_tokens: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    input_token_details: Optional[Dict[str, Any]] = None
    output_token_details: Optional[Dict[str, Any]] = None
    status_details: Optional[Dict[str, Any]] = None


class ResponseCreate(ResponseBase):
    pass


class Response(ResponseBase, BaseDBModel):
    pass


# Generic API Response Models
T = TypeVar('T')


class BaseAPIResponse(BaseModelM):
    message: str


class DataResponse(BaseAPIResponse, Generic[T]):
    data: T


# Specific API Response Models
class SessionResponse(DataResponse[SessionSchema]):
    message: str = "Session created successfully"


class ConversationResponse(DataResponse[Conversation]):
    message: str = "Conversation created successfully"


class ResponseResponse(DataResponse[Response]):
    message: str = "Response created successfully"


class RateLimitResponse(DataResponse[RateLimit]):
    message: str = "Rate limit updated successfully"


# Error Models
class ErrorDetail(BaseModelM):
    loc: Optional[List[str]] = None
    msg: str
    type: str


class ErrorResponse(BaseModelM):
    error: str
    details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None
    status_code: int = 400


# WebSocket Models
class WSMessage(BaseModelM):
    type: str
    data: Dict[str, Any]


class WSResponse(BaseModelM):
    type: str
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
