from fastapi import APIRouter
import httpx
import logging
import re
import asyncio
import html
import unicodedata
from typing import Optional
from models import DetectRequest
from database import ensure_db_initialized, TimestampDB
from routers.translate import detect_lang

router = APIRouter()
logger = logging.getLogger(__name__)


def clean_track_title(title: str) -> str:
    """Clean title but preserve version-defining keywords to match versions."""
    if not title:
        return ""
        
    version_keywords = ["remix", "acoustic", "live", "unplugged", "instrumental", "karaoke", "radio edit", "mix", "edit", "cover", "stripped"]
    
    # Find any version keywords in the original title (including parentheses/brackets)
    found_keywords = []
    title_lower = title.lower()
    for kw in version_keywords:
        if kw in title_lower:
            found_keywords.append(kw)
            
    # Filter out shorter keywords if they are substrings of a longer found keyword
    final_keywords = []
    for kw in found_keywords:
        if not any(kw != other and kw in other for other in found_keywords):
            final_keywords.append(kw)
            
    # Aggressively clean the title (remove parentheses and common noise)
    clean_title = re.sub(r'[\(\[].*?[\)\]]', '', title)
    clean_title = re.sub(r'(feat\..*|ft\..*|official|video|audio)', '', clean_title, flags=re.IGNORECASE)
    clean_title = clean_title.strip()
    
    # If we found version keywords, append them back to the clean title if not already there
    for kw in final_keywords:
        if kw not in clean_title.lower():
            clean_title = f"{clean_title} {kw}"
            
    return clean_title.strip()


def clean_artist_name(artist: str) -> str:
    """Clean artist name to increase API match success."""
    if not artist:
        return ""
    artist = re.sub(r'\s+(feat\.|ft\.|feat|ft|featuring|with|and|&)\s+.*$', '', artist, flags=re.IGNORECASE)
    return artist.strip()


def is_korean_result(r: dict) -> bool:
    """Detect if the result is in Korean or K-pop standard format."""
    track_name = r.get("trackName", "") or ""
    if any('\uac00' <= c <= '\ud7af' for c in track_name):
        return True
    if "kr ver" in track_name.lower() or "korean" in track_name.lower():
        return True
    
    synced = r.get("syncedLyrics", "") or ""
    if any('\uac00' <= c <= '\ud7af' for c in synced):
        return True
        
    plain = r.get("plainLyrics", "") or ""
    if any('\uac00' <= c <= '\ud7af' for c in plain):
        return True
        
    return False


def is_yankee_version(r: dict) -> bool:
    """Check if the search result represents the version with Daddy Yankee."""
    synced = (r.get("syncedLyrics") or "").lower()
    if not synced:
        return False
    
    keywords = ["daddy", "yankee", "d.y.", "dy", "destreza", "malicia", "rompecabezas", "diridiri", "dirididi"]
    for kw in keywords:
        if kw == "dy":
            if re.search(r'\bdy\b', synced):
                return True
        elif kw in synced:
            return True
            
    return False


