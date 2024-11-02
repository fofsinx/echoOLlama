from enum import Enum

class ObjectTypes(str, Enum):
    SESSION = "realtime.session"
    CONVERSATION = "realtime.conversation"
    RESPONSE = "realtime.response"

class DefaultValues:
    MODEL = "llama3.1"
    VOICE = "alloy"
    AUDIO_FORMAT = "pcm16"
    TOOL_CHOICE = "auto"
    TEMPERATURE = 0.7
    MAX_TOKENS = "inf"
    
    MODALITIES = ["text", "audio"]
    AUDIO_TRANSCRIPTION = {
        'model': 'whisper-1',
        'language': 'en',
    }
    TURN_DETECTION = {
        "type": "server_vad",
        "threshold": 0.5,
        "prefix_padding_ms": 300,
        "silence_duration_ms": 500
    }
