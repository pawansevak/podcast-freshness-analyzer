"""
Standalone Podcast Analyzer Demo
No external dependencies required - just Python!
"""

import json
import os

def analyze_transcript(transcript_text):
    """
    Simple analysis without LLM - uses heuristics
    """
    transcript_lower = transcript_text.lower()
    
    # Check for indicators
    has_data = any(word in transcript_lower for word in 
                   ['study', 'research', 'data', 'percent', '%', 'participants'])
    has_examples = any(word in transcript_lower for word in 
                      ['example', 'specifically', 'instance', 'for instance'])
    has_recent = any(word in transcript_lower for word in 
                    ['2024', '2025', 'recent', 'latest', 'emerging'])
    has_generic = any(phrase in transcript_lower for phrase in 
                     ['work hard', 'stay focused', 'never give up', 'hustle'])
    
    # Score based on content
    if has_data and has_examples and has_recent:
        freshness = 8
        insight = 8
        summary = "Excellent podcast with specific data, concrete examples, and recent information."
    elif has_data and has_examples:
        freshness = 7
        insight = 7
        summary = "Strong podcast with data-driven insights and specific examples."
    elif has_generic:
        freshness = 3
        insight = 3
        summary = "Generic content with common advice and few specific insights."
    else:
        freshness = 5
        insight = 5
        summary = "Moderate content with some useful information but room for more depth."
    
    return {
        "freshness_score": freshness,
        "insight_score": insight,
        "summary": summary,
        "has_data": has_data,
        "has_examples": has_examples,
        "has_recent": has_recent
    }


def print_bar(score, width=10):
    """Print a visual bar chart"""
    filled = "█" * score
    empty = "░" * (width - score)
    return f"[{filled}{empty}]"


def main():
    print("=" * 70)
    print("PODCAST ANALYZER - STANDALONE DEMO")
    print("No external packages required!")
    print("=" * 70)
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("transcripts"):
        print("❌ Error: Can't find transcripts/ folder")
        print("   Make sure you're running this from the podcast-analyzer directory")
        return
    
    # Load metadata
    try:
        with open("transcripts_metadata.json", "r") as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print("❌ Error: Can't find transcripts_metadata.json")
        return
    
    # Analyze each podcast
    results = []
    for podcast_id, info in metadata.items():
        print(f"\n📊 Analyzing: {info['title']}")
        print("-" * 70)
        
        # Load transcript
        try:
            with open(f"transcripts/{podcast_id}.txt", "r") as f:
                transcript = f.read()
        except FileNotFoundError:
            print(f"   ⚠️  Transcript file not found: {podcast_id}.txt")
            continue
        
        # Analyze
        result = analyze_transcript(transcript)
        results.append((info['title'], result))
        
        # Display results
        print(f"Freshness: {result['freshness_score']}/10")
        print(f"Insights:  {result['insight_score']}/10")
        print(f"Summary:   {result['summary']}")
        
        print("\nContent Characteristics:")
        print(f"  • Specific data: {'✓' if result['has_data'] else '✗'}")
        print(f"  • Concrete examples: {'✓' if result['has_examples'] else '✗'}")
        print(f"  • Recent references: {'✓' if result['has_recent'] else '✗'}")
    
    # Comparison
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print()
    
    for title, result in results:
        fresh_bar = print_bar(result['freshness_score'])
        insight_bar = print_bar(result['insight_score'])
        
        print(f"{title[:40]:40s}")
        print(f"  Freshness: {fresh_bar} {result['freshness_score']}/10")
        print(f"  Insights:  {insight_bar} {result['insight_score']}/10")
        print()
    
    print("=" * 70)
    print("✅ Demo Complete!")
    print()
    print("To use the full web interface:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Run server: python app.py")
    print("  3. Open browser: http://localhost:8000")
    print("=" * 70)


if __name__ == "__main__":
    main()
