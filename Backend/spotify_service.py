"""Spotify API integration service for Tunely Version 3"""

import httpx
import logging
import base64
from typing import Optional, Dict
from datetime import datetime, timedelta
from database import TimestampDB

logger = logging.getLogger(__name__)

def _extract_youtube_audio_sync(query_or_url: str) -> Optional[str]:
    """Synchronous yt-dlp extraction (must be run in executor)."""
    try:
        import yt_dlp
        search_target = query_or_url
        if not query_or_url.startswith("http"):
            search_target = f"ytsearch1:{query_or_url}"
        ydl_opts = {
            'format': 'm4a/bestaudio',
            'quiet': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_target, download=False)
            if "entries" in info:
                entries = info.get("entries", [])
                if entries:
                    return entries[0].get("url")
            else:
                return info.get("url")
        return None
    except Exception as e:
        logger.error(f"Error extracting YouTube stream URL for {query_or_url}: {e}")
        return None

def get_youtube_audio_url(query_or_url: str) -> Optional[str]:
    """Extract direct audio stream URL from a YouTube video URL or search query."""
    return _extract_youtube_audio_sync(query_or_url)

def get_youtube_track_info(query: str, target_duration_ms: Optional[int] = None) -> Optional[dict]:
    """Search YouTube and return direct audio URL, thumbnail, and duration, prioritizing matching duration."""
    try:
        import yt_dlp
        
        # Search for up to 5 videos to find the best duration match
        search_target = f"ytsearch5:{query} official audio"
        ydl_opts = {
            'format': 'm4a/bestaudio',
            'quiet': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_target, download=False)
            if "entries" in info and info.get("entries"):
                entries = info["entries"]
                
                # Find best entry
                best_entry = entries[0]
                if target_duration_ms and len(entries) > 1:
                    min_diff = float('inf')
                    for entry in entries:
                        entry_duration_sec = entry.get("duration")
                        if entry_duration_sec:
                            entry_duration_ms = entry_duration_sec * 1000
                            diff = abs(entry_duration_ms - target_duration_ms)
                            # Give a slight bonus if the title has "audio" or "lyrics" or "lyric video"
                            # to avoid music videos with long intros/outros
                            entry_title = (entry.get("title") or "").lower()
                            if "official audio" in entry_title or "lyric" in entry_title or "audio" in entry_title:
                                diff -= 5000 # 5s bonus
                            if diff < min_diff:
                                min_diff = diff
                                best_entry = entry
                                
                return {
                    "url": best_entry.get("url"),
                    "thumbnail": best_entry.get("thumbnail"),
                    "duration_ms": int(best_entry.get("duration", 0) * 1000) if best_entry.get("duration") else 240000
                }
            elif info:
                return {
                    "url": info.get("url"),
                    "thumbnail": info.get("thumbnail"),
                    "duration_ms": int(info.get("duration", 0) * 1000) if info.get("duration") else 240000
                }
        return None
    except Exception as e:
        logger.error(f"Error extracting YouTube track info for {query} ({type(e).__name__}): {e}", exc_info=True)
        return None


