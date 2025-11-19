#!/usr/bin/env python3
"""
Batch analyze all podcasts and cache results
Run this locally before deploying to avoid API costs in production
"""

import os
import json
from analyzer import analyze_podcast, load_metadata

def batch_analyze_all_podcasts():
    """Analyze all podcasts found in transcripts/ directory"""
    
    # Get list of all transcripts
    transcript_dir = "transcripts"
    
    if not os.path.exists(transcript_dir):
        print(f"❌ {transcript_dir} directory not found!")
        return
    
    # Get all .txt files
    transcript_files = [f for f in os.listdir(transcript_dir) if f.endswith('.txt')]
    podcast_ids = [f.replace('.txt', '') for f in transcript_files]
    
    print(f"📊 Found {len(podcast_ids)} podcasts to analyze")
    print("=" * 60)
    
    results = []
    
    for i, podcast_id in enumerate(podcast_ids, 1):
        print(f"\n[{i}/{len(podcast_ids)}] Analyzing: {podcast_id}")
        print("-" * 60)
        
        try:
            # Analyze (will use cache if exists)
            analysis = analyze_podcast(podcast_id, use_cache=True)
            
            # Get metadata for display
            metadata = load_metadata(podcast_id)
            title = metadata.get('title', podcast_id)
            
            results.append({
                'id': podcast_id,
                'title': title,
                'freshness': analysis.get('freshness_score'),
                'insights': analysis.get('insight_score'),
                'cached': True
            })
            
            print(f"✓ {title}")
            print(f"  Freshness: {analysis.get('freshness_score')}/10")
            print(f"  Insights: {analysis.get('insight_score')}/10")
            
        except Exception as e:
            print(f"❌ Error analyzing {podcast_id}: {e}")
            results.append({
                'id': podcast_id,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 BATCH ANALYSIS COMPLETE")
    print("=" * 60)
    
    successful = [r for r in results if 'freshness' in r]
    failed = [r for r in results if 'error' in r]
    
    print(f"\n✓ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        avg_freshness = sum(r['freshness'] for r in successful) / len(successful)
        avg_insights = sum(r['insights'] for r in successful) / len(successful)
        print(f"\n📊 Average Scores:")
        print(f"  Freshness: {avg_freshness:.1f}/10")
        print(f"  Insights: {avg_insights:.1f}/10")
    
    # Save summary
    with open('cache/batch_summary.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Summary saved to cache/batch_summary.json")
    print("\n🚀 Ready to deploy! Run: git add cache/ && git commit -m 'Add cached analyses' && git push")


if __name__ == "__main__":
    print("🤖 BATCH PODCAST ANALYZER")
    print("=" * 60)
    print("This will analyze all podcasts in transcripts/ directory")
    print("and cache the results to avoid API costs in production.")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ANTHROPIC_API_KEY not set!")
        print("Run: export ANTHROPIC_API_KEY='your-key-here'")
        print("Or add it to your .env file")
        exit(1)
    
    input("\nPress ENTER to start batch analysis (this will cost ~$0.50 per new podcast)...")
    
    batch_analyze_all_podcasts()