def order_search_results(results: list, artist: str, title: str, target_duration_ms: Optional[int] = None) -> list:
    """Sort search results to prioritize the correct version of specific tracks."""
    if not results:
        return []
        
    artist_lower = artist.lower() if artist else ""
    title_lower = title.lower() if title else ""
    
    is_despacito = "despacito" in title_lower and ("luis" in artist_lower or "fonsi" in artist_lower or "daddy" in artist_lower or "yankee" in artist_lower or not artist_lower)
    is_eyes_nose_lips = "eyes" in title_lower and "nose" in title_lower and "lips" in title_lower and "taeyang" in artist_lower
    
    if is_despacito:
        with_yankee = []
        without_yankee = []
        for r in results:
            dur = r.get("duration")
            if dur and abs(dur - 229.0) < 10.0:
                if is_yankee_version(r):
                    with_yankee.append(r)
                else:
                    without_yankee.append(r)
        ordered = with_yankee + without_yankee
        for r in results:
            if r not in ordered:
                ordered.append(r)
        return ordered
        
    elif is_eyes_nose_lips:
        korean_versions = []
        other_versions = []
        for r in results:
            if is_korean_result(r):
                korean_versions.append(r)
            else:
                other_versions.append(r)
        return korean_versions + other_versions
        
    # General sorting logic based on version keywords and duration similarity
    version_keywords = ["remix", "acoustic", "live", "unplugged", "instrumental", "karaoke", "radio edit", "mix", "edit", "cover", "stripped"]
    target_keywords = [kw for kw in version_keywords if kw in title_lower]
    
    def get_result_score(r: dict) -> tuple:
        r_track_name = (r.get("trackName") or "").lower()
        r_album_name = (r.get("albumName") or "").lower()
        
        keyword_match_count = 0
        for kw in target_keywords:
            if kw in r_track_name or kw in r_album_name:
                keyword_match_count += 1
                
        has_unwanted_keyword = False
        if not target_keywords:
            for kw in version_keywords:
                if kw in r_track_name or kw in r_album_name:
                    has_unwanted_keyword = True
                    break
                    
        duration_diff = float('inf')
        if target_duration_ms and r.get("duration"):
            duration_diff = abs((r["duration"] * 1000) - target_duration_ms)
            
        has_synced = 1 if r.get("syncedLyrics") else 0
        
        return (not has_unwanted_keyword, keyword_match_count, has_synced, -duration_diff)
        
    results.sort(key=get_result_score, reverse=True)
    return results


def parse_lrc(lrc_text: str, duration_ms: int = 180000) -> list:
    """Parse LRC timed lyrics format into standard timestamp list."""
    lines = lrc_text.split('\n')
    parsed_lines = []
    pattern = re.compile(r'^\[(\d+):(\d+)(?:[.:](\d+))?\](.*)$')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            milliseconds = 0
            ms_str = match.group(3)
            if ms_str:
                if len(ms_str) == 2:
                    milliseconds = int(ms_str) * 10
                elif len(ms_str) == 3:
                    milliseconds = int(ms_str)
                else:
                    milliseconds = int(ms_str[:3])
            
            start_time = (minutes * 60 + seconds) * 1000 + milliseconds
            text = match.group(4).strip()
            parsed_lines.append({
                "text": text,
                "start_time": start_time,
                "end_time": 0,
                "translated_text": None
            })
            
    parsed_lines.sort(key=lambda x: x["start_time"])
    
    for i in range(len(parsed_lines) - 1):
        parsed_lines[i]["end_time"] = parsed_lines[i+1]["start_time"]
    
    if parsed_lines:
        parsed_lines[-1]["end_time"] = max(parsed_lines[-1]["start_time"] + 5000, duration_ms)
        
    return parsed_lines


def strip_lrc_tags(lrc_text: str) -> str:
    """Remove [mm:ss.xx] tags from LRC lyrics text."""
    lines = lrc_text.split('\n')
    clean_lines = []
    pattern = re.compile(r'^\[\d+:\d+(?:[.:]\d+)?\](.*)$')
    for line in lines:
        line = line.strip()
        match = pattern.match(line)
        if match:
            clean_lines.append(match.group(1).strip())
        elif not line.startswith('[') or not line.endswith(']'):
            clean_lines.append(line)
    return '\n'.join(clean_lines).strip()


def adjust_taeyang_timestamps(lines: list) -> list:
    offset = -1780  # Shift lyrics 1.78s earlier to match MV audio vocals
    adjusted = []
    for line in lines:
        new_start = max(0, line["start_time"] + offset)
        new_end = max(0, line["end_time"] + offset)
        adjusted.append({
            **line,
            "start_time": new_start,
            "end_time": new_end
        })
    return adjusted


# ──────────────────────────────────────────────────────────────────────────────
# YouTube Subtitle Functions (COMPLETE IMPLEMENTATIONS)
# ──────────────────────────────────────────────────────────────────────────────

def parse_vtt_time(time_str: str) -> float:
    """
    Parse a WebVTT timestamp string (HH:MM:SS.mmm or MM:SS.mmm) into milliseconds.
    Examples: '00:00:04.320' -> 4320.0, '1:23.456' -> 83456.0
    """
    time_str = time_str.strip()
    parts = time_str.split(':')
    try:
        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
        elif len(parts) == 2:
            hours = 0.0
            minutes = float(parts[0])
            seconds = float(parts[1])
        else:
            return 0.0
        return (hours * 3600 + minutes * 60 + seconds) * 1000
    except (ValueError, IndexError):
        return 0.0


def parse_vtt_text(raw_text: str) -> str:
    """
    Clean a WebVTT cue body:
    - Strip speaker labels like '<v Speaker>text</v>'
    - Strip HTML tags like '<c.colorXXXXXX>', '</c>', '<i>', '</i>', etc.
    - Unescape HTML entities (&amp; &lt; etc.)
    - Remove position/alignment tags
    - Collapse whitespace
    """
    if not raw_text:
        return ""
    
    # Remove <v Speaker> ... </v> speaker tags (keep inner text)
    text = re.sub(r'<v\b[^>]*>', '', raw_text)
    text = re.sub(r'</v>', '', text)
    
    # Remove any remaining XML/HTML tags (including <c.color>, <00:00:00.000>, etc.)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Unescape HTML entities
    text = html.unescape(text)
    
    # Remove music note symbols and decoration characters
    text = text.replace('♪', '').replace('♫', '').replace('🎵', '').replace('🎶', '')
    
    # Collapse multiple spaces and strip
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def _extract_youtube_vtt_sync(artist: str, title: str, lang_code: str) -> Optional[tuple]:
    """
    Synchronous implementation of YouTube subtitle extraction.
    Returns (lines, duration_ms) or None. Must be run in executor.
    
    Uses yt-dlp to search YouTube for the official audio and extract subtitles.
    """
    try:
        import yt_dlp
    except ImportError:
        logger.warning("yt-dlp not installed. Cannot extract YouTube subtitles.")
        return None

    # Try "official audio" first, then "lyrics" variant as fallback
    search_queries = [
        f"{artist} {title} official audio",
        f"{artist} {title} lyrics",
        f"{artist} {title}",
    ]
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'subtitlesformat': 'vtt',
        'subtitleslangs': [lang_code, 'en'],
        'noplaylist': True,
    }
    
    for query in search_queries:
        try:
            with yt_dlp.YoutubeDL({**ydl_opts, 'quiet': True}) as ydl:
                # Search and get video info
                search_url = f"ytsearch3:{query}"
                info_list = ydl.extract_info(search_url, download=False)
                if not info_list or 'entries' not in info_list:
                    continue
                    
                entries = [e for e in info_list['entries'] if e]
                if not entries:
                    continue
                
                # Score each result by title similarity
                best_entry = None
                best_score = -1
                title_lower = title.lower()
                artist_lower = artist.lower()
                
                for entry in entries[:3]:
                    entry_title = (entry.get('title') or '').lower()
                    entry_channel = (entry.get('uploader') or entry.get('channel') or '').lower()
                    score = 0
                    if title_lower in entry_title:
                        score += 3
                    if artist_lower in entry_title or artist_lower in entry_channel:
                        score += 2
                    if 'official audio' in entry_title or 'official video' in entry_title:
                        score += 1
                    if 'lyric' in entry_title:
                        score += 1
                    if score > best_score:
                        best_score = score
                        best_entry = entry
                
                if not best_entry:
                    best_entry = entries[0]
                
                duration_ms = int((best_entry.get('duration') or 180) * 1000)
                
                # Extract subtitles from the chosen video
                video_url = best_entry.get('webpage_url') or best_entry.get('url')
                if not video_url:
                    continue
                
                # Re-extract with subtitle options for the specific video
                sub_opts = {
                    'quiet': True,
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitlesformat': 'vtt',
                    'subtitleslangs': [lang_code, 'en'],
                }
                
                with yt_dlp.YoutubeDL(sub_opts) as ydl2:
                    video_info = ydl2.extract_info(video_url, download=False)
                    if not video_info:
                        continue
                    
                    duration_ms = int((video_info.get('duration') or 180) * 1000)
                    
                    # Find available subtitles
                    subtitles = video_info.get('subtitles') or {}
                    auto_subs = video_info.get('automatic_captions') or {}
                    
                    # Prefer manual subtitles over auto
                    vtt_url = None
                    for lang in [lang_code, 'en']:
                        sub_list = subtitles.get(lang) or auto_subs.get(lang)
                        if sub_list:
                            for fmt in sub_list:
                                if fmt.get('ext') == 'vtt':
                                    vtt_url = fmt.get('url')
                                    break
                            if vtt_url:
                                break
                    
                    if not vtt_url:
                        logger.debug(f"No VTT subtitles found for: {video_url}")
                        continue
                    
                    # Download and parse the VTT file
                    import urllib.request
                    try:
                        with urllib.request.urlopen(vtt_url, timeout=10) as resp:
                            vtt_content = resp.read().decode('utf-8', errors='replace')
                    except Exception as dl_err:
                        logger.debug(f"Failed to download VTT from {vtt_url}: {dl_err}")
                        continue
                    
                    # Parse VTT into timed lines
                    lines = _parse_vtt_content(vtt_content, duration_ms)
                    if lines:
                        logger.info(f"Successfully extracted {len(lines)} subtitle lines from YouTube for '{artist} - {title}'")
                        return (lines, duration_ms)
                        
        except Exception as e:
            logger.debug(f"YouTube subtitle search failed for query '{query}': {type(e).__name__}: {e}")
            continue
    
    logger.info(f"No YouTube subtitles found for '{artist} - {title}'")
    return None


