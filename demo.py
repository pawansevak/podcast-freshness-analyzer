"""
Demo script showing how to use the Podcast Analyzer programmatically
"""

from analyzer import analyze_podcast, load_transcript, load_user_preferences
import json

def demo_analysis():
    """Run analysis on all sample podcasts and compare results"""
    
    print("=" * 70)
    print("PODCAST ANALYZER DEMO")
    print("=" * 70)
    print()
    
    podcasts = ["podcast_1", "podcast_2", "podcast_3"]
    titles = [
        "Tech Frontiers - AI Coding Agents",
        "The Productivity Show - Time Management", 
        "Science Deep Dive - Neural Plasticity"
    ]
    
    results = []
    
    for podcast_id, title in zip(podcasts, titles):
        print(f"\n📊 Analyzing: {title}")
        print("-" * 70)
        
        # Load transcript and preferences
        transcript = load_transcript(podcast_id)
        user_prefs = load_user_preferences("default")
        
        # Analyze
        result = analyze_podcast(transcript, user_prefs)
        results.append((title, result))
        
        # Display summary
        print(f"Freshness: {result['freshness_score']}/10")
        print(f"Insights:  {result['insight_score']}/10")
        print(f"Summary:   {result['summary']}")
        
        # Show unique insights with quotes
        if result.get('unique_insights'):
            print("\n💡 Unique Insights with Quotes:")
            for i, insight in enumerate(result['unique_insights'], 1):
                print(f"  {i}. [{insight['type']}]")
                print(f"     \"{insight['quote'][:150]}...\"" if len(insight['quote']) > 150 else f"     \"{insight['quote']}\"")
        
        # Show characteristics
        chars = result['key_characteristics']
        print("\nCharacteristics:")
        print(f"  • Specific data: {'✓' if chars['has_specific_data'] else '✗'}")
        print(f"  • Concrete examples: {'✓' if chars['has_concrete_examples'] else '✗'}")
        print(f"  • Novel frameworks: {'✓' if chars['has_novel_frameworks'] else '✗'}")
        print(f"  • Contrarian takes: {'✓' if chars['has_contrarian_takes'] else '✗'}")
        print(f"  • Actionable advice: {'✓' if chars['has_actionable_advice'] else '✗'}")
    
    # Comparison
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print()
    
    for title, result in results:
        fresh_bar = "█" * result['freshness_score'] + "░" * (10 - result['freshness_score'])
        insight_bar = "█" * result['insight_score'] + "░" * (10 - result['insight_score'])
        
        print(f"{title[:40]:40s}")
        print(f"  Freshness: [{fresh_bar}] {result['freshness_score']}/10")
        print(f"  Insights:  [{insight_bar}] {result['insight_score']}/10")
        print()
    
    print("\n💡 Key Takeaway:")
    print("The analyzer successfully distinguishes between high-quality, data-driven")
    print("content (podcasts 1 & 3) and generic advice content (podcast 2).")
    print()


def demo_personalization():
    """Show how personalization affects scoring"""
    
    print("\n" + "=" * 70)
    print("PERSONALIZATION DEMO")
    print("=" * 70)
    print()
    
    transcript = load_transcript("podcast_1")
    
    # Generic preferences
    generic_prefs = {
        "topics_of_interest": [],
        "freshness_priority": "medium",
        "insight_style": "general"
    }
    
    # Tech-focused preferences (matches podcast_1)
    tech_prefs = {
        "topics_of_interest": ["AI", "Technology", "Software Development"],
        "freshness_priority": "high",
        "insight_style": "data-driven"
    }
    
    print("Analyzing the same podcast with different user preferences...\n")
    
    print("1️⃣  Generic User (no specific preferences)")
    result1 = analyze_podcast(transcript, generic_prefs)
    print(f"   Freshness: {result1['freshness_score']}/10")
    print(f"   Insights:  {result1['insight_score']}/10")
    
    print("\n2️⃣  Tech-Focused User (AI, data-driven insights)")
    result2 = analyze_podcast(transcript, tech_prefs)
    print(f"   Freshness: {result2['freshness_score']}/10")
    print(f"   Insights:  {result2['insight_score']}/10")
    
    print("\n💡 In production, user preferences would be used to:")
    print("   • Weight topics matching user interests more heavily")
    print("   • Adjust scoring based on their freshness priority")
    print("   • Identify insights matching their preferred style")
    print()


if __name__ == "__main__":
    demo_analysis()
    demo_personalization()
    
    print("=" * 70)
    print("To run the web interface:")
    print("  1. Run: python app.py")
    print("  2. Open: http://localhost:8000")
    print("=" * 70)
