from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app import db
from app.api.routes.v1 import endpoints, voice
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import uvicorn

from app.websocket.connection import WebSocketConnection
from app.utils.logger import logger

origins = [
    "http://localhost:3001",
    "http://localhost:3000",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup/shutdown events"""
    try:
        await db.connect()
        logger.info("📁 File: main.py, Line: 10, Function: lifespan; Status: Application started")
        yield
    finally:
        await db.disconnect()
        logger.info("📁 File: main.py, Line: 14, Function: lifespan; Status: Application shutdown")

app = FastAPI(
    title=settings.APP_NAME,
    description="A FastAPI wrapper for the Ollama API that matches the official API structure",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    debug=settings.LOG_LEVEL == "debug",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api")
app.include_router(voice.router, prefix="/api/voice")

@app.websocket("/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    connection = WebSocketConnection(websocket)
    try:
        await connection.handle_connection()
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket client disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {str(e)}")
    finally:
        await connection.cleanup()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)