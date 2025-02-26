from typing import List, Dict, Any, Optional, AsyncGenerator, Union
import json

import ollama
import openai
from enum import Enum
from fastapi import HTTPException
from app.config import settings
from app.schemas.requests import (ChatRequest, ChatResponse)
from app.utils.logger import logger
from typing import Generator


class ModelProvider(Enum):
    """
    Enum for model providers
    📝 File: llm.py, Line: 15, Function: ModelProvider
    """
    OLLAMA = "ollama"
    OPENAI = "openai"


class LLMService:
    """
    Unified service for handling both Ollama and OpenAI models using OpenAI SDK
    """

    def __init__(self):
        """
        Initialize LLM service with OpenAI clients for both providers
        📝 File: llm.py, Line: 26, Function: __init__
        """
        # Initialize Ollama client using OpenAI SDK
        self.ollama_client = ollama.AsyncClient(
            host=settings.OLLAMA_API_BASE_URL
        )
        self.model = settings.OLLAMA_MODEL

        logger.info("🤖 llm.py: LLM service initialized with unified OpenAI SDK")

    async def generate_response(
            self,
            messages: List[Dict[str, Any]],
            temperature: float = 0.8,
            tools: Optional[List[Dict]] = None,
            stream: bool = True,
            provider: ModelProvider = ModelProvider.OPENAI,
            model: Optional[str] = None
    ) -> Union[AsyncGenerator[Any, None], Any]:
        """
        Generate response using specified provider
        📝 File: llm.py, Line: 54, Function: generate_response
        """
        try:
            client = self.ollama_client if provider == ModelProvider.OLLAMA else None
            if client is None:
                raise ValueError("Invalid provider")
            model = model if model is not None else self.model if provider == ModelProvider.OLLAMA else None

            if model is None:
                raise ValueError("Model not specified")

            response = await client.generate(
                model=model,
                prompt=messages,
                tools=tools,
                stream=stream
            )

            logger.info(f"🤖 llm.py: Generated response with {len(messages)} messages using {provider.value}")
            return response

        except Exception as e:
            logger.error(f"❌ llm.py: LLM response generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def chat_stream(
            self,
            request: ChatRequest,
            provider: ModelProvider = ModelProvider.OPENAI
    ) -> Generator[str, None, None]:
        """
        Stream chat responses using OpenAI SDK
        📝 File: llm.py, Line: 82, Function: chat_stream
        """
        try:
            client = self.ollama_client if provider == ModelProvider.OLLAMA else None

            if client is None:
                raise ValueError("Invalid provider")

            streaming_allowed: bool = request.stream

            request_dict = {
                "model": request.model,
                "tools": request.tools,
                "messages": [m.model_dump() for m in request.messages]
            }
            if streaming_allowed:
                stream = await client.chat(
                    **request_dict,
                    stream=True
                )

                async for chunk in stream:
                    if chunk['message']['content']:
                        yield chunk['message']['content']
            else:
                response = await client.chat(
                    **request_dict,
                    stream=False
                )
                yield response['message']['content']

        except Exception as e:
            logger.error(f"❌ llm.py: Chat stream failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def process_function_call(
            self,
            function_call: Dict[str, Any],
            available_functions: Dict[str, callable]
    ) -> Any:
        """
        Process function calls from LLM
        📝 File: llm.py, Line: 116, Function: process_function_call
        """
        try:
            function_name = function_call["name"]
            function_args = json.loads(function_call["arguments"])

            if function_name not in available_functions:
                raise ValueError(f"Unknown function: {function_name}")

            function_to_call = available_functions[function_name]
            function_response = await function_to_call(**function_args)

            logger.info(f"🔧 llm.py: Executed function {function_name}")
            return function_response

        except Exception as e:
            logger.error(f"❌ llm.py: Function call processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def set_default_model(self, model: str) -> None:
        """
        Set default model for Ollama
        📝 File: llm.py, Line: 137, Function: set_default_model
        """
        self.model = model
        logger.info(f"🤖 llm.py: Default model set to {model}")