import asyncio
import hashlib
import json
import os
import tempfile
from datetime import datetime
from typing import Optional, Tuple, Generator

import openai
from faster_whisper import WhisperModel

from app.config import settings
from app.core.voice import get_stt_model
from app.utils.errors import AudioProcessingError
from app.utils.logger import logger


class AudioService:
    """Service for handling audio processing, STT and TTS operations"""

    def __init__(self):
        """
        Initialize audio service with models and cache
        📝 File: audio.py, Line: 22, Function: __init__
        """
        self.stt_model: Optional[WhisperModel] = None
        self.temp_dir = os.path.join(tempfile.gettempdir(), "audio_processing")
        self.openai_client = openai.OpenAI(
            api_key=settings.TTS_OPENAI_API_KEY,
            base_url=settings.TTS_OPENAI_API_BASE_URL,
        ) if settings.TTS_ENGINE == "openai" else None
        os.makedirs(self.temp_dir, exist_ok=True)

        logger.info("🎙️ audio.py: AudioService initialized")

    async def initialize_stt(self) -> None:
        """
        Initialize STT model with proper configuration
        📝 File: audio.py, Line: 37, Function: initialize_stt
        """

        if not self.stt_model:
            try:
                self.stt_model = get_stt_model()
                logger.info("✅ audio.py: STT model initialized")
            except Exception as e:
                logger.error(f"❌ audio.py: STT model initialization failed: {str(e)}")
                raise AudioProcessingError("Failed to initialize STT model")

    async def transcribe_audio(
            self,
            audio_data: bytes,
            event_id: str,
            language: str = 'en',
            task: str = 'transcribe',
            beam_size: int = 5,
            vad_filter: bool = True
    ) -> Generator[str, None, None]:  # type: ignore
        """
        Transcribe audio with streaming support
        📝 File: audio.py, Line: 60, Function: transcribe_audio
        """
        try:
            await self.initialize_stt()
            temp_path = self._save_audio_buffer(audio_data, event_id)

            segments, info = await asyncio.to_thread(
                self.stt_model.transcribe,
                temp_path,
                language=language,
                task=task,
                beam_size=beam_size,
                vad_filter=vad_filter,
                initial_prompt=None,
            )

            logger.info(
                f"ℹ️ audio.py: Detected language: {info.language} "
                f"with probability {info.language_probability:.2f}"
            )

            for segment in segments:
                yield segment.text
                logger.info(f"🎯 audio.py: Transcribed segment: {segment.text[:30]}...")

        except Exception as e:
            logger.error(f"❌ audio.py: Transcription failed: {str(e)}")
            yield json.dumps({"error": str(e)})
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def generate_speech(
            self,
            text: str,
            voice: str = 'alloy',
            model: str = 'tts-1',
            response_format: str = 'mp3'
    ) -> Tuple[str, str]:
        """
        Generate speech using OpenAI's TTS API with caching
        📝 File: audio.py, Line: 98, Function: generate_speech
        """
        try:
            # Create cache key
            body = {
                "model": model,
                "input": text,
                "voice": voice,
                "response_format": response_format
            }
            cache_key = hashlib.sha256(json.dumps(body).encode()).hexdigest()

            # Setup cache paths
            settings.setup_cache_dir()
            file_path = os.path.join(settings.SPEECH_CACHE_DIR, f"{cache_key}.mp3")
            file_body_path = os.path.join(settings.SPEECH_CACHE_DIR, f"{cache_key}.json")

            # Return cached file if exists
            if os.path.isfile(file_path):
                return file_path, cache_key

            # Generate new audio
            if settings.TTS_ENGINE == "openai":
                with self.openai_client.audio.speech.with_streaming_response.create(
                        model=settings.TTS_MODEL,
                        voice=voice,
                        input=text
                ) as response:
                    with open(file_path, "wb") as f:
                        for chunk in response.iter_bytes():
                            f.write(chunk)

                    # Save request body for cache
                    with open(file_body_path, "w") as f:
                        json.dump(body, f)

                    return file_path, cache_key
            else:
                raise AudioProcessingError("Unsupported TTS engine")

        except Exception as e:
            logger.error(f"❌ audio.py: Speech generation failed: {str(e)}")
            raise AudioProcessingError(f"Failed to generate speech: {str(e)}")

    def _save_audio_buffer(self, audio_bytes: bytes, event_id: str) -> str:
        """
        Save audio buffer to temporary file
        📝 File: audio.py, Line: 146, Function: _save_audio_buffer
        """
        try:
            temp_path = os.path.join(
                self.temp_dir,
                f"{event_id}_{datetime.now().timestamp()}.wav"
            )

            with open(temp_path, "wb") as f:
                f.write(audio_bytes)

            return temp_path

        except Exception as e:
            logger.error(f"❌ audio.py: Failed to save audio buffer: {str(e)}")
            raise AudioProcessingError("Failed to save audio data")

    async def commit_audio_buffer(self, audio_data: bytes, event_id: str) -> None:
        pass

    async def cleanup(self) -> None:
        """
        Cleanup resources and temporary files
        📝 File: audio.py, Line: 167, Function: cleanup
        """
        try:
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    os.remove(os.path.join(self.temp_dir, file))
                os.rmdir(self.temp_dir)

            self.stt_model = None
            logger.info("🧹 audio.py: Audio service cleanup completed")

        except Exception as e:
            logger.error(f"❌ audio.py: Cleanup failed: {str(e)}")
