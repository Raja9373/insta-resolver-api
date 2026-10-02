from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import re

app = FastAPI(title="AllFreeTools Instagram Resolver - Unlimited")

# Allow your AI Studio / frontend to call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_url(url: str) -> str:
    # Remove extra params, keep clean instagram url
    return url.split("?")[0].strip()

@app.get("/")
def home():
    return {"status": "ok", "message": "Instagram Resolver API is Running - Use /convert?url=INSTAGRAM_URL"}

@app.get("/convert")
def convert(url: str = Query(..., description="Instagram Reel/Post URL")):
    url = clean_url(url)
    
    # Validate instagram url
    if "instagram.com" not in url:
        raise HTTPException(status_code=400, detail="Invalid Instagram URL")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        'format': 'best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # yt-dlp sometimes returns playlist for reels, handle it
            if 'entries' in info:
                info = info['entries'][0]

            video_url = info.get('url') or info.get('requested_formats', [{}])[0].get('url')
            thumbnail = info.get('thumbnail')
            title = info.get('title') or info.get('fulltitle') or "Instagram Video"
            ext = info.get('ext', 'mp4')
            
            # Fallback: try to find best mp4 url in formats
            if not video_url and 'formats' in info:
                # find mp4 with both video+audio
                for f in reversed(info['formats']):
                    if f.get('ext') == 'mp4' and f.get('vcodec') != 'none':
                        video_url = f.get('url')
                        break
            
            if not video_url:
                raise HTTPException(status_code=404, detail="Video URL not found. Post may be private.")

            return {
                "status": "success",
                "title": title,
                "video_url": video_url,
                "thumbnail": thumbnail,
                "ext": ext,
                "original_url": url
            }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"RESOLVER_ERROR: {str(e)}")

# For Render.com - it will use this port
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
