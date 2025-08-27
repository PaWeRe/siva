"""SIVA FastAPI server main entry point."""

import sys
from pathlib import Path

# Add src directory to Python path for absolute imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# Import new settings module
from siva.settings import settings, get_siva_config

# Import old settings for backward compatibility
try:
    from config.settings import settings as old_settings

    USE_OLD_SETTINGS = True
except ImportError:
    USE_OLD_SETTINGS = False
    old_settings = None

from core.data_manager import DataManager
from core.llm_judge import LLMJudge
from core.vector_store import VectorStore
from api import routes
from api.embedding_viz import router as embedding_router
from api.websockets import websocket_tts, websocket_stt

# Import the bridge for tau2-bench integration
from siva.bridge import initialize_bridge

# Import new API service
from siva.api_service.main_router import main_router as new_api_router

# Create FastAPI app
app = FastAPI(
    title="SIVA API",
    description="Self-Learning Voice Agent for Healthcare Intake",
    version="2.0.0",
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

# Initialize the SIVA bridge for tau2-bench integration
siva_bridge = initialize_bridge(
    vector_store=vector_store,
    llm_judge=llm_judge,
    data_manager=data_manager,
    openai_client=openai_client,
    current_mode=settings.current_mode,
)

# Set global components in routes module (keeping existing functionality)
routes.vector_store = vector_store
routes.llm_judge = llm_judge
routes.data_manager = data_manager
routes.openai_client = openai_client
routes.current_mode = settings.current_mode

# Also set the bridge for future use
routes.siva_bridge = siva_bridge

# Include legacy API routes (maintaining backward compatibility)
app.include_router(routes.router)
app.include_router(embedding_router, prefix="/api")

# Include new API routes (tau2-bench compatible)
app.include_router(new_api_router, prefix="/api")


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
