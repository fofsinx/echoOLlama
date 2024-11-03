from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.db.database import db
from app.api.routes.v1 import endpoints, voice
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import uvicorn

from app.websocket.connection import WebSocketConnection
from app.utils.logger import logger

origins = settings.CORS_ORIGINS

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

@app.websocket_route("/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""

    # Get the requested protocols from the client
    requested_protocols = websocket.headers.get("Sec-WebSocket-Protocol", "").split(", ")
    
    logger.info(f"🔌 Requested protocols: {requested_protocols}")

    connection = WebSocketConnection(websocket, db, subprotocol=requested_protocols)
    try:
        logger.info("🔌 WebSocket client connected")
        connection.set_model(websocket.query_params["model"])
        await connection.handle_connection()
    except WebSocketDisconnect as e:
        logger.info(f"🔌 {e.code} WebSocket client disconnected: {e.reason}")
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
