from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging
from database import TimestampDB
from models import FavoriteRequest
from routers.auth import get_current_user

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])
logger = logging.getLogger(__name__)

@router.get("")
async def get_favorites(current_user: dict = Depends(get_current_user)):
    try:
        favs = TimestampDB.get_user_favorites(current_user["id"])
        return {"success": True, "favorites": favs}
    except Exception as e:
        logger.error(f"Error fetching favorites ({type(e).__name__}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading favorites"
        )

@router.post("")
async def add_favorite(req: FavoriteRequest, current_user: dict = Depends(get_current_user)):
    try:
        success = TimestampDB.add_user_favorite(
            user_id=current_user["id"],
            artist=req.artist,
            title=req.title,
            language=req.language
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save favorite"
            )
        return {"success": True, "message": "Song added to favorites"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving favorite ({type(e).__name__}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving favorite"
        )

@router.delete("")
async def remove_favorite(
    artist: str = Query(...), 
    title: str = Query(...), 
    current_user: dict = Depends(get_current_user)
):
    try:
        success = TimestampDB.remove_user_favorite(
            user_id=current_user["id"],
            artist=artist,
            title=title
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete favorite"
            )
        return {"success": True, "message": "Song removed from favorites"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite ({type(e).__name__}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting favorite"
        )
