import re
import json
import unicodedata

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Remove text inside parentheses or brackets
    text = re.sub(r'[\(\[].*?[\)\]]', '', text)
    # Normalize unicode to decompose accents (e.g. 'ó' -> 'o' + accent)
    nfkd_form = unicodedata.normalize('NFKD', text)
    # Encode to ASCII, ignoring decomposed accent marks, then decode back
    ascii_text = nfkd_form.encode('ascii', 'ignore').decode('utf-8')
    # Keep only letters, numbers, and spaces
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', ascii_text.lower())
    # Normalize whitespace
    return " ".join(cleaned.split())

def calculate_lyric_offset(lrclib_lines: list, yt_lines: list) -> int:
    """Calculate the offset (in ms) to shift lrclib_lines to match yt_lines using globally unique text matching."""
    if not lrclib_lines or not yt_lines:
        return 0
        
    # Step 1: Clean and count frequencies in LRCLIB lines
    lr_cleaned = []
    lr_counts = {}
    for line in lrclib_lines:
        text = line.get("text") or ""
        cleaned = clean_text(text)
        lr_cleaned.append(cleaned)
        if cleaned:
            lr_counts[cleaned] = lr_counts.get(cleaned, 0) + 1
            
    # Step 2: Clean and count frequencies in YouTube lines
    yt_cleaned = []
    yt_counts = {}
    for line in yt_lines:
        text = line.get("text") or ""
        cleaned = clean_text(text)
        yt_cleaned.append(cleaned)
        if cleaned:
            yt_counts[cleaned] = yt_counts.get(cleaned, 0) + 1
            
    # Step 3: Match globally unique lines
    offsets = []
    for idx_lr, lr_line in enumerate(lrclib_lines):
        lr_clean = lr_cleaned[idx_lr]
        if not lr_clean or lr_counts.get(lr_clean, 0) != 1:
            continue
            
        # Only match reasonably long lines to avoid short noise matches
        if len(lr_clean) < 10 or len(lr_clean.split()) < 3:
            continue
            
        # Check if this unique LRCLIB line matches a unique YouTube line
        for idx_yt, yt_line in enumerate(yt_lines):
            yt_clean = yt_cleaned[idx_yt]
            if not yt_clean or yt_counts.get(yt_clean, 0) != 1:
                continue
                
            # If one is a substring of the other or they match exactly
            if lr_clean == yt_clean or lr_clean in yt_clean or yt_clean in lr_clean:
                offset = yt_line["start_time"] - lr_line["start_time"]
                offsets.append(offset)
                safe_lr = lr_line['text'].encode('ascii', errors='replace').decode()
                safe_yt = yt_line['text'].encode('ascii', errors='replace').decode()
                print(f"Matched unique line: '{safe_lr}' <-> '{safe_yt}' -> Offset: {offset}ms")
                break
                
    if not offsets:
        print("No unique lines matched. Falling back to simple linear search...")
        # Fallback to simple matching on non-unique lines (e.g. first 30 lines) as backup
        offsets = []
        for lr_line in lrclib_lines[:30]:
            lr_clean = clean_text(lr_line.get("text") or "")
            if len(lr_clean) < 12 or len(lr_clean.split()) < 3:
                continue
            for yt_line in yt_lines[:50]:
                yt_clean = clean_text(yt_line.get("text") or "")
                if len(yt_clean) < 12 or len(yt_clean.split()) < 3:
                    continue
                if lr_clean in yt_clean or yt_clean in lr_clean:
                    offset = yt_line["start_time"] - lr_line["start_time"]
                    offsets.append(offset)
                    break
                    
    if not offsets:
        return 0
        
    offsets.sort()
    median_offset = offsets[len(offsets) // 2]
    return median_offset

def run_test():
    with open(r"C:\Users\Asus\OneDrive\Documents\Tunely\Backend\scratch\enrique_parsed.json", 'r', encoding='utf-8') as f:
        yt_lines = json.load(f)
        
    lrclib_lines = [
        {"text": "Yo te miro y se me corta la respiración", "start_time": 12240},
        {"text": "Cuando tú me miras se me sube el corazón", "start_time": 17450},
        {"text": "Me palpita lento el corazón", "start_time": 20120},
        {"text": "Y en un silencio tu mirada dice mil palabras", "start_time": 22840},
        {"text": "La noche en la que te suplico que no salga el sol", "start_time": 27950},
        {"text": "Bailando, bailando", "start_time": 32100},
        {"text": "Bailando, bailando", "start_time": 35300},
    ]
    
    print("Calculating offset...")
    offset = calculate_lyric_offset(lrclib_lines, yt_lines)
    print(f"\nFinal calculated offset: {offset}ms ({offset/1000:.2f}s)")
    
    # Verify shifting
    shifted_first = lrclib_lines[0]["start_time"] + offset
    expected_first = 42834 # from enrique_parsed.json
    diff = abs(shifted_first - expected_first)
    if diff < 1000:
        print(f"PASS: Shifted first line start time to {shifted_first}ms, expected ~{expected_first}ms (diff: {diff}ms)")
    else:
        print(f"FAIL: Shifted to {shifted_first}ms, expected {expected_first}ms")

if __name__ == "__main__":
    run_test()
