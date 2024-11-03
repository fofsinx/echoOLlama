from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

class MessageType(Enum):
    """WebSocket message types from documentation"""
    # Session events
    SESSION_UPDATE = "session.update"
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    
    # Audio buffer events
    AUDIO_APPEND = "input_audio_buffer.append"
    AUDIO_COMMIT = "input_audio_buffer.commit"
    AUDIO_CLEAR = "input_audio_buffer.clear"
    AUDIO_COMMITTED = "input_audio_buffer.committed"
    AUDIO_CLEARED = "input_audio_buffer.cleared"
    
    # Conversation events
    CONVERSATION_CREATE = "conversation.item.create"
    CONVERSATION_TRUNCATE = "conversation.item.truncate"
    CONVERSATION_DELETE = "conversation.item.delete"
    
    # Response events
    RESPONSE_CREATE = "response.create"
    RESPONSE_CANCEL = "response.cancel"
    RESPONSE_CONTENT_PART_ADDED = "response.content_part.added"
    RESPONSE_CONTENT_PART_DONE = "response.content_part.done"
    RESPONSE_FUNCTION_CALL_ARGS_DONE = "response.function_call_arguments.done"
    
    # Rate limit events
    RATE_LIMITS_UPDATED = "rate_limits.updated"

@dataclass
class SessionConfig:
    """Session configuration from documentation"""
    modalities: List[str]
    id: str
    voice: str
    instructions: Optional[str] = None
    input_audio_format: str = "pcm16"
    output_audio_format: str = "pcm16"
    input_audio_transcription: Optional[Dict] = None
    turn_detection: Optional[Dict] = None
    tools: List[Dict] = None
    tool_choice: str = "auto"
    temperature: float = 0.8
    max_response_output_tokens: Union[int, str] = "inf"

@dataclass
class WebSocketEvent:
    """Base WebSocket event structure"""
    event_id: str
    type: MessageType
    data: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class ContentPart:
    """Content part structure for responses"""
    type: str  # "text" or "audio"
    text: Optional[str] = None
    audio: Optional[str] = None  # Base64 encoded
    transcript: Optional[str] = None