import json
from app.config import Settings
from fastapi import APIRouter, HTTPException
from faster_whisper import WhisperModel
from typing import Generator
import asyncio
import os
from app.utils.logger import logger

router = APIRouter()

config = Settings()


def get_stt_model():
    if config.STT_MODEL_CHOICE == "whisper":
        try:
            stt_model = WhisperModel(
                model_size_or_path=config.WHISPER_MODEL_SIZE,
                device=config.WHISPER_DEVICE,
                compute_type=config.WHISPER_COMPUTE_TYPE,
                cpu_threads=4,
                num_workers=2
            )
            return stt_model
        except Exception as e:
            logger.error(f"❌ voice.py: Failed to initialize Whisper model: {str(e)}")
            raise
    else:
        raise HTTPException(status_code=500, detail="STT_MODEL_CHOICE not supported")


async def generate_transcription(temp_path: str, language: str, task: str, beam_size: int, vad_filter: bool) -> \
        Generator[str, None, None]:  # type: ignore
    try:
        stt_model = get_stt_model()
        if stt_model is None:
            raise HTTPException(status_code=500, detail="STT_MODEL not initialized")

        # Use faster-whisper's streaming API
        segments, info = await asyncio.to_thread(
            stt_model.transcribe,
            temp_path,
            language=language,
            task=task,
            beam_size=beam_size,
            vad_filter=vad_filter,
            initial_prompt=None
        )

        logger.info(f"ℹ️ voice.py: Detected language: {info.language} with probability {info.language_probability:.2f}")

        # Stream each segment as it's transcribed
        for segment in segments:
            yield f"{segment.text}\n"
            logger.info(f"🎯 voice.py: Transcribed segment: {segment.text[:30]}...")
    except Exception as e:
        logger.error(f"❌ voice.py: Error in transcription generation: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.info(f"🧹 voice.py: Cleaned up temporary file {temp_path}")
