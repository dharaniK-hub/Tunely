import yt_dlp
import json

def test_yt_subtitles_clean():
    # Search for Enrique Iglesias Bailando on YouTube
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
            
            subtitles = entry.get('subtitles', {})
            automatic_captions = entry.get('automatic_captions', {})
            
            print(f"Subtitles: {list(subtitles.keys())}")
            # Filter automatic captions to keep it short
            auto_keys = list(automatic_captions.keys())
            print(f"Auto captions count: {len(auto_keys)}")
            print(f"Auto captions sample: {auto_keys[:10]}")
            
            # If Spanish subtitle (es) exists, let's check its formats
            if 'es' in subtitles:
                print("\nSpanish subtitle formats:")
                for fmt in subtitles['es']:
                    print(f"  Format ext: {fmt.get('ext')}, URL: {fmt.get('url')[:60]}...")
            # If auto-generated Spanish exists
            elif 'es' in automatic_captions:
                print("\nAuto Spanish caption formats:")
                for fmt in automatic_captions['es']:
                    print(f"  Format ext: {fmt.get('ext')}, URL: {fmt.get('url')[:60]}...")

if __name__ == "__main__":
    test_yt_subtitles_clean()
