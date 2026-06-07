from fastapi import APIRouter
import logging
from spotify_service import get_spotify_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/search")
async def spotify_search_track(artist: str, title: str):
    """Search for a track on Spotify"""
    try:
        spotify = get_spotify_service()
        if not spotify:
            return {"error": "Spotify service not initialized", "track": None}
        
        track = await spotify.search_track(artist, title)
        if track:
            return {"success": True, "track": track}
        else:
            return {"success": False, "error": "Track not found"}
    except Exception as e:
        logger.error(f"Spotify search error ({type(e).__name__}): {e}", exc_info=True)
        error_msg = f"{type(e).__name__}: {str(e)}" if str(e) else type(e).__name__
        return {"error": error_msg, "track": None}