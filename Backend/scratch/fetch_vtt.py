import yt_dlp
import httpx

def test_fetch_vtt():
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
            
            # Find a Spanish subtitle key (keys starting with 'es')
            es_key = None
            for key in subtitles.keys():
                if key.startswith('es'):
                    es_key = key
                    break
            
            if es_key:
                print(f"Found Spanish subtitle key: {es_key}")
                formats = subtitles[es_key]
                vtt_url = None
                for fmt in formats:
                    if fmt.get('ext') == 'vtt':
                        vtt_url = fmt.get('url')
                        break
                
                if vtt_url:
                    print(f"VTT URL: {vtt_url[:100]}...")
                    # Fetch first 500 bytes of the VTT content
                    res = httpx.get(vtt_url)
                    if res.status_code == 200:
                        print("\nFirst 400 characters of VTT:")
                        print(res.text[:400])
                    else:
                        print(f"Failed to fetch VTT content: {res.status_code}")
                else:
                    print("No VTT format found for Spanish subtitles.")
            else:
                print("No Spanish subtitles found.")

if __name__ == "__main__":
    test_fetch_vtt()
