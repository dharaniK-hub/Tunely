import re

_KOREAN_ONSETS = {
    "kk": 1, "tt": 4, "pp": 8, "ss": 10, "jj": 13,
    "ch": 14, "ng": 11, "g": 0, "k": 0, "n": 2, "d": 3, "t": 16,
    "r": 5, "l": 5, "m": 6, "b": 7, "p": 17, "s": 9, "j": 12, "h": 18,
}

_KOREAN_VOWELS = {
    "yae": 3, "yeo": 6, "wae": 10, "oe": 11, "wo": 14, "we": 15, "wi": 16,
    "ya": 2, "ye": 7, "yo": 12, "yu": 17, "ae": 1, "eo": 4, "eu": 18,
    "ui": 19, "wa": 9, "a": 0, "e": 5, "o": 8, "u": 13, "i": 20,
}

_KOREAN_FINALS = {
    "": 0, "g": 1, "kk": 2, "ks": 3, "n": 4, "nj": 5, "nh": 6, "d": 7,
    "r": 8, "l": 8, "lg": 9, "lm": 10, "lb": 11, "ls": 12, "lt": 13,
    "lp": 14, "lh": 15, "m": 16, "b": 17, "bs": 18, "s": 19, "ss": 20,
    "ng": 21, "j": 22, "ch": 23, "k": 1, "t": 25, "p": 26, "h": 27,
    "ps": 18,
}

_ROMANIZED_KOREAN_WORDS = {
    "neujeun": "늦은", "bam": "밤", "biga": "비가", "naeryeowa": "내려와",
    "neol": "널", "deryeowa": "데려와", "neo": "너", "eobshi": "없이",
    "eobsi": "없이", "jal": "잘", "sal": "살", "su": "수", "itdago": "있다고",
    "jeojeun": "젖은", "gieok": "기억", "kkeute": "끝에", "dwicheogyeo": "뒤척여",
    "na": "나", "mothaneun": "못하는", "surdo": "술도", "suldo": "술도",
    "mashigo": "마시고", "sogtaneun": "속타는", "mam": "맘", "bamsae": "밤새",
    "chaewo": "채워", "bwado": "봐도", "shirdeo": "싫어", "eobneun": "없는",
    "haruneun": "하루는", "gideo": "기도", "bideo": "비도", "yeot": "엿",
    "gatae": "같애", "yeogi": "여기", "gajyeo": "가져", "mianhae": "미안해",
    "molla": "몰라", "modeunge": "모든 게", "geotbakke": "것밖에",
    "andweneun": "안되는", "naraseo": "나라서", "hwatgime": "홧김에",
    "moreuge": "모르게", "tteonabonaetjiman": "떠나보냈지만", "jime": "짐에",
    "jebar": "제발", "ijge": "잊게", "haedar": "해달", "geojitmariya": "거짓말이야",
    "narkaroun": "나를", "mal": "mal", "iya": "이야", "molrasseo": "몰랐어",
    "ijeya": "이제야", "arasseo": "알았어", "piryohae": "필요해", "moreu": "모르",
    "ge": "게", "modeun": "모든", "kkeutnatde": "끝났대", "boge": "보게",
    "bor": "볼", "suga": "수가", "eobde": "없대", "gu": "그", "amudo": "아무도",
    "honja": "혼자", "useum": "웃음", "boiji": "보이지", "anha": "않아",
    "nunmurjogcha": "눈물조차", "goiji": "고이지", "deoneun": "더는",
    "sargo": "살고", "sipji": "싶지", "oh": "오", "bye": "bye",
    # Added Fake Love words
    "nan": "난", "wihaeseoramyeon": "위해서라면", "seulpeodo": "슬퍼도",
    "gippeun": "기쁜", "cheok": "척", "hal": "할", "apado": "아파도",
    "ganghan": "강한", "sarangi": "사랑이", "sarangmaneuro": "사랑만으로",
    "wanbyeokhagil": "완벽하길", "nae": "내", "yakjeomdeureun": "약점들은",
    "da": "다", "sumgyeojigil": "숨겨지길", "ilwojiji": "이뤄지지",
    "anhneun": "않는", "kkumsogeseo": "꿈속에서", "piul": "피울",
    "eopsneun": "없는", "kkocheul": "꽃을", "kiwosseo": "키웠어",
    "sesangeul": "세상을", "jwossne": "줬네", "jeonbu": "전부",
    "bakkwosseo": "바꿨어"
}

