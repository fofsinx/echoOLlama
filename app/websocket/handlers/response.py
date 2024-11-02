from typing import Dict, Any, List

from fastapi import WebSocket
from redis import Redis
from app.services.llm import LLMService
from app.db.database import Database
from app.websocket.base_handler import BaseHandler
from app.websocket.types import ContentPart
from app.utils.logger import logger


class ResponseHandler(BaseHandler):
    def __init__(self, websocket: WebSocket, redis: Redis, llm: LLMService, db: Database):
        super().__init__(websocket, redis, llm, db)

    def handle_response_create(self, handler):
        pass

    def handle_response_cancel(self, handler):
        pass

    async def _process_response(
            self,
            event_id: str,
            response_id: str,
            config: Dict[str, Any]
    ) -> None:
        """
        Process response with LLM integration
        📝 File: response.py, Line: 20, Function: _process_response
        """
        try:
            # Get session from database
            session = await self.db.get_session(event_id)
            if not session:
                raise ValueError("Session not found")

            # Get conversation history
            messages = await self._get_conversation_history(event_id)

            # Generate response
            async for chunk in await self.llm.generate_response(
                    messages=messages,
                    temperature=config.get("temperature", 0.8),
                    tools=config.get("tools", []),
                    stream=True
            ):
                if chunk.choices[0].delta.content:
                    # Store in database
                    await self.db.create_message(
                        session_id=event_id,
                        role="assistant",
                        content=chunk.choices[0].delta.content,
                        content_type="text",
                        metadata={"response_id": response_id}
                    )

                    # Send to websocket
                    await self._send_content_part(
                        event_id,
                        response_id,
                        ContentPart(
                            type="text",
                            text=chunk.choices[0].delta.content
                        )
                    )

                elif chunk.choices[0].delta.function_call:
                    # Handle function calls
                    await self._handle_function_call(
                        event_id,
                        response_id,
                        chunk.choices[0].delta.function_call
                    )

            # Update rate limits
            await self._update_rate_limits(event_id)

        except Exception as e:
            logger.error(f"❌ response.py: Response processing failed: {str(e)}")
            await self._handle_error(event_id, response_id, str(e))

    async def _get_conversation_history(
            self,
            session_id: str,
            limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history from database
        📝 File: response.py, Line: 82, Function: _get_conversation_history
        """
        messages = await self.db.get_session_messages(
            session_id=session_id,
            limit=limit
        )

        return [
            {
                "role": msg["role"],
                "content": msg["content"],
                **({"function_call": msg["function_call"]}
                   if msg["function_call"] else {})
            }
            for msg in messages
        ]
