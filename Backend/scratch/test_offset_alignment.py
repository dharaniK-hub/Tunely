import re
import json

def calculate_lyric_offset(lrclib_lines: list, yt_lines: list) -> int:
    """Calculate the offset (in ms) to shift lrclib_lines to match yt_lines using text matching."""
    if not lrclib_lines or not yt_lines:
        return 0
        
    offsets = []
    
    def clean_text(t):
        return re.sub(r'[^a-zA-Z0-9\s]', '', t.lower()).strip()
        
    for lr_line in lrclib_lines[:20]:
        lr_text = lr_line.get("text") or ""
        lr_clean = clean_text(lr_text)
        if len(lr_clean) < 12 or len(lr_clean.split()) < 3:
            continue
            
        # Search for a matching line in YouTube subtitles
        for yt_line in yt_lines:
            yt_text = yt_line.get("text") or ""
            yt_clean = clean_text(yt_text)
            if len(yt_clean) < 12 or len(yt_clean.split()) < 3:
                continue
            # Check if one is a substring of another
            if lr_clean in yt_clean or yt_clean in lr_clean:
                offset = yt_line["start_time"] - lr_line["start_time"]
                offsets.append(offset)
                # Print with safe encoding
                safe_lr = lr_line['text'].encode('ascii', errors='replace').decode()
                safe_yt = yt_line['text'].encode('ascii', errors='replace').decode()
                print(f"Matched: '{safe_lr}' with '{safe_yt}' -> Offset: {offset}ms")
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
