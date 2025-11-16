"""
Podcast Analyzer - FastAPI Backend (Mostly Mid)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json
import os
from analyzer import (
    analyze_podcast,
    load_transcript,
    load_metadata,
    save_analysis_cache,
    load_analysis_cache
)

app = FastAPI(title="Mostly Mid - Podcast Analyzer")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to read HTML files
def get_html(filename):
    with open(f"static/{filename}", 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serve the main HTML page"""
    return get_html("index.html")  # Changed from index.html

@app.get("/analyze/{podcast_id}", response_class=HTMLResponse)
def view_analysis(podcast_id: str):
    """Serve the results page"""
    return get_html("results.html")

@app.get("/api/podcasts")
def list_podcasts():
    """Get list of available podcasts"""
    try:
        with open("transcripts_metadata.json") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Metadata file not found")

@app.get("/api/analyze/{podcast_id}")
def analyze_api(podcast_id: str, use_cache: bool = True):
    """
    Analyze a podcast transcript
    """
    try:
        # Check cache first
        if use_cache:
            cached = load_analysis_cache(podcast_id)
            if cached:
                return cached
        
        # Analyze
        result = analyze_podcast(podcast_id, use_cache=False)
        return result
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Podcast '{podcast_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Mostly Mid API"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"🔥 Starting Mostly Mid on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)