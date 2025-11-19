#!/usr/bin/env python3
"""
Generate metadata for all cached podcasts
"""

import os
import json

def create_metadata():
    cache_dir = "cache"
    transcripts_dir = "transcripts"
    
    # Get all cached analyses
    cache_files = [f for f in os.listdir(cache_dir) if f.endswith('_analysis_critical.json')]
    
    metadata = {}
    
    for cache_file in cache_files:
        # Extract podcast ID from filename
        podcast_id = cache_file.replace('_analysis_critical.json', '')
        
        # Load the analysis
        with open(os.path.join(cache_dir, cache_file), 'r') as f:
            analysis = json.load(f)
        
        # Create a readable title from podcast_id
        title = podcast_id.replace('_', ' ').title()
        
        # Limit title length
        if len(title) > 80:
            title = title[:77] + "..."
        
        metadata[podcast_id] = {
            "title": title,
            "freshness_score": analysis.get("freshness_score", 5),
            "insight_score": analysis.get("insight_score", 5),
            "summary": analysis.get("summary", "No summary available"),
            "top_insight": analysis.get("top_5_takeaways", [{}])[0].get("insight", "No insights available") if analysis.get("top_5_takeaways") else "No insights available"
        }
    
    # Save metadata
    with open('transcripts_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Created metadata for {len(metadata)} podcasts")
    print(f"💾 Saved to transcripts_metadata.json")

if __name__ == "__main__":
    create_metadata()
