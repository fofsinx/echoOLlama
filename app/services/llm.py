from typing import List, Dict, Any, Optional, AsyncGenerator, Union
import json
import openai
from enum import Enum
from fastapi import HTTPException
from app.config import settings
from app.schemas.requests import ChatRequest
from app.schemas import ChatResponse
from app.utils.logger import logger

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
        # Initialize OpenAI client
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE_URL,
            timeout=settings.LLM_TIMEOUT,
            max_retries=settings.LLM_MAX_RETRIES
        )
        
        # Initialize Ollama client using OpenAI SDK
        self.ollama_client = openai.AsyncOpenAI(
            api_key="ollama",  # Dummy API key for Ollama
            base_url=settings.OLLAMA_API_BASE_URL,
            timeout=settings.LLM_TIMEOUT,
            max_retries=settings.LLM_MAX_RETRIES
        )
        
        logger.info("🤖 llm.py: LLM service initialized with unified OpenAI SDK")

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.8,
        tools: Optional[List[Dict]] = None,
        stream: bool = True,
        provider: ModelProvider = ModelProvider.OPENAI
    ) -> Union[AsyncGenerator[Any, None], Any]:
        """
        Generate response using specified provider
        📝 File: llm.py, Line: 54, Function: generate_response
        """
        try:
            client = self.ollama_client if provider == ModelProvider.OLLAMA else self.openai_client
            model = settings.OLLAMA_MODEL if provider == ModelProvider.OLLAMA else settings.GPT_MODEL
            
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
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
    ) -> AsyncGenerator[ChatResponse, None]:
        """
        Stream chat responses using OpenAI SDK
        📝 File: llm.py, Line: 82, Function: chat_stream
        """
        try:
            client = self.ollama_client if provider == ModelProvider.OLLAMA else self.openai_client
            
            stream = await client.chat.completions.create(
                model=request.model,
                messages=[m.model_dump() for m in request.messages],
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield ChatResponse(
                        model=request.model,
                        message={
                            "role": "assistant",
                            "content": chunk.choices[0].delta.content
                        },
                        done=chunk.choices[0].finish_reason is not None
                    )
                    
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