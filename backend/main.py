from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List

# Import our custom modules
from spotify_client import search_track
from recommendation_agent import remix_agent
from audio_acquisition import search_youtube_video, download_mp3
from audio_processor import create_remix

app = FastAPI(title="AI Remix Agent API")

# Configure CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- REQUEST MODELS ----
class SearchRequest(BaseModel):
    query: str

class RecommendRequest(BaseModel):
    title: str
    artist: str
    genre: str

class RemixRequest(BaseModel):
    base_title: str
    base_artist: str
    remix_title: str
    remix_artist: str
    target_bpm: int

# ---- ENDPOINTS ----

@app.get("/")
def read_root():
    return {"message": "AI Remix Agent API is running"}

@app.post("/api/search")
def api_search_track(req: SearchRequest):
    """Search Spotify for a base track."""
    raw_tracks = search_track(req.query, limit=5)
    formatted_tracks = []
    for t in raw_tracks:
        track_art = t['album']['images'][0]['url'] if t.get('album') and t['album'].get('images') else None
        formatted_tracks.append({
            "id": t['id'],
            "title": t['name'],
            "artist": t['artists'][0]['name'] if t.get('artists') else "Unknown",
            "art": track_art
        })
    return {"results": formatted_tracks}

@app.post("/api/recommend")
def api_recommend_tracks(req: RecommendRequest):
    """Use LangGraph to recommend compatible tracks."""
    initial_state = {
        "base_track_title": req.title,
        "base_track_artist": req.artist,
        "base_track_genre": req.genre,
        "recommendations": [],
        "error": ""
    }
    
    result = remix_agent.invoke(initial_state)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
        
    return {"recommendations": result["recommendations"]}

@app.post("/api/remix")
def api_generate_remix(req: RemixRequest):
    """Full pipeline: Search YT -> Download MP3s -> Process -> Return URL."""
    base_query = f"{req.base_title} {req.base_artist} Official Audio"
    remix_query = f"{req.remix_title} {req.remix_artist} Official Audio"
    
    # 1. Search YouTube
    base_vid = search_youtube_video(base_query)
    remix_vid = search_youtube_video(remix_query)
    
    if not base_vid or not remix_vid:
        raise HTTPException(status_code=404, detail="Could not find one or both tracks on YouTube.")
        
    # 2. Download MP3s (this is synchronous and will take time)
    os.makedirs("downloads", exist_ok=True)
    base_path = f"downloads/{base_vid}.mp3"
    remix_path = f"downloads/{remix_vid}.mp3"
    
    if not os.path.exists(base_path):
        download_mp3(base_vid, base_path)
    if not os.path.exists(remix_path):
        download_mp3(remix_vid, remix_path)
        
    if not os.path.exists(base_path) or not os.path.exists(remix_path):
        raise HTTPException(status_code=500, detail="Failed to download MP3 files.")
        
    # 3. Process Audio
    output_filename = f"remix_{base_vid}_{remix_vid}.wav"
    output_path = f"downloads/{output_filename}"
    
    try:
        if not os.path.exists(output_path):
            create_remix(base_path, remix_path, output_path, req.target_bpm)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
        
    # Ideally return a URL to serve the file. FastAPI StaticFiles would be used here.
    return {"message": "Remix completed successfully", "file": output_filename}