def is_probably_romanized_korean(text: str) -> bool:
    if not text or any('\uac00' <= c <= '\ud7af' for c in text):
        return False
    lowered = text.lower()
    tokens = re.findall(r"[a-z']+", lowered)
    short_mode = len(tokens) < 6
    korean_markers = {"eo", "eu", "ae", "ui", "ya", "yeo", "ye", "wa", "wo", "we", "wi", "ne", "neo", "na", "naega", "niga", "sarang", "geojitmal", "mianhae", "eob", "eobs", "itda", "jeong", "ham", "haneul", "bogo", "deon", "kkeut", "gatae", "molla", "mwoya", "ani", "geu", "neun", "neoreul", "jigeum"}
    marker_hits = mapped_hits = 0
    for token in tokens:
        if token in _ROMANIZED_KOREAN_WORDS:
            mapped_hits += 1
        if token in korean_markers or any(fragment in token for fragment in ("eo", "eu", "ae", "ui", "kke", "ssi", "jyo", "gwa", "wo", "ya", "yeo", "ye", "wa", "we", "wi", "ss", "ch", "pp", "tt", "kk", "jj", "eop", "jwos")):
            marker_hits += 1
    if short_mode:
        return mapped_hits >= 2 or marker_hits >= 2
    return mapped_hits >= 2 or (marker_hits >= 4 and (marker_hits / max(len(tokens), 1)) >= 0.2)

def _compose_hangul_syllable(onset: str, vowel: str, final: str = "") -> str:
    initial_index = _KOREAN_ONSETS.get(onset, 11)
    vowel_index = _KOREAN_VOWELS.get(vowel)
    if vowel_index is None: return ""
    final_index = _KOREAN_FINALS.get(final, 0)
    return chr(0xAC00 + ((initial_index * 21) + vowel_index) * 28 + final_index)

def _match_romanized_prefix(text: str, options: list[str]) -> tuple[str, int]:
    for option in options:
        if text.startswith(option): return option, len(option)
    return "", 0

def _starts_with_vowel(text: str) -> bool:
    return any(text.startswith(vowel) for vowel in sorted(_KOREAN_VOWELS, key=len, reverse=True))

def transliterate_romanized_korean(text: str) -> str:
    if not text: return text
    vowel_order = sorted(_KOREAN_VOWELS, key=len, reverse=True)
    onset_order = sorted(_KOREAN_ONSETS, key=len, reverse=True)
    final_order = sorted(_KOREAN_FINALS, key=len, reverse=True)

    def transliterate_token(token: str) -> str:
        normalized = token.lower()
        if normalized in _ROMANIZED_KOREAN_WORDS: return _ROMANIZED_KOREAN_WORDS[normalized]
        normalized = normalized.replace("rr", "r").replace("dd", "d")
        pieces = []
        index = 0
        while index < len(normalized):
            if not normalized[index].isalnum():
                index += 1
                continue
            remaining = normalized[index:]
            onset, onset_len = _match_romanized_prefix(remaining, onset_order)
            if onset_len == 0:
                if _starts_with_vowel(remaining): onset = "ng"
                else:
                    pieces.append(token[index])
                    index += 1
                    continue
            index += onset_len
            remaining = normalized[index:]
            vowel, vowel_len = _match_romanized_prefix(remaining, vowel_order)
            if vowel_len == 0:
                pieces.append(token[index - onset_len:index] if onset_len else token[index])
                index += 1
                continue
            index += vowel_len
            remaining = normalized[index:]
            
            consonant_run = []
            scan = 0
            while index + scan < len(normalized) and not _starts_with_vowel(normalized[index + scan:]):
                consonant_run.append(normalized[index + scan])
                scan += 1
            run_text = "".join(consonant_run)
            
            coda = ""
            if run_text:
                if index + scan >= len(normalized):
                    coda, coda_len = _match_romanized_prefix(run_text, final_order)
                    if coda_len == 0:
                        coda = run_text[-1]
                        coda_len = 1
                    scan = coda_len
                else:
                    next_onset = ""
                    next_onset_len = 0
                    for i in range(len(run_text)):
                        suffix = run_text[i:]
                        if suffix in _KOREAN_ONSETS and suffix != "ng":
                            next_onset = suffix
                            next_onset_len = len(suffix)
                            break
                    
                    leftover = run_text[:-next_onset_len] if next_onset_len > 0 else run_text
                    if leftover:
                        coda, coda_len = _match_romanized_prefix(leftover, final_order)
                        if coda_len == 0:
                            coda = leftover[0]
                            coda_len = 1
                        scan = coda_len
                    else:
                        coda = ""
                        scan = 0
                        
            syllable = _compose_hangul_syllable(onset, vowel, coda)
            pieces.append(syllable if syllable else token[index - onset_len - vowel_len:index])
            index += scan
        return "".join(pieces)

    result_parts = []
    cursor = 0
    for match in re.finditer(r"[A-Za-z']+|[^A-Za-z']+", text):
        if match.start() > cursor: result_parts.append(text[cursor:match.start()])
        segment = match.group(0)
        result_parts.append(transliterate_token(segment) if segment and segment[0].isalpha() else segment)
        cursor = match.end()
    if cursor < len(text): result_parts.append(text[cursor:])
    return "".join(result_parts)

def extract_romanization(text: str) -> str:
    if any('\uac00' <= c <= '\ud7af' for c in text):
        lines = text.split('\n')
        romanized_lines = []
        for line in lines:
            romanized = ''.join(c for c in line if c.isascii() and (c.isalpha() or c.isdigit() or c in ' \t.,!?:;"\'-()[]{}…'))
            romanized = re.sub(r'\s+', ' ', romanized).strip()
            if romanized: romanized_lines.append(romanized)
        result = '\n'.join(romanized_lines)
        return result if result.strip() else text
    return text