from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

# Load .env file if present (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on actual env vars

from database import ensure_db_initialized
from spotify_service import init_spotify_service

# Import all routers
from routers import lyrics, translate, spotify, sync, auth, favorites

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize SQLite Database tables
    ensure_db_initialized()
    
    # 2. Initialize Spotify Service from environment variables
    spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    if not spotify_client_id or not spotify_client_secret:
        logging.warning(
            "SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not set. "
            "Track metadata will fall back to YouTube-only search."
        )
    init_spotify_service(spotify_client_id, spotify_client_secret)
    yield

app = FastAPI(
    lifespan=lifespan, 
    title="Tunely API",
    description="Lyrics translation, sync, and karaoke backend",
    version="1.0.0"
)

# Mount static files for local audio playback
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# CORS — read allowed origins from environment variable
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(lyrics.router, tags=["Lyrics"])
app.include_router(translate.router, tags=["Translation"])
app.include_router(spotify.router, prefix="/v3/spotify", tags=["Spotify"])
app.include_router(sync.router, prefix="/v3/sync", tags=["Sync"])
app.include_router(auth.router, tags=["Authentication"])
app.include_router(favorites.router, tags=["Favorites"])  # was missing!

@app.get("/health")
async def health():
    """Health check endpoint — verifies DB connectivity."""
    try:
        from database import TimestampDB
        # Simple DB connectivity test
        TimestampDB.get_user_by_username("__health_check__")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "db": db_status,
        "version": "1.0.0"
    }