import yt_dlp
import httpx
import json
import re

def parse_time(time_str):
    time_str = time_str.strip().replace(',', '.')
    parts = time_str.split(':')
    if len(parts) == 3:
        h = int(parts[0])
        m = int(parts[1])
        s_ms = parts[2].split('.')
        s = int(s_ms[0])
        ms_str = s_ms[1] if len(s_ms) > 1 else "0"
        # Pad to 3 digits
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

def parse_vtt(vtt_text):
    # Split into blocks by blank lines
    blocks = re.split(r'\n\s*\n', vtt_text)
    lines_parsed = []
    
    timestamp_pattern = re.compile(r'((?:\d{2}:)?\d{2}:\d{2}[.,]\d{1,3})\s*-->\s*((?:\d{2}:)?\d{2}:\d{2}[.,]\d{1,3})')
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        
        # Look for timestamp line
        time_match = None
        time_line_idx = -1
        for idx, line in enumerate(lines):
            match = timestamp_pattern.search(line)
            if match:
                time_match = match
                time_line_idx = idx
                break
                
        if time_match:
            start_ms = parse_time(time_match.group(1))
            end_ms = parse_time(time_match.group(2))
            
            # Subtitle text is everything after the timestamp line
            text_lines = [l.strip() for l in lines[time_line_idx + 1:] if l.strip()]
            # Join text lines, remove VTT tags like <c> or </c>
            text = " ".join(text_lines)
            text = re.sub(r'<[^>]+>', '', text).strip()
            
            # Avoid metadata-only or empty subtitles
            if text and not text.startswith('NOTE') and not text.startswith('STYLE'):
                lines_parsed.append({
                    "text": text,
                    "start_time": start_ms,
                    "end_time": end_ms,
                    "translated_text": None
                })
                
    return lines_parsed

def run():
    query = "ytsearch1:Enrique Iglesias Bailando"
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info and info["entries"]:
            entry = info["entries"][0]
            subtitles = entry.get('subtitles', {})
            
            es_key = None
            for key in subtitles.keys():
                if key.startswith('es'):
                    es_key = key
                    break
            
            if es_key:
                print(f"Parsing subtitles for key: {es_key}")
                formats = subtitles[es_key]
                vtt_url = None
                for fmt in formats:
                    if fmt.get('ext') == 'vtt':
                        vtt_url = fmt.get('url')
                        break
                
                if vtt_url:
                    res = httpx.get(vtt_url)
                    if res.status_code == 200:
                        parsed = parse_vtt(res.text)
                        # Write to json file
                        out_path = r"C:\Users\Asus\OneDrive\Documents\Tunely\Backend\scratch\enrique_parsed.json"
                        with open(out_path, 'w', encoding='utf-8') as f:
                            json.dump(parsed, f, indent=2, ensure_ascii=False)
                        print(f"SUCCESS: Parsed {len(parsed)} subtitle lines.")
                        print("Sample of parsed lines:")
                        for item in parsed[:5]:
                            print(f"  [{item['start_time']} -> {item['end_time']}]: {item['text']}")
                    else:
                        print("Failed to fetch VTT")
                else:
                    print("No VTT format")
            else:
                print("No Spanish subtitles key")

if __name__ == "__main__":
    run()
