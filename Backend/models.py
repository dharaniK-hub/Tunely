from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
import re

class DetectRequest(BaseModel):
    text: str
    
    @field_validator('text')
    @classmethod
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('text must not be empty')
        if len(v) > 50000:
            raise ValueError('text too long (max 50,000 characters)')
        return v

class TranslateRequest(BaseModel):
    text: str
    source: str = "auto"
    target: str = "en"
    
    @field_validator('text')
    @classmethod
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('text must not be empty')
        if len(v) > 50000:
            raise ValueError('text too long (max 50,000 characters)')
        return v

class TimestampLine(BaseModel):
    """Represents a single line with timing info"""
    text: str
    start_time: float  # milliseconds
    end_time: float
    translated_text: Optional[str] = None

class LyricsWithTimestamps(BaseModel):
    """Complete lyrics with sync timestamps"""
    song_id: str
    artist: str
    title: str
    language: str
    lines: List[TimestampLine]
    duration: float  # total song duration in ms
    created_at: Optional[datetime] = None

class SpotifyTrackInfo(BaseModel):
    """Spotify track metadata"""
    spotify_id: str
    title: str
    artist: str
    album: str
    duration_ms: int
    image_url: Optional[str] = None
    preview_url: Optional[str] = None

class RealTimeTranslationRequest(BaseModel):
    """Request for real-time translation streaming"""
    artist: str
    title: str
    source_language: str
    target_language: str = "en"

class SyncUpdate(BaseModel):
    """Update for lyric sync position"""
    song_id: str
    current_time_ms: float
    line_index: int
    
    @field_validator('current_time_ms')
    @classmethod
    def validate_time(cls, v):
        if v < 0:
            raise ValueError('current_time_ms cannot be negative')
        if v > 86400000:  # 24 hours in ms
            raise ValueError('current_time_ms out of range')
        return v

class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 30:
            raise ValueError('Username must be at most 30 characters')
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('Username may only contain letters, numbers, underscores, dots, and hyphens')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password is too long (max 128 characters)')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class OAuthLogin(BaseModel):
    provider: str
    email: str
    oauth_id: str
    username: Optional[str] = None

class FavoriteRequest(BaseModel):
    artist: str
    title: str
    language: str
    
    @field_validator('artist', 'title')
    @classmethod
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('must not be empty')
        if len(v) > 200:
            raise ValueError('too long (max 200 characters)')
        return v.strip()

class PasswordChange(BaseModel):
    current_password: Optional[str] = None
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('New password is too long')
        return v