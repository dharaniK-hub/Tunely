import re
from typing import List, Tuple

def split_mixed_language_line(line: str) -> List[Tuple[str, str]]:
    """
    Split a mixed-language line into segments with their detected language.
    Returns list of (segment_text, detected_language) tuples.
    """
    if not line.strip():
        return []
    
    # Pattern to capture different scripts including whitespace
    pattern = r'[\uac00-\ud7af\u1100-\u11ff]+|[\u4e00-\u9fff]+|[\u3040-\u309f\u30a0-\u30ff]+|[a-zA-Z0-9]+|\s+|[^\s\uac00-\ud7af\u1100-\u11ff\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\w]+'
    
    raw_segments = []
    for match in re.finditer(pattern, line):
        text = match.group(0)
        
        # Detect language based on script
        if any('\uac00' <= c <= '\ud7af' for c in text):
            lang = "ko"  # Korean
        elif any('\u4e00' <= c <= '\u9fff' for c in text):
            lang = "zh"  # Chinese
        elif any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in text):
            lang = "ja"  # Japanese
        elif any(c.isalpha() for c in text):
            lang = "en"  # English/Latin
        else:
            lang = "other"  # Numbers, punctuation, etc.
        
        raw_segments.append([text, lang])
        
    # Pass 1: Merge consecutive segments of the same language
    merged = []
    for text, lang in raw_segments:
        if merged and merged[-1][1] == lang:
            merged[-1][0] += text
        else:
            merged.append([text, lang])
            
    # Pass 2: Merge 'other' segments that are sandwiched between the same language
    changed = True
    while changed:
        changed = False
        i = 0
        new_merged = []
        while i < len(merged):
            if i + 2 < len(merged) and merged[i][1] == merged[i+2][1] and merged[i+1][1] == 'other' and merged[i][1] != 'other':
                new_merged.append([merged[i][0] + merged[i+1][0] + merged[i+2][0], merged[i][1]])
                i += 3
                changed = True
            else:
                new_merged.append(merged[i])
                i += 1
        merged = new_merged
        
    return [(s[0], s[1]) for s in merged]