from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import yt_dlp
import re

app = FastAPI(title="Multi-Quality Social Downloader API")

@app.get("/")
def home():
    return {"status": "online", "message": "API running perfectly!"}

@app.get("/analyze")
def analyze_video(url: str):
    if "youtube.com" in url or "youtu.be" in url:
        raise HTTPException(
            status_code=400, 
            detail="YouTube downloads are restricted due to store safety policies."
        )

    # Base Extraction Configuration
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.tiktok.com/',
        }
    }

    # Clean TikTok tracking metrics from link before scanning
    if "tiktok.com" in url:
        url = url.split('?')[0]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Anti-Block Failover Strategy
            if not info:
                # Force retry utilizing alternative fallback arguments
                ydl_opts['force_generic_extractor'] = True
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_fallback:
                    info = ydl_fallback.extract_info(url, download=False)
            
            if not info:
                raise HTTPException(status_code=400, detail="TikTok security verification block. Please try again.")

            video_title = info.get('title', 'Social Media File')
            thumbnail = info.get('thumbnail', '')
            formats = info.get('formats', [])

            video_options = []
            audio_options = []
            seen_resolutions = set()

            for fmt in formats:
                stream_url = fmt.get('url')
                if not stream_url:
                    continue

                if fmt.get('vcodec') == 'none' and fmt.get('acodec') != 'none':
                    audio_options.append({
                        "quality": f"{int(fmt.get('abr', 128))}kbps Audio",
                        "extension": fmt.get('ext', 'mp3'),
                        "download_url": stream_url
                    })
                
                elif fmt.get('vcodec') != 'none':
                    height = fmt.get('height')
                    resolution_label = f"{height}p" if height else "Default HD"
                    
                    if resolution_label not in seen_resolutions:
                        seen_resolutions.add(resolution_label)
                        video_options.append({
                            "resolution": resolution_label,
                            "extension": fmt.get('ext', 'mp4'),
                            "download_url": stream_url
                        })

            # Format list organizer 
            if video_options and any(x['resolution'] != "Default HD" for x in video_options):
                video_options = sorted(
                    [x for x in video_options if 'p' in x['resolution']], 
                    key=lambda x: int(x['resolution'].replace('p', '')), 
                    reverse=True
                )
            
            # Global Fallback if formats dictionary gets stripped by TikTok filters
            if not video_options and info.get('url'):
                video_options.append({
                    "resolution": "Default High Quality",
                    "extension": info.get('ext', 'mp4'),
                    "download_url": info.get('url')
                })

            return JSONResponse(content={
                "status": "success",
                "title": video_title,
                "thumbnail": thumbnail,
                "videos": video_options,
                "audios": audio_options
            })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
