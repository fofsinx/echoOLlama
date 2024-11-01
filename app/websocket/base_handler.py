from datetime import datetime
from typing import Dict, Any
from fastapi import WebSocket
from redis import Redis
from app.utils.logger import logger

class BaseHandler:
    """Base class for all handlers"""
    
    def __init__(self, websocket: WebSocket, redis: Redis):
        self.websocket = websocket
        self.redis = redis

    async def send_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send WebSocket event with logging"""
        try:
            await self.websocket.send_json({
                "type": event_type,
                "data": data,
                "timestamp": datetime.now(datetime.UTC).isoformat()
            })
            logger.info(f"📤 base_handler.py: Sent event {event_type}")
        except Exception as e:
            logger.error(f"❌ base_handler.py: Failed to send event {event_type}: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass