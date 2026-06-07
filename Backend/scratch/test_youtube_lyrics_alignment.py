import asyncio
import httpx
import re
import html
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_vtt_time(time_str: str) -> int:
    time_str = time_str.strip().replace(',', '.')
    parts = time_str.split(':')
    if len(parts) == 3:
        h = int(parts[0])
        m = int(parts[1])
        s_ms = parts[2].split('.')
        s = int(s_ms[0])
        ms_str = s_ms[1] if len(s_ms) > 1 else "0"
        ms = int(ms_str.ljust(3, '0')[:3])
    elif len(parts) == 2:
        h = 0
        m = int(parts[0])
        s_ms = parts[1].split('.')
        s = int(s_ms[0])
        ms_str = s_ms[1] if len(s_ms) > 1 else "0"
        ms = int(ms_str.ljust(3, '0')[:3])
    else:
        return 0
    return (h * 3600 + m * 60 + s) * 1000 + ms

def parse_vtt_text(vtt_text: str) -> list:
    blocks = re.split(r'\n\s*\n', vtt_text)
    lines_parsed = []
    
    timestamp_pattern = re.compile(r'((?:\d{2}:)?\d{2}:\d{2}[.,]\d{1,3})\s*-->\s*((?:\d{2}:)?\d{2}:\d{2}[.,]\d{1,3})')
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        
        time_match = None
        time_line_idx = -1
        for idx, line in enumerate(lines):
            match = timestamp_pattern.search(line)
            if match:
                time_match = match
                time_line_idx = idx
                break
                
        if time_match:
            start_ms = parse_vtt_time(time_match.group(1))
            end_ms = parse_vtt_time(time_match.group(2))
            
            text_lines = [l.strip() for l in lines[time_line_idx + 1:] if l.strip()]
            text = " ".join(text_lines)
            text = re.sub(r'<[^>]+>', '', text).strip()
            text = html.unescape(text)
            text = text.replace('♪', '').strip()
            
            if text and not text.startswith('NOTE') and not text.startswith('STYLE'):
                if re.match(r'^\[[^\]]+\]$', text):
                    continue
                lines_parsed.append({
                    "text": text,
                    "start_time": start_ms,
                    "end_time": end_ms,
                    "translated_text": None
                })
                
    return lines_parsed

async def get_youtube_subtitles_in_lang(artist: str, title: str, lang_code: str) -> Optional[tuple[list, int]]:
    try:
        import yt_dlp
        
        query = f"{artist} - {title}"
        search_target = f"ytsearch1:{query}"
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
        }
        
        loop = asyncio.get_event_loop()
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(search_target, download=False)
                
        info = await loop.run_in_executor(None, extract)
        
        if not info or "entries" not in info or not info["entries"]:
            return None
            
        entry = info["entries"][0]
        duration_sec = entry.get("duration")
        duration_ms = int(duration_sec * 1000) if duration_sec else 180000
        
        subtitles = entry.get('subtitles', {})
        automatic_captions = entry.get('automatic_captions', {})
        
        target_key = None
        formats = None
        
        def find_key(sub_dict):
            for k in sub_dict.keys():
                if k == lang_code or k.startswith(f"{lang_code}-"):
                    return k
            return None
            
        key = find_key(subtitles)
        if key:
            formats = subtitles[key]
        else:
            key = find_key(automatic_captions)
            if key:
                formats = automatic_captions[key]
                
        if formats:
            vtt_url = None
            for fmt in formats:
                if fmt.get('ext') == 'vtt':
                    vtt_url = fmt.get('url')
                    break
                    
            if vtt_url:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.get(vtt_url)
                    if res.status_code == 200:
                        lines = parse_vtt_text(res.text)
                        if lines:
                            return lines, duration_ms
        return None
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return None

async def main():
    print("Testing YouTube subtitles alignment for Enrique Iglesias - Bailando...")
    res = await get_youtube_subtitles_in_lang("Enrique Iglesias", "Bailando", "es")
    if res:
        lines, duration_ms = res
        print(f"SUCCESS! Fetched {len(lines)} lines. Duration: {duration_ms}ms")
        print("First 5 lines:")
        for idx, line in enumerate(lines[:5]):
            print(f"  Line {idx+1} [{line['start_time']} -> {line['end_time']}]: {line['text']}")
    else:
        print("FAILED to fetch or parse subtitles.")

if __name__ == "__main__":
    asyncio.run(main())
