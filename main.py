"""SIVA FastAPI server main entry point."""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from config.settings import settings
from core.data_manager import DataManager
from core.llm_judge import LLMJudge
from core.vector_store import VectorStore
from api import routes
from api.embedding_viz import router as embedding_router
from api.websockets import websocket_tts, websocket_stt

# Create FastAPI app
app = FastAPI(
    title="SIVA API",
    description="Self-Learning Voice Agent for Healthcare Intake",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Initialize global components
openai_client = OpenAI(api_key=settings.openai_api_key)
vector_store = VectorStore(
    data_dir=settings.data_dir,
    similarity_threshold=settings.similarity_threshold,
    openai_api_key=settings.openai_api_key,
)
llm_judge = LLMJudge(openai_api_key=settings.openai_api_key)
data_manager = DataManager(data_dir=settings.data_dir)

# Set global components in routes module
routes.vector_store = vector_store
routes.llm_judge = llm_judge
routes.data_manager = data_manager
routes.openai_client = openai_client
routes.current_mode = settings.current_mode

# Include API routes
app.include_router(routes.router)
app.include_router(embedding_router, prefix="/api")


# WebSocket endpoints
@app.websocket("/ws/tts")
async def tts_endpoint(websocket: WebSocket):
    """Text-to-Speech WebSocket endpoint."""
    await websocket_tts(websocket)


@app.websocket("/ws/stt")
async def stt_endpoint(websocket: WebSocket):
    """Speech-to-Text WebSocket endpoint."""
    await websocket_stt(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
    )
