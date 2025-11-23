"""
Podcast Analyzer - FastAPI Backend (Mostly Mid)
Updated with landing page and /episodes route
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import os
from pathlib import Path
from typing import List, Dict, Any

app = FastAPI(title="Mostly Mid - Podcast Analyzer")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if directory exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration - look in BOTH folders
CACHE_DIR = Path("cache")
TRANSCRIPTS_DIR = Path("transcripts")


def load_episodes() -> List[Dict[str, Any]]:
    """
    Load all episode analyses - looks in BOTH cache/ and transcripts/ folders
    Supports BOTH old (critical) and new (hybrid) formats
    """
    episodes = []
    
    # Look in BOTH cache/ and transcripts/ folders
    analysis_files = []
    
    if CACHE_DIR.exists():
        analysis_files.extend(list(CACHE_DIR.glob("*_analysis_critical.json")))
        analysis_files.extend(list(CACHE_DIR.glob("*_analysis_hybrid.json")))
    
    if TRANSCRIPTS_DIR.exists():
        analysis_files.extend(list(TRANSCRIPTS_DIR.glob("*_analysis_critical.json")))
        analysis_files.extend(list(TRANSCRIPTS_DIR.glob("*_analysis_hybrid.json")))
    
    print(f"Found {len(analysis_files)} analysis files")
    
    for analysis_file in analysis_files:
        try:
            with open(analysis_file) as f:
                data = json.load(f)
            
            # Extract episode ID
            episode_id = analysis_file.stem.replace("_analysis_critical", "").replace("_analysis_hybrid", "")
            
            # Check if this is hybrid format (has "scores" object) or old format (has flat scores)
            is_hybrid = "scores" in data and isinstance(data["scores"], dict)
            
            if is_hybrid:
                # NEW HYBRID FORMAT
                episode = {
                    "id": episode_id,
                    "title": format_title(episode_id),
                    "format": "hybrid",
                    
                    # All 6 dimension scores
                    "overall_score": data["scores"]["overall"],
                    "insight_density": data["scores"]["insight_density"],
                    "signal_to_noise": data["scores"]["signal_to_noise"],
                    "actionability": data["scores"]["actionability"],
                    "contrarian_index": data["scores"]["contrarian_index"],
                    "freshness": data["scores"]["freshness"],
                    "host_quality": data["scores"]["host_quality"],
                    
                    # Verdict fields
                    "tldr": data.get("verdict", {}).get("tldr", ""),
                    "best_for": data.get("verdict", {}).get("best_for", ""),
                    "skip_if": data.get("verdict", {}).get("skip_if", ""),
                    "worth_it": data.get("verdict", {}).get("worth_it", False),
                    "best_quote": data.get("verdict", {}).get("best_quote", ""),
                    
                    # Top 5 takeaways
                    "top_5_takeaways": data.get("top_5_takeaways", []),
                    "top_insight": data.get("top_5_takeaways", [{}])[0].get("insight", "") if data.get("top_5_takeaways") else "",
                    "top_insight_timestamp": data.get("top_5_takeaways", [{}])[0].get("timestamp", "") if data.get("top_5_takeaways") else "",
                    
                    # Count truly non-obvious
                    "truly_non_obvious_count": sum(
                        1 for t in data.get("top_5_takeaways", []) 
                        if t.get("obviousness_level") == "truly_non_obvious"
                    ),
                    
                    # Other fields
                    "summary": data.get("summary", ""),
                    "characteristics": data.get("characteristics", []),
                    "obvious_insights_rejected": data.get("obvious_insights_rejected", []),
                    "why_these_scores": data.get("why_these_scores", {}),
                }
            else:
                # OLD CRITICAL FORMAT (fallback)
                episode = {
                    "id": episode_id,
                    "title": format_title(episode_id),
                    "format": "old",
                    
                    # Map old format to new
                    "overall_score": (data.get("freshness_score", 5) + data.get("insight_score", 5)) / 2,
                    "insight_density": data.get("insight_score", 5),
                    "freshness": data.get("freshness_score", 5),
                    "signal_to_noise": 5,  # Not in old format
                    "actionability": 5,  # Not in old format
                    "contrarian_index": 5,  # Not in old format
                    "host_quality": 5,  # Not in old format
                    
                    # Old format fields
                    "tldr": data.get("summary", ""),
                    "best_for": "Experienced PMs",  # Generic fallback
                    "skip_if": "",
                    "worth_it": data.get("insight_score", 5) >= 6,
                    "best_quote": "",
                    
                    # Top 5 from old format
                    "top_5_takeaways": data.get("top_5_takeaways", []),
                    "top_insight": data.get("top_5_takeaways", [{}])[0].get("insight", "") if data.get("top_5_takeaways") else "",
                    "top_insight_timestamp": data.get("top_5_takeaways", [{}])[0].get("timestamp", "") if data.get("top_5_takeaways") else "",
                    
                    "truly_non_obvious_count": sum(
                        1 for t in data.get("top_5_takeaways", []) 
                        if t.get("obviousness_level") == "truly_non_obvious"
                    ),
                    
                    "summary": data.get("summary", ""),
                    "characteristics": data.get("characteristics", []),
                    "obvious_insights_rejected": data.get("obvious_insights_rejected", []),
                    "why_these_scores": {},
                }
            
            episodes.append(episode)
            
        except Exception as e:
            print(f"Error loading {analysis_file}: {e}")
            import traceback
            traceback.print_exc()
    
    # Remove duplicates (prefer cache/ over transcripts/)
    seen_ids = {}
    unique_episodes = []
    for ep in episodes:
        if ep["id"] not in seen_ids:
            unique_episodes.append(ep)
            seen_ids[ep["id"]] = True
    
    # Sort by overall score descending
    unique_episodes.sort(key=lambda x: x["overall_score"], reverse=True)
    
    return unique_episodes


def format_title(episode_id: str) -> str:
    """Format episode ID into a readable title"""
    title = episode_id.replace("_", " ").title()
    if len(title) > 100:
        title = title[:97] + "..."
    return title


def calculate_stats(episodes: List[Dict]) -> Dict[str, Any]:
    """Calculate aggregate statistics"""
    if not episodes:
        return {
            "total": 0,
            "avg_score": 0,
            "high_quality": 0,
            "worth_listening": 0,
            "avg_non_obvious": 0
        }
    
    scores = [ep["overall_score"] for ep in episodes]
    
    return {
        "total": len(episodes),
        "avg_score": round(sum(scores) / len(scores), 1),
        "high_quality": sum(1 for s in scores if s >= 7),
        "worth_listening": sum(1 for ep in episodes if ep.get("worth_it", False)),
        "avg_non_obvious": round(
            sum(ep.get("truly_non_obvious_count", 0) for ep in episodes) / len(episodes), 1
        ) if episodes else 0
    }


def get_html(filename):
    """Read HTML file from static directory"""
    try:
        with open(f"static/{filename}", 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"HTML file '{filename}' not found")


# Routes

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serve the landing page"""
    return get_html("index.html")


