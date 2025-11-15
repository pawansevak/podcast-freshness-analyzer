"""
Podcast Analyzer - FastAPI Backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import os
from analyzer import (
    analyze_podcast,
    load_transcript,
    load_user_preferences,
    save_analysis_cache,
    load_analysis_cache
)

app = FastAPI(title="Podcast Analyzer API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserPreferences(BaseModel):
    topics_of_interest: list[str]
    freshness_priority: str
    insight_style: str
    avoid_topics: list[str] = []


class UserRating(BaseModel):
    podcast_id: str
    user_id: str
    freshness_rating: int
    insight_rating: int
    feedback: str = ""


@app.get("/")
def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")


@app.get("/api/podcasts")
def list_podcasts():
    """Get list of available podcasts"""
    try:
        with open("transcripts_metadata.json") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Metadata file not found")


@app.get("/api/analyze/{podcast_id}")
def analyze(podcast_id: str, user_id: str = "default", use_cache: bool = True):
    """
    Analyze a podcast transcript
    
    Args:
        podcast_id: ID of the podcast to analyze
        user_id: User ID for personalized analysis
        use_cache: Whether to use cached results if available
    """
    try:
        # Check cache first
        if use_cache:
            cached = load_analysis_cache(podcast_id, user_id)
            if cached:
                return {
                    **cached,
                    "cached": True
                }
        
        # Load transcript and user preferences
        transcript = load_transcript(podcast_id)
        user_prefs = load_user_preferences(user_id)
        
        # Analyze
        result = analyze_podcast(transcript, user_prefs)
        
        # Cache the result
        save_analysis_cache(podcast_id, user_id, result)
        
        return {
            **result,
            "cached": False
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/preferences/{user_id}")
def get_preferences(user_id: str = "default"):
    """Get user preferences"""
    try:
        return load_user_preferences(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/preferences/{user_id}")
def update_preferences(user_id: str, preferences: UserPreferences):
    """Update user preferences"""
    try:
        os.makedirs("users", exist_ok=True)
        filepath = f"users/{user_id}_preferences.json"
        
        with open(filepath, 'w') as f:
            json.dump(preferences.dict(), f, indent=2)
        
        return {"status": "success", "message": "Preferences updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rating")
def submit_rating(rating: UserRating):
    """Submit user rating for a podcast analysis"""
    try:
        os.makedirs("users/ratings", exist_ok=True)
        filepath = f"users/ratings/{rating.user_id}_{rating.podcast_id}.json"
        
        rating_data = {
            **rating.dict(),
            "submitted_at": str(os.times())
        }
        
        with open(filepath, 'w') as f:
            json.dump(rating_data, f, indent=2)
        
        return {"status": "success", "message": "Rating submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Podcast Analyzer API"}


# Mount static files last
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    print("Starting Podcast Analyzer API server...")
    print("Visit http://localhost:8000 to use the app")
    uvicorn.run(app, host="0.0.0.0", port=8000)
