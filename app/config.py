import json
from typing import Any, Tuple, Type

from app.utils.logger import logger
import os
from pydantic_settings import BaseSettings, EnvSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict
from pydantic.fields import FieldInfo

class CustomSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == 'RATE_LIMIT_REQUESTS':
            return int(value) if value else 0
        if field_name == 'RATE_LIMIT_TOKENS':
            return int(value) if value else 0

        if field_name == 'USE_CUDA':
            print(f"🔍 config.py: USE_CUDA: {value}")
            return value.lower() == 'true' if value else False
        
        if field_name == 'DEBUG':
            return value.lower() == 'true' if value else False
        
        if field_name == 'CORS_ORIGINS':
            return [origin.strip() for origin in value.split(',')] if value else []

        return json.loads(value) if value else None

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    # API Settings
    APP_NAME: str = "OLLAMAGATE"
    API_VERSION: str = "v1"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Database
    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_USER: str = "ollamagateuser"
    DB_PASSWORD: str = "ollamagate"
    DB_NAME: str = "ollamagate"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # LLM Settings
    OLLAMA_API_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: str = "sk-default"
    GPT_MODEL: str = "gpt-4-turbo-preview"
    OLLAMA_MODEL: str = "llama3.1"

    # Audio & Speech Settings
    AUDIO_STORAGE_PATH: str = "/tmp/audio_buffers"
    MAX_AUDIO_SIZE_MB: int = 10
    DATA_DIR: str = f"{os.getcwd()}/data"
    CACHE_DIR: str = os.path.join(DATA_DIR, "cache")
    SPEECH_CACHE_DIR: str = os.path.join(CACHE_DIR, "audio", "speech")

    # Speech-to-Text Settings
    STT_MODEL_CHOICE: str = "whisper"
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "float16"
    STT_MODEL: any = None
    USE_CUDA: bool = False

    # Text-to-Speech Settings
    TTS_ENGINE: str = "openai"
    TTS_MODEL: str = "tts-1"
    TTS_OPENAI_API_KEY: str = 'sk-111111111'
    TTS_OPENAI_API_BASE_URL: str = "http://localhost:8000/v1"

    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = 30

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_TOKENS: int = 50000

    # Session
    SESSION_EXPIRATION_TIME: int = 60 * 60 # 1 hour

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_cuda()
        self.setup_cache_dir()

    def _setup_cuda(self):
        """Setup CUDA if available and requested"""
        if self.USE_CUDA:
            try:
                import torch
                assert torch.cuda.is_available(), "CUDA not available"
                self.WHISPER_DEVICE = "cuda"
                self.WHISPER_COMPUTE_TYPE = "float16"
                logger.info("🚀 config.py: CUDA enabled successfully")
            except Exception as e:
                cuda_error = (
                    "Error when testing CUDA but USE_CUDA_DOCKER is true. "
                    f"Resetting USE_CUDA_DOCKER to false: {e}"
                )
                logger.warning(f"⚠️ config.py: {cuda_error}")
                os.environ["USE_CUDA_DOCKER"] = "false"
                self.USE_CUDA = "false"
                self.WHISPER_DEVICE = "cpu"
                self.WHISPER_COMPUTE_TYPE = "float32"
        else:
            self.WHISPER_DEVICE = "cpu"
            self.WHISPER_COMPUTE_TYPE = "float32"

    def setup_cache_dir(self):
        """Setup cache directories"""
        try:
            os.makedirs(self.SPEECH_CACHE_DIR, exist_ok=True)
            os.makedirs(self.AUDIO_STORAGE_PATH, exist_ok=True)
            logger.info("📁 config.py: Cache directories setup complete")
        except Exception as e:
            logger.error(f"❌ config.py: Error setting up cache directories: {str(e)}")
            raise e

    @property
    def is_cuda_enabled(self) -> bool:
        """Check if CUDA is enabled"""
        return self.WHISPER_DEVICE == "cuda"

    @property
    def cache_dirs(self) -> dict:
        """Get all cache directories"""
        return {
            "data": self.DATA_DIR,
            "cache": self.CACHE_DIR,
            "speech": self.SPEECH_CACHE_DIR,
            "audio": self.AUDIO_STORAGE_PATH
        }

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (CustomSource(settings_cls),)


settings = Settings()


logger.info(f"🔍 config.py: Settings: {settings.model_dump()}")