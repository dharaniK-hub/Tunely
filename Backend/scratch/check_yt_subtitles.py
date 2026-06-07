import yt_dlp
import json

def test_yt_subtitles():
    # Let's search for Enrique Iglesias Bailando on YouTube
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
            print(f"Title: {entry.get('title')}")
            print(f"ID: {entry.get('id')}")
            
            # Print formats and keys related to subtitles
            print("\nAvailable keys in entry:")
            print([k for k in entry.keys() if 'sub' in k or 'caption' in k])
            
            subtitles = entry.get('subtitles', {})
            automatic_captions = entry.get('automatic_captions', {})
            
            print(f"\nSubtitles languages: {list(subtitles.keys())}")
            print(f"Automatic captions languages: {list(automatic_captions.keys())}")
            
            # Let's inspect Spanish or English if available
            for lang in ['es', 'en', 'es-419']:
                if lang in subtitles:
                    print(f"\nExplicit subtitle found for {lang}:")
                    print(json.dumps(subtitles[lang][:3], indent=2))
                elif lang in automatic_captions:
                    print(f"\nAutomatic caption found for {lang}:")
                    print(json.dumps(automatic_captions[lang][:3], indent=2))

if __name__ == "__main__":
    test_yt_subtitles()