@app.get("/episodes", response_class=HTMLResponse)
def episodes_page():
    """Serve the episodes list page"""
    return get_html("episodes.html")


@app.get("/episode/{episode_id}", response_class=HTMLResponse)
def episode_detail_page(episode_id: str):
    """Serve episode detail page"""
    return get_html("episode.html")


@app.get("/analyze/{podcast_id}", response_class=HTMLResponse)
def view_analysis_legacy(podcast_id: str):
    """Legacy endpoint"""
    return get_html("results.html")


@app.get("/api/episodes")
def list_episodes():
    """Get list of all analyzed episodes"""
    try:
        episodes = load_episodes()
        stats = calculate_stats(episodes)
        
        return {
            "episodes": episodes,
            "stats": stats,
            "total": len(episodes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading episodes: {str(e)}")


@app.get("/api/episode/{episode_id}")
def get_episode(episode_id: str):
    """Get detailed data for a specific episode"""
    try:
        episodes = load_episodes()
        episode = next((ep for ep in episodes if ep["id"] == episode_id), None)
        
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode '{episode_id}' not found")
        
        return episode
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/podcasts")
def list_podcasts():
    """Legacy endpoint - for backwards compatibility"""
    try:
        with open("transcripts_metadata.json") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fall back to new format
        return list_episodes()


@app.get("/api/analyze/{podcast_id}")
def analyze_api(podcast_id: str, use_cache: bool = True):
    """
    Get analysis for a podcast (legacy endpoint)
    """
    try:
        episodes = load_episodes()
        episode = next((ep for ep in episodes if ep["id"] == podcast_id), None)
        
        if not episode:
            raise HTTPException(status_code=404, detail=f"Podcast '{podcast_id}' not found")
        
        return episode
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    episodes = load_episodes()
    return {
        "status": "healthy",
        "service": "Mostly Mid API",
        "version": "2.0 (Hybrid Analyzer)",
        "episodes_loaded": len(episodes)
    }

@app.route('/episode/<episode_id>')
def episode_detail(episode_id):
    return send_from_directory('static', 'episode.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"🎯 Starting Mostly Mid (Hybrid Analyzer) on port {port}")
    print(f"📊 Looking for analyses in: {CACHE_DIR} and {TRANSCRIPTS_DIR}")
    
    episodes = load_episodes()
    if episodes:
        stats = calculate_stats(episodes)
        print(f"✅ Loaded {stats['total']} episodes")
        print(f"📈 Average score: {stats['avg_score']}/10")
        print(f"🎯 High quality (7+): {stats['high_quality']}")
        print(f"💡 Avg non-obvious insights: {stats['avg_non_obvious']}/5")
    else:
        print("⚠️  No episodes found. Run analyzer_hybrid.py to analyze episodes!")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
