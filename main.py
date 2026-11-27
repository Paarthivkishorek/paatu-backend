from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import yt_dlp
import requests
import os

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Paatu Backend is Live!"}

@app.get("/stream/{video_id}")
def stream_audio(video_id: str, request: Request):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android_vr", "tv", "ios"]
            }
        },
    }

    # Optional: If cookies.txt is added on Render later, it will auto-use it
    if os.path.exists("/etc/secrets/cookies.txt"):
        ydl_opts["cookiefile"] = "/etc/secrets/cookies.txt"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]
            http_headers = info.get("http_headers", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    range_header = request.headers.get("range")
    if range_header:
        http_headers["Range"] = range_header

    req = requests.get(audio_url, headers=http_headers, stream=True)

    response_headers = {
        "Content-Type": req.headers.get("Content-Type", "audio/mp4"),
        "Accept-Ranges": "bytes",
    }
    if "Content-Length" in req.headers:
        response_headers["Content-Length"] = req.headers["Content-Length"]
    if "Content-Range" in req.headers:
        response_headers["Content-Range"] = req.headers["Content-Range"]

    return StreamingResponse(
        req.iter_content(chunk_size=65536),
        status_code=req.status_code,
        headers=response_headers,
    )
