from typing import Dict, Any
from fastapi import HTTPException
from datetime import datetime
import json
from app.websocket.types import MessageType
from app.websocket.base_handler import BaseHandler
from app.utils.logger import logger


class ConversationHandler(BaseHandler):
    """Handles conversation-related events"""

    async def handle_conversation_create(self, message: Dict[str, Any]) -> None:
        """
        Handle conversation item creation
        📝 File: conversation.py, Line: 15, Function: handle_conversation_create
        """
        try:
            item = message.get("item", {})
            event_id = message.get("event_id", "default")

            # Validate conversation item
            self._validate_conversation_item(item)

            # Add metadata
            item_with_metadata = self._add_item_metadata(item, event_id)

            # Store conversation item
            await self._store_conversation_item(item_with_metadata, event_id)

            await self.send_event(MessageType.CONVERSATION_CREATE.value, {
                "event_id": event_id,
                "item": item_with_metadata
            })

            logger.info(f"💬 conversation.py: Item created for conversation {event_id}")

        except Exception as e:
            logger.error(f"❌ conversation.py: Item creation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def handle_conversation_truncate(self, message: Dict[str, Any]) -> None:
        """
        Handle conversation truncation
        📝 File: conversation.py, Line: 42, Function: handle_conversation_truncate
        """
        try:
            event_id = message.get("event_id", "default")
            before_id = message.get("before_id")

            if not before_id:
                raise ValueError("before_id is required for truncation")

            conv_key = f"conversation:{event_id}"
            items = await self.redis.lrange(conv_key, 0, -1)

            # Find index of before_id
            truncate_index = None
            for i, item in enumerate(items):
                item_data = json.loads(item)
                if item_data.get("id") == before_id:
                    truncate_index = i
                    break

            if truncate_index is None:
                raise ValueError(f"Item with id {before_id} not found")

            # Remove items after truncate_index
            await self.redis.ltrim(conv_key, 0, truncate_index - 1)

            await self.send_event(MessageType.CONVERSATION_TRUNCATE.value, {
                "event_id": event_id,
                "before_id": before_id
            })

            logger.info(f"✂️ conversation.py: Conversation {event_id} truncated before {before_id}")

        except Exception as e:
            logger.error(f"❌ conversation.py: Truncation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    def _validate_conversation_item(self, item: Dict[str, Any]) -> None:
        """Validate conversation item structure"""
        required_fields = ["type", "role", "content"]
        if not all(k in item for k in required_fields):
            raise ValueError(f"Missing required fields: {required_fields}")

        valid_roles = ["user", "assistant", "system"]
        if item["role"] not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")

    def _add_item_metadata(self, item: Dict[str, Any], event_id: str) -> Dict[str, Any]:
        """Add metadata to conversation item"""
        return {
            **item,
            "id": f"msg_{datetime.now().timestamp()}",
            "created_at": datetime.now().isoformat(),
            "event_id": event_id
        }

    async def _store_conversation_item(self, item: Dict[str, Any], event_id: str) -> None:
        """Store conversation item in Redis"""
        conv_key = f"conversation:{event_id}"
        await self.redis.rpush(conv_key, json.dumps(item))
        await self.redis.expire(conv_key, 86400)  # 24 hour TTL

    def set_model(self, model):
        self.llm.set_default_model(model)