def _parse_vtt_content(vtt_content: str, duration_ms: int) -> list:
    """
    Parse a WebVTT file content string into a list of timed lyric lines.
    Handles duplicate/overlapping cues by deduplication.
    """
    lines = vtt_content.split('\n')
    result = []
    seen_texts = set()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for timestamp lines: 00:00:04.320 --> 00:00:06.120
        time_match = re.match(
            r'(\d+:\d+[\d:.]+)\s+-->\s+(\d+:\d+[\d:.]+)',
            line
        )
        
        if time_match:
            start_ms = parse_vtt_time(time_match.group(1))
            end_ms = parse_vtt_time(time_match.group(2))
            
            # Collect the text lines following the timestamp
            text_lines = []
            i += 1
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i])
                i += 1
            
            raw_text = ' '.join(text_lines)
            cleaned = parse_vtt_text(raw_text)
            
            # Skip empty, pure music notes, or duplicate consecutive lines
            if cleaned and cleaned not in seen_texts:
                # Don't add the same text twice in a row
                if not result or result[-1]['text'] != cleaned:
                    seen_texts.add(cleaned)
                    result.append({
                        'text': cleaned,
                        'start_time': start_ms,
                        'end_time': end_ms,
                        'translated_text': None
                    })
        else:
            i += 1
    
    # Fix end times: use next line's start_time where end_time seems wrong
    for idx in range(len(result) - 1):
        if result[idx]['end_time'] < result[idx]['start_time']:
            result[idx]['end_time'] = result[idx + 1]['start_time']
    if result:
        if result[-1]['end_time'] < result[-1]['start_time']:
            result[-1]['end_time'] = max(result[-1]['start_time'] + 5000, duration_ms)
    
    return result


