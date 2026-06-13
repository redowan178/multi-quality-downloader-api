from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI(title="Multi-Quality Social Downloader API")

@app.get("/")
def home():
    return {"status": "online", "message": "Your Downloader API is running perfectly!"}

@app.get("/analyze")
def analyze_video(url: str):
    # Safety Filter: Block YouTube to protect your developer account from being banned
    if "youtube.com" in url or "youtu.be" in url:
        raise HTTPException(
            status_code=400, 
            detail="YouTube downloads are restricted due to store safety policies."
        )

    # Core settings for scanning social media metadata
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Safely analyze the social media link
            info = ydl.extract_info(url, download=False)
            
            video_title = info.get('title', 'Social Media Media File')
            thumbnail = info.get('thumbnail', '')
            formats = info.get('formats', [])

            video_options = []
            audio_options = []
            seen_resolutions = set()

            for fmt in formats:
                stream_url = fmt.get('url')
                if not stream_url:
                    continue

                # Filter and separate audio files
                if fmt.get('vcodec') == 'none' and fmt.get('acodec') != 'none':
                    audio_options.append({
                        "quality": f"{int(fmt.get('abr', 128))}kbps Audio",
                        "extension": fmt.get('ext', 'mp3'),
                        "download_url": stream_url
                    })
                
                # Filter and separate video files
                elif fmt.get('vcodec') != 'none':
                    height = fmt.get('height')
                    if height:
                        resolution_label = f"{height}p"
                        
                        # Strip away duplicate entries
                        if resolution_label not in seen_resolutions:
                            seen_resolutions.add(resolution_label)
                            video_options.append({
                                "resolution": resolution_label,
                                "extension": fmt.get('ext', 'mp4'),
                                "download_url": stream_url
                            })

            # Sort the resolutions from highest quality (1080p) down to lowest (240p)
            video_options = sorted(video_options, key=lambda x: int(x['resolution'].replace('p', '')), reverse=True)

            return JSONResponse(content={
                "status": "success",
                "title": video_title,
                "thumbnail": thumbnail,
                "videos": video_options,
                "audios": audio_options
            })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scan link: {str(e)}")
