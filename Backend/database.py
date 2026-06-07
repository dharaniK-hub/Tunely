"""Database module for Tunely Version 3 - timestamps and sync data"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging
import json
import hashlib
import secrets

logger = logging.getLogger(__name__)

DATABASE_PATH = "./tunely_v3.db"

class TimestampDB:
    """Handle timestamp data persistence"""
    
    @staticmethod
    def init_db():
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Users table (handles both credential and OAuth logins)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    email TEXT UNIQUE,
                    oauth_provider TEXT,
                    oauth_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # User favorites table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    artist TEXT NOT NULL,
                    title TEXT NOT NULL,
                    language TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, artist, title)
                )
            """)

            # Lyrics with timestamps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lyrics_timestamps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_id TEXT UNIQUE NOT NULL,
                    artist TEXT NOT NULL,
                    title TEXT NOT NULL,
                    language TEXT,
                    lyrics_json TEXT,
                    duration_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Spotify cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spotify_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spotify_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    artist TEXT,
                    album TEXT,
                    duration_ms INTEGER,
                    image_url TEXT,
                    preview_url TEXT,
                    audio_features_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User sync sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    song_id TEXT NOT NULL,
                    user_id TEXT,
                    current_time_ms FLOAT DEFAULT 0,
                    line_index INTEGER DEFAULT 0,
                    is_playing BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Translation cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translation_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lyrics_hash TEXT NOT NULL,
                    source_lang TEXT,
                    target_lang TEXT,
                    translation_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(lyrics_hash, source_lang, target_lang)
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False

    @staticmethod
    def get_cached_translation(text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Retrieve a cached translation if it exists"""
        try:
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT translation_json
                FROM translation_cache
                WHERE lyrics_hash = ? AND source_lang = ? AND target_lang = ?
            """, (text_hash, source_lang, target_lang))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return row[0]
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached translation: {e}")
            return None

    @staticmethod
    def save_cached_translation(text: str, source_lang: str, target_lang: str, translation: str) -> bool:
        """Save a successful translation to the cache"""
        try:
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO translation_cache 
                (lyrics_hash, source_lang, target_lang, translation_json, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (text_hash, source_lang, target_lang, translation))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving cached translation: {e}")
            return False
            
    @staticmethod
    def save_lyrics_timestamps(song_id: str, artist: str, title: str, 
                              language: str, lines: List[Dict], duration_ms: int):
        """Save lyrics with timestamps"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            lyrics_json = json.dumps(lines)
            
            cursor.execute("""
                INSERT OR REPLACE INTO lyrics_timestamps 
                (song_id, artist, title, language, lyrics_json, duration_ms, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (song_id, artist, title, language, lyrics_json, duration_ms))
            
            conn.commit()
            conn.close()
            logger.info(f"Saved timestamps for {song_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving timestamps: {e}")
            return False
    
    @staticmethod
    def get_lyrics_timestamps(song_id: str) -> Optional[Dict]:
        """Retrieve lyrics with timestamps"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT song_id, artist, title, language, lyrics_json, duration_ms, created_at
                FROM lyrics_timestamps
                WHERE song_id = ?
            """, (song_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "song_id": row[0],
                    "artist": row[1],
                    "title": row[2],
                    "language": row[3],
                    "lines": json.loads(row[4]),
                    "duration_ms": row[5],
                    "created_at": row[6]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving timestamps: {e}")
            return None
    
    @staticmethod
    def cache_spotify_track(spotify_id: str, title: str, artist: str, 
                           album: str, duration_ms: int, image_url: Optional[str],
                           preview_url: Optional[str], audio_features: Optional[Dict]):
        """Cache Spotify track information"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            features_json = json.dumps(audio_features) if audio_features else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO spotify_cache
                (spotify_id, title, artist, album, duration_ms, image_url, preview_url, audio_features_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (spotify_id, title, artist, album, duration_ms, image_url, preview_url, features_json))
            
            conn.commit()
            conn.close()
            logger.info(f"Cached Spotify track: {spotify_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching Spotify track: {e}")
            return False

    @staticmethod
    def get_cached_spotify_track(artist: str, title: str) -> Optional[Dict]:
        """Retrieve cached Spotify track by artist and title (case-insensitive)"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM spotify_cache 
                WHERE LOWER(artist) = ? AND LOWER(title) = ?
            """, (artist.lower(), title.lower()))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached Spotify track: {e}")
            return None
    
    @staticmethod
    def create_sync_session(session_id: str, song_id: str, user_id: Optional[str] = None) -> bool:
        """Create a new sync session"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO sync_sessions (session_id, song_id, user_id)
                VALUES (?, ?, ?)
            """, (session_id, song_id, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating sync session: {e}")
            return False
    
    @staticmethod
    def update_sync_position(session_id: str, current_time_ms: float, line_index: int, is_playing: bool):
        """Update current sync position"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sync_sessions
                SET current_time_ms = ?, line_index = ?, is_playing = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (current_time_ms, line_index, is_playing, session_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating sync position ({type(e).__name__}): {e}", exc_info=True)
            return False

    @staticmethod
    def hash_password(password: str, salt: str = None) -> str:
        """Hash a password using SHA-256 with a salt."""
        if not salt:
            salt = secrets.token_hex(16)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{dk.hex()}"

    @staticmethod
    def create_user(username: str, password: Optional[str] = None, email: Optional[str] = None,
                    oauth_provider: Optional[str] = None, oauth_id: Optional[str] = None) -> Optional[int]:
        """Create a new user. Returns the user ID if successful."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            password_hash = None
            if password:
                password_hash = TimestampDB.hash_password(password)

            cursor.execute("""
                INSERT INTO users (username, password_hash, email, oauth_provider, oauth_id)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password_hash, email, oauth_provider, oauth_id))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except Exception as e:
            logger.error(f"Error creating user ({type(e).__name__}): {e}", exc_info=True)
            return None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict]:
        """Fetch user by username."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting user by username ({type(e).__name__}): {e}", exc_info=True)
            return None

    @staticmethod
    def get_user_by_oauth(provider: str, oauth_id: str) -> Optional[Dict]:
        """Fetch user by OAuth details."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE oauth_provider = ? AND oauth_id = ?", (provider, oauth_id))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting user by oauth ({type(e).__name__}): {e}", exc_info=True)
            return None

    @staticmethod
    def verify_user_password(username: str, password: str) -> Optional[Dict]:
        """Verify user's password and return user info if verified."""
        user = TimestampDB.get_user_by_username(username)
        if not user or not user.get("password_hash"):
            return None
            
        stored_hash_info = user["password_hash"]
        if ":" not in stored_hash_info:
            return None
            
        salt, stored_hash = stored_hash_info.split(":", 1)
        computed_hash_info = TimestampDB.hash_password(password, salt)
        _, computed_hash = computed_hash_info.split(":", 1)
        
        if secrets.compare_digest(stored_hash, computed_hash):
            return user
        return None

    @staticmethod
    def update_password(user_id: int, new_password: str) -> bool:
        """Update a user's password."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            password_hash = TimestampDB.hash_password(new_password)
            
            cursor.execute("""
                UPDATE users
                SET password_hash = ?
                WHERE id = ?
            """, (password_hash, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating password ({type(e).__name__}): {e}", exc_info=True)
            return False

    @staticmethod
    def create_session(user_id: int, days_valid: int = 7) -> Optional[str]:
        """Create a new session token for the user."""
        try:
            token = secrets.token_hex(32)
            expires_at = (datetime.now() + timedelta(days=days_valid)).isoformat()
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_sessions (token, user_id, expires_at)
                VALUES (?, ?, ?)
            """, (token, user_id, expires_at))
            
            conn.commit()
            conn.close()
            return token
        except Exception as e:
            logger.error(f"Error creating user session ({type(e).__name__}): {e}", exc_info=True)
            return None

    @staticmethod
    def verify_session(token: str) -> Optional[Dict]:
        """Verify session token and return user details if valid."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Fetch session and user
            cursor.execute("""
                SELECT u.*, s.expires_at 
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ?
            """, (token,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                user_data = dict(row)
                expires_at_str = user_data.pop("expires_at", None)
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if datetime.now() < expires_at:
                        return user_data
                    else:
                        # Clean up expired session
                        TimestampDB.delete_session(token)
            return None
        except Exception as e:
            logger.error(f"Error verifying session ({type(e).__name__}): {e}", exc_info=True)
            return None

    @staticmethod
    def delete_session(token: str) -> bool:
        """Delete/invalidate a session token."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting session ({type(e).__name__}): {e}", exc_info=True)
            return False

    @staticmethod
    def get_user_favorites(user_id: int) -> List[Dict]:
        """Get list of favorite songs for a user."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT artist, title, language, added_at 
                FROM user_favorites 
                WHERE user_id = ?
                ORDER BY added_at DESC
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            favorites = []
            for r in rows:
                item = dict(r)
                # Generate matching frontend ID format
                artist_val = item["artist"]
                title_val = item["title"]
                item["id"] = f"{artist_val}|{title_val}".lower()
                
                # Format added_at as timestamp ms if it's a string, or fallback
                added_at = item.get("added_at")
                if isinstance(added_at, str):
                    try:
                        dt = datetime.strptime(added_at, "%Y-%m-%d %H:%M:%S")
                        item["addedAt"] = int(dt.timestamp() * 1000)
                    except ValueError:
                        item["addedAt"] = int(datetime.now().timestamp() * 1000)
                else:
                    item["addedAt"] = int(datetime.now().timestamp() * 1000)
                favorites.append(item)
                
            return favorites
        except Exception as e:
            logger.error(f"Error getting user favorites ({type(e).__name__}): {e}", exc_info=True)
            return []

    @staticmethod
    def add_user_favorite(user_id: int, artist: str, title: str, language: str) -> bool:
        """Add a song to user's favorites list."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO user_favorites (user_id, artist, title, language)
                VALUES (?, ?, ?, ?)
            """, (user_id, artist, title, language))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding user favorite ({type(e).__name__}): {e}", exc_info=True)
            return False

    @staticmethod
    def remove_user_favorite(user_id: int, artist: str, title: str) -> bool:
        """Remove a song from user's favorites list."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM user_favorites 
                WHERE user_id = ? AND artist = ? AND title = ?
            """, (user_id, artist, title))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error removing user favorite ({type(e).__name__}): {e}", exc_info=True)
            return False

# Initialize database on module import
init_db_once = False

def ensure_db_initialized():
    """Ensure database is initialized"""
    global init_db_once
    if not init_db_once:
        TimestampDB.init_db()
        init_db_once = True