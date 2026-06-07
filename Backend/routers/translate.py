from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import httpx
from langdetect import detect, detect_langs
import logging
import re
import asyncio
from datetime import datetime

from models import DetectRequest, TranslateRequest
from database import TimestampDB
from connection_manager import manager
from utils.korean_helpers import is_probably_romanized_korean, transliterate_romanized_korean
from utils.language_utils import split_mixed_language_line

router = APIRouter()
logger = logging.getLogger(__name__)

def is_probably_hinglish(text: str) -> bool:
    if not text:
        return False
    if any('\u0900' <= c <= '\u097f' for c in text):
        return False
        
    lowered = text.lower()
    tokens = set(re.findall(r"[a-z']+", lowered))
    
    hinglish_words = {
        "tum", "ho", "hai", "ko", "se", "ke", "ka", "ki", "me", "mein", "bhi", 
        "toh", "ab", "na", "nahi", "nhi", "kya", "bina", "tera", "mera", "meri", 
        "tere", "mere", "aap", "hum", "hoon", "kar", "raha", "rahi", "rahe", 
        "saath", "sath", "aur", "naam", "nam", "dil", "pyar", "pyaar", "zindagi",
        "jindagi", "juda", "sakte", "liye", "gaya", "gaye", "gayi", "kaisa", "pe",
        "rasta", "rishta", "gawara", "door", "har", "roz", "jeete",
        "tujhko", "diya", "waqt", "sabhi", "lamha", "saans"
    }
    
    matches = tokens.intersection(hinglish_words)
    total_tokens = len(tokens)
    
    if total_tokens < 5:
        return len(matches) >= 1
    elif total_tokens < 15:
        return len(matches) >= 2
    else:
        return len(matches) >= 3

