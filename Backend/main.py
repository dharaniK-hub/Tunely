from fastapi import FastAPI
import httpx
from langdetect import detect

app = FastAPI()

# 🎵 Get lyrics
@app.get("/lyrics")
async def get_lyrics(artist: str, title: str):
    url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url)

    if res.status_code != 200:
        return {"error": "Lyrics not found"}
    
    lyrics = res.json().get("lyrics", "")
    return {"lyrics": lyrics}


# 🌍 Translate lyrics
@app.post("/translate")
async def translate(text: str):
    lang = detect(text)

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://libretranslate.de/translate",
            data={
                "q": text,
                "source": lang,
                "target": "en",
                "format": "text"
            }
        )

    return res.json()