from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
import yt_dlp

app = FastAPI(title="Multi-Quality Social Downloader API")

@app.get("/")
def home():
    return {"status": "online", "message": "Your Downloader API is running perfectly!"}

@app.get("/analyze")
def analyze_video(url: str):
    # Safety Rule: Block YouTube downloading streams to protect Google Play policies
    if "youtube.com" in url or "youtu.be" in url:
        raise HTTPException(
            status_code=400, 
            detail="YouTube downloads are restricted due to store safety policies."
        )

    video_options = []
    audio_options = []
    video_title = "Social Media File"

    # ==========================================
    # ROUTE 1: TIKTOK FIREWALL BYPASS STRATEGY
    # ==========================================
    if "tiktok.com" in url:
        try:
            # Clean tracking garbage strings out of the incoming mobile link parameter
            clean_url = url.split('?')[0]
            
            # Send payload request via residential web worker API to bypass Render IP block
            api_endpoint = f"https://tikwm.com{clean_url}"
            response = requests.get(api_endpoint, timeout=15).json()

            if response.get("code") == 0:
                data = response.get("data", {})
                video_title = data.get("title", "TikTok Video")
                
                hd_url = data.get("hdplay")      # 1080p stream link
                regular_url = data.get("play")   # 720p stream link
                audio_url = data.get("music")    # MP3 background audio link

                if hd_url:
                    video_options.append({
                        "resolution": "1080p (HD No Watermark)",
                        "extension": "mp4",
                        "download_url": f"https://www.tikwm.com{hd_url}"
                    })
                if regular_url:
                    video_options.append({
                        "resolution": "720p (Standard No Watermark)",
                        "extension": "mp4",
                        "download_url": f"https://www.tikwm.com{regular_url}"
                    })
                if audio_url:
                    audio_options.append({
                        "quality": "128kbps Audio Track",
                        "extension": "mp3",
                        "download_url": audio_url
                    })
            else:
                raise HTTPException(status_code=400, detail="TikTok link could not be parsed. Private video or broken URL.")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TikTok Module Error: {str(e)}")

    # ==========================================
    # ROUTE 2: FACEBOOK, INSTAGRAM, & X ENGINE
    # ==========================================
    else:
        # Standard web configuration settings to load metadata
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise HTTPException(status_code=404, detail="Could not retrieve video streaming data.")

                video_title = info.get('title', 'Social Media File')
                formats = info.get('formats', [])
                seen_resolutions = set()

                for fmt in formats:
                    stream_url = fmt.get('url')
                    if not stream_url:
                        continue

                    # Capture extraction criteria for standalone audio profile tags
                    if fmt.get('vcodec') == 'none' and fmt.get('acodec') != 'none':
                        bitrate = fmt.get('abr', 128)
                        audio_options.append({
                            "quality": f"{int(bitrate)}kbps Audio",
                            "extension": fmt.get('ext', 'mp3'),
                            "download_url": stream_url
                        })
                    
                    # Capture extraction criteria for video profile tags
                    elif fmt.get('vcodec') != 'none':
                        height = fmt.get('height')
                        if height:
                            res_label = f"{height}p"
                            if res_label not in seen_resolutions:
                                seen_resolutions.add(res_label)
                                video_options.append({
                                    "resolution": res_label,
                                    "extension": fmt.get('ext', 'mp4'),
                                    "download_url": stream_url
                                })

                # Order quality indexes downwards dynamically from 1080p to lower tiers
                if video_options:
                    video_options = sorted(video_options, key=lambda x: int(x['resolution'].replace('p', '')), reverse=True)
                
                # Global engine safety fallback if platform profile arrays are completely blocked
                if not video_options and info.get('url'):
                    video_options.append({
                        "resolution": "Default Resolution",
                        "extension": info.get('ext', 'mp4'),
                        "download_url": info.get('url')
                    })

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Core Engine Scan Error: {str(e)}")

    # Send the structured uniform response packets block down to Sketchware client
    return JSONResponse(content={
        "status": "success",
        "title": video_title,
        "videos": video_options,
        "audios": audio_options
    })