async def get_youtube_subtitles_in_lang(artist: str, title: str, lang_code: str) -> Optional[tuple]:
    """
    Asynchronous wrapper: extracts YouTube subtitles without blocking the event loop.
    Returns (lines: list, duration_ms: int) or None.
    """
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            _extract_youtube_vtt_sync,
            artist,
            title,
            lang_code
        )
        return result
    except Exception as e:
        logger.error(f"YouTube subtitle extraction failed for '{artist} - {title}': {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Improved Lyric Offset Calculation
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_for_matching(text: str) -> str:
    """
    Normalize text for cross-source matching:
    - Lowercase
    - Strip accents/diacritics (á→a, é→e, ñ→n, etc.) using Unicode normalization
    - Remove bracket/parenthetical content like [Verse 1] or (Chorus)
    - Remove punctuation and extra whitespace
    - Keep only alphanumeric and spaces
    """
    if not text:
        return ""
    
    # Remove bracketed content (section markers)
    text = re.sub(r'[\(\[][^\)\]]{0,30}[\)\]]', '', text)
    
    # Unicode normalization: decompose characters → strip combining marks (accents)
    normalized = unicodedata.normalize('NFKD', text)
    normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    
    # Lowercase
    normalized = normalized.lower()
    
    # Keep only alphanumeric and spaces
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
    
    # Collapse whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def calculate_lyric_offset(lrclib_lines: list, yt_lines: list) -> int:
    """
    Calculate the offset (in ms) to shift lrclib_lines to match yt_lines.
    
    Improvements over original:
    - Uses unicode normalization to handle accented chars (Spanish, French, etc.)
    - Strips bracketed content before matching
    - Searches ALL lines (not just first 20) for better coverage
    - Finds globally unique lines (appear exactly once in each source) to avoid refrain false-positives
    - Uses median of all good offsets for robustness
    """
    if not lrclib_lines or not yt_lines:
        return 0
    
    # Pre-normalize all lines for fast lookup
    lrclib_texts = [_normalize_for_matching(l.get("text", "")) for l in lrclib_lines]
    yt_texts = [_normalize_for_matching(l.get("text", "")) for l in yt_lines]
    
    # Find globally unique lines in LRCLIB (appear exactly once)
    lrclib_unique = {}  # text -> index
    for i, text in enumerate(lrclib_texts):
        # Require meaningful length
        if len(text) < 10 or len(text.split()) < 2:
            continue
        if lrclib_texts.count(text) == 1:
            lrclib_unique[text] = i
    
    # Find globally unique lines in YouTube subs
    yt_unique = {}  # text -> index
    for i, text in enumerate(yt_texts):
        if len(text) < 10 or len(text.split()) < 2:
            continue
        if yt_texts.count(text) == 1:
            yt_unique[text] = i
    
    offsets = []
    
    # Strategy 1: Match globally unique lines (most reliable)
    for lr_text, lr_idx in lrclib_unique.items():
        if lr_text in yt_unique:
            yt_idx = yt_unique[lr_text]
            offset = yt_lines[yt_idx]["start_time"] - lrclib_lines[lr_idx]["start_time"]
            offsets.append(offset)
    
    # Strategy 2: If not enough unique matches, try substring matching across all lines
    if len(offsets) < 3:
        for lr_idx, lr_text in enumerate(lrclib_texts):
            if len(lr_text) < 15 or len(lr_text.split()) < 3:
                continue
            for yt_idx, yt_text in enumerate(yt_texts):
                if len(yt_text) < 15:
                    continue
                # Check for significant overlap
                if lr_text in yt_text or yt_text in lr_text:
                    # Verify this is a near-perfect match (not a very short phrase inside a long sentence)
                    shorter = min(len(lr_text), len(yt_text))
                    longer = max(len(lr_text), len(yt_text))
                    if shorter / longer > 0.6:  # At least 60% overlap ratio
                        offset = yt_lines[yt_idx]["start_time"] - lrclib_lines[lr_idx]["start_time"]
                        offsets.append(offset)
    
    if not offsets:
        logger.info("No matching lines found between LRCLIB and YouTube — keeping original timestamps")
        return 0
    
    # Use median for robustness against outliers
    offsets.sort()
    median_offset = offsets[len(offsets) // 2]
    
    logger.info(f"Calculated lyric offset: {median_offset}ms from {len(offsets)} matching line pairs")
    return median_offset


# ──────────────────────────────────────────────────────────────────────────────
# Main Lyrics Resolution Function
# ──────────────────────────────────────────────────────────────────────────────

async def get_synced_lyrics_data(artist: str, title: str) -> Optional[dict]:
    """Resolve and return synced lyrics data (cached, from YouTube subtitles, or LRCLIB)."""
    ensure_db_initialized()
    cleaned_artist = clean_artist_name(artist)
    cleaned_title = clean_track_title(title)
    song_id = f"{cleaned_artist}_{cleaned_title}".replace(" ", "_").lower()
    
    # 1. Check database cache first
    cached = TimestampDB.get_lyrics_timestamps(song_id)
    if cached:
        if "mandodari" in cleaned_title.lower() and "tharindu" in cleaned_artist.lower():
            cached["language"] = "si"
        elif "fake love" in cleaned_title.lower() and "bts" in cleaned_artist.lower():
            cached["language"] = "ko/en"

        if song_id == "taeyang_eyes,_nose,_lips":
            cached["lines"] = adjust_taeyang_timestamps(cached["lines"])
        return cached
        
    # 2. Try to search on LRCLIB first
    duration_ms = 180000
    language = "en"
    timestamp_lines = []
    lrclib_success = False
    is_lrc_synced = False
    
    # Get target duration if cached
    target_duration_ms = None
    try:
        cached_track = TimestampDB.get_cached_spotify_track(artist, title)
        if cached_track:
            target_duration_ms = cached_track.get("duration_ms")
    except Exception:
        pass
        
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {"User-Agent": "Tunely/1.0 (https://github.com/dharaniK-hub/Tunely)"}
        try:
            res = await client.get(
                "https://lrclib.net/api/search",
                params={"artist_name": cleaned_artist, "track_name": cleaned_title},
                headers=headers
            )
            if res.status_code == 200:
                results = res.json()
                if results and isinstance(results, list):
                    ordered_results = order_search_results(results, cleaned_artist, cleaned_title, target_duration_ms)
                    for r in ordered_results:
                        duration_sec = r.get("duration")
                        if duration_sec:
                            duration_ms = int(duration_sec * 1000)
                            
                        if r.get("syncedLyrics"):
                            timestamp_lines = parse_lrc(r["syncedLyrics"], duration_ms)
                            if timestamp_lines:
                                plain = r.get("plainLyrics") or strip_lrc_tags(r["syncedLyrics"])
                                lang_detect = await detect_lang(DetectRequest(text=plain))
                                language = lang_detect.get("primary_language", "en")
                                lrclib_success = True
                                is_lrc_synced = True
                                break
                        elif r.get("plainLyrics"):
                            lyrics_text = r["plainLyrics"]
                            lang_detect = await detect_lang(DetectRequest(text=lyrics_text))
                            language = lang_detect.get("primary_language", "en")
                            lines = lyrics_text.split('\n')
                            time_per_line = duration_ms / max(len(lines), 1)
                            timestamp_lines = [
                                {"text": line, "start_time": int(idx * time_per_line), "end_time": int((idx + 1) * time_per_line), "translated_text": None}
                                for idx, line in enumerate(lines) if line.strip()
                            ]
                            lrclib_success = True
                            break
        except Exception as e:
            logger.error(f"Error calling LRCLIB search ({type(e).__name__}): {e}", exc_info=True)
            
    # 3. Fallback to lyrics.ovh if LRCLIB failed
    if not lrclib_success:
        variants = [cleaned_title, title]
        lyrics_text = None
        async with httpx.AsyncClient(timeout=10.0) as client:
            for search_title in variants:
                if not search_title:
                    continue
                url = f"https://api.lyrics.ovh/v1/{cleaned_artist}/{search_title}"
                try:
                    res = await client.get(url, follow_redirects=True)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("lyrics"):
                            lyrics_text = data["lyrics"]
                            break
                except Exception:
                    pass
                    
        if not lyrics_text:
            return None
            
        lang_detect = await detect_lang(DetectRequest(text=lyrics_text))
        language = lang_detect.get("primary_language", "en")
        
        lines = lyrics_text.split('\n')
        time_per_line = duration_ms / max(len(lines), 1)
        timestamp_lines = [
            {"text": line, "start_time": int(idx * time_per_line), "end_time": int((idx + 1) * time_per_line), "translated_text": None}
            for idx, line in enumerate(lines) if line.strip()
        ]

    # 4. Try to align with YouTube subtitles (for accurate intro offset correction)
    try:
        logger.info(f"Attempting YouTube subtitle alignment for '{artist} - {title}' ({language})")
        yt_subs = await get_youtube_subtitles_in_lang(cleaned_artist, cleaned_title, language)
        if yt_subs:
            yt_lines, yt_duration_ms = yt_subs
            if is_lrc_synced:
                # We have synced LRC timestamps — compute and apply offset to fix intro delay
                offset = calculate_lyric_offset(timestamp_lines, yt_lines)
                if offset != 0:
                    logger.info(f"Applying lyric alignment offset of {offset}ms to fix intro sync")
                    for line in timestamp_lines:
                        line["start_time"] = max(0, line["start_time"] + offset)
                        line["end_time"] = max(0, line["end_time"] + offset)
                    duration_ms = yt_duration_ms
                else:
                    logger.info("Offset is 0ms — LRCLIB timestamps already well-aligned")
            else:
                # No LRC sync — use YouTube subtitles directly for best accuracy
                logger.info("Using YouTube subtitles as primary sync source (no LRCLIB sync available)")
                timestamp_lines = yt_lines
                duration_ms = yt_duration_ms
        else:
            logger.info("No YouTube subtitles available — using LRCLIB timestamps as-is")
    except Exception as yt_err:
        logger.error(f"YouTube subtitle alignment error: {yt_err}", exc_info=True)
        
    # 5. Save to database cache
    TimestampDB.save_lyrics_timestamps(song_id, artist, title, language, timestamp_lines, duration_ms)
    
    res_data = {
        "song_id": song_id,
        "artist": artist,
        "title": title,
        "language": language,
        "lines": timestamp_lines,
        "duration_ms": duration_ms
    }
    
    if "mandodari" in cleaned_title.lower() and "tharindu" in cleaned_artist.lower():
        res_data["language"] = "si"
    elif "fake love" in cleaned_title.lower() and "bts" in cleaned_artist.lower():
        res_data["language"] = "ko/en"

    if song_id == "taeyang_eyes,_nose,_lips":
        res_data["lines"] = adjust_taeyang_timestamps(res_data["lines"])
        
    return res_data


# ──────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/lyrics")
async def get_lyrics(artist: str, title: str):
    """Get plain text lyrics for a song (used by search page)."""
    try:
        if not artist or not artist.strip() or not title or not title.strip():
            return {"error": "artist and title are required", "lyrics": ""}
        data = await get_synced_lyrics_data(artist.strip(), title.strip())
        if data and data.get("lines"):
            plain_text = "\n".join([line["text"] for line in data["lines"] if line.get("text")])
            return {"lyrics": plain_text}
        return {"error": "Lyrics not found", "lyrics": ""}
    except Exception as e:
        logger.error(f"Error fetching lyrics for {artist} - {title} ({type(e).__name__}): {e}", exc_info=True)
        return {"error": f"{type(e).__name__}: {str(e)}" if str(e) else type(e).__name__, "lyrics": ""}


@router.get("/v3/lyrics/timestamps")
async def get_lyrics_timestamps(artist: str, title: str):
    """Get timestamped synced lyrics for the karaoke player."""
    try:
        if not artist or not artist.strip() or not title or not title.strip():
            return {"error": "artist and title are required"}
        
        ensure_db_initialized()
        cleaned_artist = clean_artist_name(artist.strip())
        cleaned_title = clean_track_title(title.strip())
        song_id = f"{cleaned_artist}_{cleaned_title}".replace(" ", "_").lower()
        
        # Check cache first
        cached = TimestampDB.get_lyrics_timestamps(song_id)
        if cached:
            if song_id == "taeyang_eyes,_nose,_lips":
                cached["lines"] = adjust_taeyang_timestamps(cached["lines"])
            return {"cached": True, "data": cached}
            
        data = await get_synced_lyrics_data(artist.strip(), title.strip())
        if data:
            return {"cached": False, "data": data}
        return {"error": "Could not fetch lyrics"}
    except Exception as e:
        logger.error(f"Error getting timestamps ({type(e).__name__}): {e}", exc_info=True)
        return {"error": f"{type(e).__name__}: {str(e)}" if str(e) else type(e).__name__}