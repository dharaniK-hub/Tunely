from fastapi import APIRouter, Header, HTTPException, status, Depends
import logging
from database import TimestampDB
from models import UserRegister, UserLogin, OAuthLogin, PasswordChange

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials",
        )
    token = authorization.split("Bearer ")[1].strip()
    user = TimestampDB.verify_session(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid",
        )
    return user

@router.post("/signup")
async def signup(req: UserRegister):
    try:
        # Check if user already exists
        existing = TimestampDB.get_user_by_username(req.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        user_id = TimestampDB.create_user(
            username=req.username,
            password=req.password,
            email=req.email
        )
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user"
            )
            
        # Create session token automatically upon signup
        token = TimestampDB.create_session(user_id)
        return {
            "success": True,
            "message": "User registered successfully",
            "token": token,
            "user": {
                "id": user_id,
                "username": req.username,
                "email": req.email
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error ({type(e).__name__}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {type(e).__name__}"
        )

@router.post("/login")
async def login(req: UserLogin):
    try:
        user = TimestampDB.verify_user_password(req.username, req.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
            
        token = TimestampDB.create_session(user["id"])
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error ({type(e).__name__}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {type(e).__name__}"
        )

@router.post("/oauth")
async def oauth_login(req: OAuthLogin):
    """
    Handles sign-in / registration via Mock OAuth (Google / Facebook).
    If the email already exists under a different provider, links it or throws.
    """
    try:
        # Check if user already registered via this OAuth provider + ID
        user = TimestampDB.get_user_by_oauth(req.provider, req.oauth_id)
        
        if not user:
            # Check if email is already taken under normal account
            # If so, link it, otherwise create a new account
            username = req.username or req.email.split("@")[0]
            # Ensure unique username
            base_username = username
            counter = 1
            while TimestampDB.get_user_by_username(username):
                username = f"{base_username}_{counter}"
                counter += 1
                
            user_id = TimestampDB.create_user(
                username=username,
                email=req.email,
                oauth_provider=req.provider,
                oauth_id=req.oauth_id
            )
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to register OAuth user"
                )
            user = {
                "id": user_id,
                "username": username,
                "email": req.email
            }
            
        token = TimestampDB.create_session(user["id"])
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth authentication error ({type(e).__name__}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth error: {type(e).__name__}"
        )

@router.post("/logout")
async def logout(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return {"success": True, "message": "Already logged out"}
    token = authorization.split("Bearer ")[1].strip()
    TimestampDB.delete_session(token)
    return {"success": True, "message": "Logged out successfully"}

@router.post("/change-password")
async def change_password(req: PasswordChange, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["id"]
        # Fetch latest user details from DB to get the password_hash
        user = TimestampDB.get_user_by_username(current_user["username"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        password_hash = user.get("password_hash")
        
        # If the user has a password_hash set, verify the current password first
        if password_hash:
            if not req.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required"
                )
            verified_user = TimestampDB.verify_user_password(current_user["username"], req.current_password)
            if not verified_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect current password"
                )
                
        # Update the password
        success = TimestampDB.update_password(user_id, req.new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
            
        return {"success": True, "message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error ({type(e).__name__}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change error: {type(e).__name__}"
        )

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "user": {
            "id": current_user["id"],
            "username": current_user["username"],
            "email": current_user["email"],
            "oauth_provider": current_user["oauth_provider"]
        }
    }