async def transliterate_hinglish_to_devanagari(client: httpx.AsyncClient, text: str) -> str:
    if not text.strip():
        return text
    url = "https://inputtools.google.com/request"
    params = {
        "text": text,
        "itc": "hi-t-i0-und",
        "num": 1,
        "cp": 0,
        "cs": 1,
        "ie": "utf-8",
        "oe": "utf-8",
        "app": "demopage"
    }
    for attempt in range(3):
        try:
            res = await client.get(url, params=params, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                if data[0] == "SUCCESS":
                    words = []
                    for word_res in data[1]:
                        if word_res[1]:
                            words.append(word_res[1][0])
                    return " ".join(words)
            elif res.status_code == 429:
                await asyncio.sleep(0.5 * (attempt + 1))
        except Exception as e:
            if attempt == 2:
                logger.error(f"Transliteration error for '{text}' ({type(e).__name__}): {e}", exc_info=True)
            await asyncio.sleep(0.5 * (attempt + 1))
    return text


def is_probably_manglish(text: str) -> bool:
    if not text:
        return False
    if any('\u0d00' <= c <= '\u0d7f' for c in text):
        return False
        
    lowered = text.lower()
    tokens = set(re.findall(r"[a-z']+", lowered))
    
    manglish_words = {
        "avalude", "ninte", "enikkente", "kandappo", "chiri", "penne", "niram", "kayyil", "kaalile", 
        "arunjanam", "aranjanam", "kidakkumbo", "nokkalle", "suganthathin", "ozhukunnu", "pidakunnu", 
        "mizhi", "mizhikal", "undallo", "madiyundallo", "adivayattil", "nenjiloru", "karimizhiyulla", 
        "kalavaani", "kaarkoonthal", "sringaari", "karimashi", "chankathu", "pedakkunnu"
    }
    
    matches = tokens.intersection(manglish_words)
    total_tokens = len(tokens)
    
    if total_tokens < 5:
        return len(matches) >= 1
    elif total_tokens < 15:
        return len(matches) >= 2
    else:
        return len(matches) >= 3

async def transliterate_manglish_to_malayalam(client: httpx.AsyncClient, text: str) -> str:
    if not text.strip():
        return text
    url = "https://inputtools.google.com/request"
    params = {
        "text": text,
        "itc": "ml-t-i0-und",
        "num": 1,
        "cp": 0,
        "cs": 1,
        "ie": "utf-8",
        "oe": "utf-8",
        "app": "demopage"
    }
    for attempt in range(3):
        try:
            res = await client.get(url, params=params, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                if data[0] == "SUCCESS":
                    words = []
                    for word_res in data[1]:
                        if word_res[1]:
                            words.append(word_res[1][0])
                    return " ".join(words)
            elif res.status_code == 429:
                await asyncio.sleep(0.5 * (attempt + 1))
        except Exception as e:
            if attempt == 2:
                logger.error(f"Malayalam transliteration error for '{text}' ({type(e).__name__}): {e}", exc_info=True)
            await asyncio.sleep(0.5 * (attempt + 1))
    return text


@router.post("/detect")
async def detect_lang(req: DetectRequest):
    try:
        if not req.text.strip():
            return {"language": "auto", "languages": ["auto"], "primary_language": "auto"}
        
        if is_probably_hinglish(req.text):
            return {"language": "hi", "languages": ["hi"], "primary_language": "hi"}
        
        if is_probably_manglish(req.text):
            return {"language": "ml", "languages": ["ml"], "primary_language": "ml"}
        
        text_to_detect = req.text
        if any('\uac00' <= c <= '\ud7af' for c in req.text):
            cleaned_lines = [''.join(c for c in line if not c.isascii() or c.isspace()).strip() for line in req.text.split('\n')]
            cleaned_lines = [line for line in cleaned_lines if line]
            if cleaned_lines: text_to_detect = '\n'.join(cleaned_lines)
        
        try:
            langs = detect_langs(text_to_detect)
            detected_langs = [(str(lang).split(':')[0], float(str(lang).split(':')[1])) for lang in langs]
            significant_langs = sorted([(l, p) for l, p in detected_langs if p > 0.1], key=lambda x: x[1], reverse=True)
            
            if not significant_langs:
                return {"language": "auto", "languages": ["auto"], "primary_language": "auto"}
            
            all_languages = [lang for lang, _ in significant_langs]
            non_english = [l for l in significant_langs if l[0] != 'en']
            primary_lang = non_english[0][0] if len(significant_langs) > 1 and non_english else significant_langs[0][0]
            
            return {"language": primary_lang, "languages": all_languages, "primary_language": primary_lang}
        except Exception:
            lang = detect(text_to_detect)
            return {"language": lang, "languages": [lang], "primary_language": lang}
            
    except Exception as e:
        logger.error(f"Error detecting language ({type(e).__name__}): {e}", exc_info=True)
        error_msg = f"{type(e).__name__}: {str(e)}" if str(e) else type(e).__name__
        return {"language": "auto", "languages": ["auto"], "primary_language": "auto", "error": error_msg}

@router.post("/translate")
async def translate(req: TranslateRequest):
    try:
        if req.source == req.target or not req.text.strip():
            return {"translatedText": req.text}
        
        source_lang = req.source if req.source != "auto" else "auto"
        target_lang = req.target
        text_to_translate = req.text
        
        has_korean = any('\uac00' <= c <= '\ud7af' for c in text_to_translate)
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text_to_translate)
        
        if source_lang == "id" and has_korean: source_lang = "ko"
        elif source_lang == "id" and has_chinese: source_lang = "zh-CN"

        hinglish_mode = False
        if not has_korean and not has_chinese:
            if is_probably_hinglish(text_to_translate):
                source_lang = "hi"
                hinglish_mode = True

        manglish_mode = False
        if not has_korean and not has_chinese and not hinglish_mode:
            if is_probably_manglish(text_to_translate) or source_lang in {"ml", "id"}:
                source_lang = "ml"
                manglish_mode = True

        romanized_korean_mode = False
        if not has_korean and not hinglish_mode and not manglish_mode and source_lang in {"auto", "id"}:
            if is_probably_romanized_korean(text_to_translate):
                source_lang = "ko"
                romanized_korean_mode = True


        if has_korean and source_lang == "ko":
            cleaned_lines = []
            for line in text_to_translate.split('\n'):
                if any('\uac00' <= c <= '\ud7af' for c in line) and any(c.isascii() and c.isalpha() for c in line):
                    processed_words = [
                        w for w in line.split() if 
                        any('\uac00' <= c <= '\ud7af' for c in w) or 
                        (any(c.isascii() and c.isalpha() for c in w) and all(c.isascii() or c in "-\'" for c in w)) or 
                        (w and w[0].isdigit()) or 
                        w in ',.!?:;"-()[]{}…※♪★↓'
                    ]
                    cleaned = re.sub(r'\s+', ' ', ' '.join(processed_words)).strip()
                    if cleaned: cleaned_lines.append(cleaned)
                elif any('\uac00' <= c <= '\ud7af' for c in line):
                    cleaned = re.sub(r'\s+', ' ', ''.join(c for c in line if '\uac00' <= c <= '\ud7af' or '\u1100' <= c <= '\u11ff' or c in ' \t\n.,!?:;"\'-()[]{}…※♪★↓' or c.isdigit())).strip()
                    if cleaned: cleaned_lines.append(cleaned)
                elif line.strip():
                    cleaned_lines.append(line)
            text_to_translate = '\n'.join(cleaned_lines)

        async def _do_translate(client: httpx.AsyncClient, segment: str, effective_source: str) -> str:
            if effective_source == "ko" or req.source == "ko":
                try:
                    google_res = await client.get("https://translate.googleapis.com/translate_a/single", params={"client": "gtx", "sl": effective_source if effective_source != "auto" else "ko", "tl": target_lang, "dt": "t", "q": segment}, timeout=8.0)
                    if google_res.status_code == 200:
                        translated = "".join([chunk[0] for chunk in google_res.json()[0] or [] if chunk and chunk[0]]).strip()
                        if translated and translated.lower() != segment.lower(): return translated
                except Exception: pass
                
                try:
                    res = await client.post("https://api.libretranslate.de/translate", json={"q": segment, "source": "ko", "target": target_lang, "format": "text"}, timeout=8.0, follow_redirects=True)
                    if res.status_code == 200:
                        translated = res.json().get("translatedText", segment)
                        if translated.strip() and translated.lower() != segment.lower(): return translated
                except Exception: pass
            
            try:
                google_res = await client.get("https://translate.googleapis.com/translate_a/single", params={"client": "gtx", "sl": effective_source, "tl": target_lang, "dt": "t", "q": segment}, timeout=8.0)
                if google_res.status_code == 200:
                    translated = "".join([chunk[0] for chunk in google_res.json()[0] or [] if chunk and chunk[0]]).strip()
                    if translated: return translated
            except Exception: pass
            return segment

        async def translate_segment(client: httpx.AsyncClient, segment: str, segment_source: str) -> str:
            if not segment.strip(): return segment
            effective_source = segment_source if segment_source != "auto" else "auto"
            cached = TimestampDB.get_cached_translation(segment, effective_source, target_lang)
            if cached: return cached
            
            final_translation = await _do_translate(client, segment, effective_source)
            if final_translation != segment:
                TimestampDB.save_cached_translation(segment, effective_source, target_lang, final_translation)
            return final_translation

        # === DEDUPLICATION & CONCURRENCY OPTIMIZATION ===
        
        lines = text_to_translate.split('\n')
        
        # 1. DEDUPLICATE: Find only the unique lines
        unique_lines = {}
        for line in lines:
            if not line.strip():
                continue
            cache_key = line.strip().lower()
            if cache_key not in unique_lines:
                unique_lines[cache_key] = line

        # 2. CONCURRENCY: Process up to 5 unique lines at the same time
        sem = asyncio.Semaphore(5) 
        
        async def process_single_line(client: httpx.AsyncClient, line: str, cache_key: str):
            async with sem:
                
                line_source = source_lang
                if line_source == "auto" and not romanized_korean_mode and not hinglish_mode:
                    if any('\uac00' <= c <= '\ud7af' for c in line):
                        line_source = "ko"
                    elif any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in line):
                        line_source = "ja"
                    elif any('\u4e00' <= c <= '\u9fff' for c in line):
                        line_source = "zh"
                    else:
                        try:
                            line_source = detect(line)
                            if line_source == "ko" and not is_probably_romanized_korean(line):
                                line_source = "auto"
                        except Exception: line_source = "auto"

                if line_source == target_lang:
                    return cache_key, line

                is_line_korean = is_probably_romanized_korean(line) if (romanized_korean_mode or source_lang == "ko") else False
                line_text = transliterate_romanized_korean(line) if is_line_korean else line
                line_source = "ko" if is_line_korean else line_source

                if hinglish_mode:
                    line_text = await transliterate_hinglish_to_devanagari(client, line)
                    line_source = "hi"

                if manglish_mode:
                    line_text = await transliterate_manglish_to_malayalam(client, line)
                    line_source = "ml"

                candidates = [line_source]
                if romanized_korean_mode and "auto" not in candidates: candidates.append("auto")
                elif line_source != "auto": candidates.append("auto")


                translated_line = line
                for candidate in candidates:
                    if candidate == target_lang: continue
                    translated_line = await translate_segment(client, line_text, candidate)
                    if translated_line.strip().lower() != line_text.strip().lower(): break

                return cache_key, translated_line

        # Execute all unique translations concurrently
        async with httpx.AsyncClient(timeout=20.0, limits=httpx.Limits(max_connections=10)) as client:
            tasks = [process_single_line(client, line, key) for key, line in unique_lines.items()]
            results = await asyncio.gather(*tasks)
            
        # Map results back to a dictionary
        line_translation_cache = {key: trans for key, trans in results}

        # 3. RECONSTRUCT: Build the final lyrics using the cached translations
        translated_lines = []
        for line in lines:
            if not line.strip():
                translated_lines.append(line)
            else:
                cache_key = line.strip().lower()
                translated_lines.append(line_translation_cache[cache_key])

        return {"translatedText": '\n'.join(translated_lines)}
        
    except Exception as e:
        logger.error(f"Unexpected translation error ({type(e).__name__}): {e}", exc_info=True)
        error_msg = f"{type(e).__name__}: {str(e)}" if str(e) else type(e).__name__
        return {"translatedText": req.text, "error": f"Translation failed: {error_msg}"}

@router.websocket("/ws/translate")
async def websocket_translate(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if not data.get("text") or not data.get("target"):
                await websocket.send_json({"error": "Missing text or target language"})
                continue
            
            source = data.get("source", "auto")
            target = data.get("target")
            
            try:
                translated = await translate(TranslateRequest(text=data.get("text"), source=source, target=target))
                await websocket.send_json({"status": "success", "translated": translated.get("translatedText", data.get("text")), "source": source, "target": target, "timestamp": datetime.now().isoformat()})
            except Exception as e:
                await websocket.send_json({"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)