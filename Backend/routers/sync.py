from fastapi import APIRouter, Depends, HTTPException, status
import logging
from models import SyncUpdate
from database import ensure_db_initialized, TimestampDB
from routers.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/position")
async def update_sync_position(update: SyncUpdate, current_user: dict = Depends(get_current_user)):
    """Update the user's current playback position for a song."""
    try:
        ensure_db_initialized()
        user_id = str(current_user["id"])
        # Use a user-specific session_id so users don't overwrite each other
        session_id = f"{user_id}_{update.song_id}"
        TimestampDB.update_sync_position(
            session_id=session_id,
            song_id=update.song_id,
            user_id=user_id,
            current_time_ms=update.current_time_ms,
            line_index=update.line_index
        )
        return {"success": True}
    except Exception as e:
        logger.error(f"Sync position update error ({type(e).__name__}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sync position: {type(e).__name__}"
        )