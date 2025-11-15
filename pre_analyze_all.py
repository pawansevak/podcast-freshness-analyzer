"""
Pre-analyze all podcasts and cache results
"""

import os
import json
from analyzer_llm import analyze_podcast, load_metadata

def get_all_podcast_ids():
    """Get list of all podcast IDs"""
    podcast_ids = []
    
    if os.path.exists('transcripts'):
        for filename in os.listdir('transcripts'):
            if filename.endswith('.txt'):
                podcast_id = filename.replace('.txt', '')
                podcast_ids.append(podcast_id)
    
    return sorted(podcast_ids)


def pre_analyze_all(force_reanalyze=False):
    """Analyze all podcasts and cache results"""
    
    podcast_ids = get_all_podcast_ids()
    
    print(f"Found {len(podcast_ids)} podcasts to analyze")
    print("="*60)
    
    results_summary = []
    
    for i, podcast_id in enumerate(podcast_ids, 1):
        print(f"\n[{i}/{len(podcast_ids)}] Processing: {podcast_id}")
        
        try:
            result = analyze_podcast(podcast_id, use_cache=not force_reanalyze)
            
            metadata = load_metadata(podcast_id)
            results_summary.append({
                "podcast_id": podcast_id,
                "title": metadata.get("title", podcast_id),
                "freshness_score": result["freshness_score"],
                "insight_score": result["insight_score"],
                "characteristics": result.get("characteristics", [])
            })
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Sort by insight score
    results_summary.sort(key=lambda x: x.get("insight_score", 0), reverse=True)
    
    print("\n" + "="*60)
    print("Top Podcasts by Insight Score:")
    for i, result in enumerate(results_summary[:10], 1):
        if "error" not in result:
            print(f"{i}. {result['title'][:50]}")
            print(f"   Freshness: {result['freshness_score']}/10 | Insights: {result['insight_score']}/10\n")
    
    # Save summary
    os.makedirs('cache', exist_ok=True)
    with open('cache/analysis_summary.json', 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"Total analyzed: {len(podcast_ids)}")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    pre_analyze_all(force_reanalyze=force)