class SpotifyService:
    """Handles all Spotify API interactions"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.spotify.com/v1"
        self.auth_url = "https://accounts.spotify.com/api/token"
        self.access_token = None
        self.token_expiry = None
    
    async def get_access_token(self) -> str:
        """Get Spotify API access token using Client Credentials flow"""
        try:
            # Check if token is still valid
            if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
                return self.access_token
            
            # Prepare auth header
            auth_str = f"{self.client_id}:{self.client_secret}"
            auth_b64 = base64.b64encode(auth_str.encode()).decode()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    self.auth_url,
                    headers={"Authorization": f"Basic {auth_b64}"},
                    data={"grant_type": "client_credentials"}
                )
            
            if res.status_code == 200:
                data = res.json()
                self.access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                logger.info("Spotify token refreshed successfully")
                return self.access_token
            else:
                logger.error(f"Failed to get Spotify token: {res.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Spotify token ({type(e).__name__}): {e}", exc_info=True)
            return None
    
    async def search_track(self, artist: str, title: str) -> Optional[Dict]:
        """Search for a track on Spotify"""
        try:
            # Check for Despacito override
            artist_lower = artist.lower() if artist else ""
            title_lower = title.lower() if title else ""
            if "despacito" in title_lower and ("luis" in artist_lower or "fonsi" in artist_lower or "daddy" in artist_lower or "yankee" in artist_lower or not artist_lower):
                logger.info("Despacito Luis Fonsi override triggered")
                stream_url = get_youtube_audio_url("https://www.youtube.com/watch?v=kJQP7kiw5Fk") or "https://archive.org/download/mastermix-usb-reggae-reggaeton/08%20-%20Luis%20Fonsi%20Feat.%20Daddy%20Yankee%20-%20Despacito%2089.mp3"
                return {
                    "id": "despacito_luis_fonsi",
                    "name": "Despacito",
                    "artist": "Luis Fonsi ft. Daddy Yankee",
                    "album": "Vida",
                    "duration_ms": 229000,
                    "image_url": "https://archive.org/download/mastermix-usb-reggae-reggaeton/08%20-%20Luis%20Fonsi%20Feat.%20Daddy%20Yankee%20-%20Despacito%2089.png",
                    "preview_url": stream_url,
                    "spotify_uri": "spotify:track:6habF01Z4hc6j70F13Q74a"
                }

            if "eyes" in title_lower and "nose" in title_lower and "lips" in title_lower and "taeyang" in artist_lower:
                logger.info("Eyes, Nose, Lips Taeyang override triggered")
                stream_url = get_youtube_audio_url("https://www.youtube.com/watch?v=UwuAPyOImoI") or "http://localhost:8000/static/eyes_nose_lips.m4a"
                return {
                    "id": "eyes_nose_lips_taeyang",
                    "name": "Eyes, Nose, Lips",
                    "artist": "TAEYANG",
                    "album": "RISE",
                    "duration_ms": 230000,
                    "image_url": "https://i.scdn.co/image/ab67616d0000b273b0a7b45c26b38dc7639f706d",
                    "preview_url": stream_url,
                    "spotify_uri": "spotify:track:0Xy146Ew3qB0gPzP60T2Xp"
                }

            if "kalyani" in title_lower and ("arjn" in artist_lower or "kds" in artist_lower):
                logger.info("Kalyani ARJN KDS override triggered")
                stream_url = get_youtube_audio_url("https://www.youtube.com/watch?v=CqDByohxbtA")
                return {
                    "id": "arjn_kds_kalyani",
                    "name": "Kalyani",
                    "artist": "ARJN, KDS",
                    "album": "Kalyani",
                    "duration_ms": 234501,
                    "image_url": "https://img.youtube.com/vi/CqDByohxbtA/hqdefault.jpg",
                    "preview_url": stream_url,
                    "spotify_uri": "spotify:track:arjn_kds_kalyani"
                }

            if "tum" in title_lower and "hi" in title_lower and "ho" in title_lower:
                logger.info("Tum Hi Ho override triggered")
                stream_url = get_youtube_audio_url("Arijit Singh Tum Hi Ho")
                return {
                    "id": "tum_hi_ho_arijit_singh",
                    "name": "Tum Hi Ho",
                    "artist": "Arijit Singh",
                    "album": "Aashiqui 2",
                    "duration_ms": 262000,
                    "image_url": "https://i.scdn.co/image/ab67616d0000b2732959828c460d37e41680d927",
                    "preview_url": stream_url,
                    "spotify_uri": "spotify:track:565983759"
                }

            if "sanasennam" in title_lower and ("senaka" in artist_lower or not artist_lower):
                logger.info("Sanasennam Ma Senaka Batagoda override triggered")
                stream_url = get_youtube_audio_url("https://www.youtube.com/watch?v=gyBo3APBuDU")
                return {
                    "id": "senaka_batagoda_sanasennam_ma",
                    "name": "Sanasennam Ma",
                    "artist": "Senaka Batagoda",
                    "album": "Sanasennam Ma",
                    "duration_ms": 289000,
                    "image_url": "https://i.ytimg.com/vi/gyBo3APBuDU/hqdefault.jpg",
                    "preview_url": stream_url,
                    "spotify_uri": "spotify:track:senaka_batagoda_sanasennam_ma"
                }

            # 1. Check local cache first
            try:
                cached_track = TimestampDB.get_cached_spotify_track(artist, title)
                if cached_track:
                    logger.info(f"Found cached Spotify track details for {artist} - {title}")
                    yt_info = get_youtube_track_info(f"{cached_track['artist']} - {cached_track['title']}", cached_track["duration_ms"])
                    stream_url = yt_info["url"] if yt_info else None
                    return {
                        "id": cached_track["spotify_id"] + "_yt" if stream_url else cached_track["spotify_id"],
                        "name": cached_track["title"],
                        "artist": cached_track["artist"],
                        "album": cached_track["album"],
                        "duration_ms": cached_track["duration_ms"],
                        "image_url": cached_track["image_url"],
                        "preview_url": stream_url or cached_track["preview_url"],
                        "spotify_uri": f"spotify:track:{cached_track['spotify_id']}"
                    }
            except Exception as cache_err:
                logger.error(f"Error checking cache: {cache_err}")

            # 2. Query Spotify API
            token = await self.get_access_token()
            tracks = []
            if token:
                query = f"artist:{artist} track:{title}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.get(
                        f"{self.base_url}/search",
                        headers={"Authorization": f"Bearer {token}"},
                        params={"q": query, "type": "track", "limit": 1}
                    )
                if res.status_code == 200:
                    tracks = res.json().get("tracks", {}).get("items", [])

            if tracks:
                track = tracks[0]
                logger.info(f"Found Spotify track: {track.get('name')}")
                spotify_id = track.get("id")
                track_name = track.get("name")
                artist_name = track["artists"][0].get("name") if track.get("artists") else artist
                album_name = track.get("album", {}).get("name")
                duration_ms = track.get("duration_ms")
                image_url = track.get("album", {}).get("images", [{}])[0].get("url")
                spotify_preview = track.get("preview_url")

                # Cache in DB
                try:
                    TimestampDB.cache_spotify_track(
                        spotify_id=spotify_id,
                        title=track_name,
                        artist=artist_name,
                        album=album_name,
                        duration_ms=duration_ms,
                        image_url=image_url,
                        preview_url=spotify_preview,
                        audio_features=None
                    )
                except Exception as cache_save_err:
                    logger.error(f"Failed to save to cache: {cache_save_err}")

                # Resolve YouTube audio stream URL
                yt_info = get_youtube_track_info(f"{artist_name} - {track_name}", duration_ms)
                stream_url = yt_info["url"] if yt_info else None

                return {
                    "id": spotify_id + "_yt" if stream_url else spotify_id,
                    "name": track_name,
                    "artist": artist_name,
                    "album": album_name,
                    "duration_ms": duration_ms,
                    "image_url": image_url,
                    "preview_url": stream_url or spotify_preview,
                    "spotify_uri": track.get("uri")
                }
            
            # 3. Fallback to YouTube-only search if Spotify fails
            logger.warning(f"No Spotify track found for {artist} - {title}. Falling back to YouTube search.")
            yt_info = get_youtube_track_info(f"{artist} - {title}")
            if yt_info and yt_info.get("url"):
                return {
                    "id": f"yt_{int(datetime.now().timestamp())}",
                    "name": title,
                    "artist": artist,
                    "album": "YouTube Audio",
                    "duration_ms": yt_info.get("duration_ms", 240000),
                    "image_url": yt_info.get("thumbnail") or "https://img.youtube.com/vi/default/hqdefault.jpg",
                    "preview_url": yt_info["url"],
                    "spotify_uri": "spotify:track:fallback"
                }

            return None
            
        except Exception as e:
            logger.error(f"Error searching Spotify ({type(e).__name__}): {e}", exc_info=True)
            return None
    
    async def get_track_audio_features(self, track_id: str) -> Optional[Dict]:
        """Get audio features for a track (tempo, energy, etc.)"""
        try:
            token = await self.get_access_token()
            if not token:
                return None
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{self.base_url}/audio-features/{track_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
            
            if res.status_code == 200:
                return res.json()
            else:
                logger.warning(f"Could not get audio features for {track_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting audio features ({type(e).__name__}): {e}", exc_info=True)
            return None

# Global Spotify service instance (configure with env variables)
spotify_service = None

def init_spotify_service(client_id: str, client_secret: str):
    """Initialize the global Spotify service"""
    global spotify_service
    spotify_service = SpotifyService(client_id, client_secret)
    logger.info("Spotify service initialized")

def get_spotify_service() -> Optional[SpotifyService]:
    """Get the global Spotify service instance"""
    return spotify_service
