#!/usr/bin/env python3
"""
Generate ProductReps insight cards from podcast analysis JSON files.
Updated to support 15-20 insights per episode with category classification.

Usage:
  python generate_productreps_data.py              # Without AI judgment (fast)
  python generate_productreps_data.py --with-ai    # With AI judgment (requires ANTHROPIC_API_KEY)
  
Environment:
  ANTHROPIC_API_KEY - Required for --with-ai mode
"""

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Check if AI generation is requested
GENERATE_AI_JUDGMENTS = "--with-ai" in sys.argv

if GENERATE_AI_JUDGMENTS:
    try:
        import anthropic
        client = anthropic.Anthropic()
        print("✓ Anthropic client initialized - AI judgments will be generated")
    except Exception as e:
        print(f"✗ Could not initialize Anthropic client: {e}")
        print("  Set ANTHROPIC_API_KEY environment variable or run without --with-ai")
        GENERATE_AI_JUDGMENTS = False
else:
    print("ℹ Running without AI judgment generation (use --with-ai to enable)")

TRANSCRIPTS_DIR = Path("transcripts")
OUTPUT_FILE = Path("productreps_insights.json")

# Valid categories
VALID_CATEGORIES = [
    "learn_from_legends",
    "build_ai_products", 
    "speak_ai_fluently",
    "ai_superpowers"
]


def extract_metadata_from_analysis(data: dict, filename: str) -> dict:
    """
    Extract episode metadata from analysis JSON.
    Supports both old format (inferred from filename) and new format (episode_metadata).
    """
    
    # Check for new format with episode_metadata
    if "episode_metadata" in data:
        meta = data["episode_metadata"]
        return {
            "podcast": meta.get("podcast", "Unknown Podcast"),
            "episode": meta.get("episode", "Unknown Episode"),
            "guest": meta.get("guest", "Unknown Guest"),
            "category": meta.get("primary_category", "learn_from_legends")
        }
    
    # Fallback: Extract from filename (old format)
    name = filename.replace("_analysis_hybrid.json", "")
    
    # Common patterns: "Title _ Guest Name" or "Guest Name _ Title"
    if " _ " in name:
        parts = name.split(" _ ")
        if len(parts) >= 2:
            title_part = parts[0].strip()
            guest_part = parts[-1].strip()
            guest_clean = guest_part.split("(")[0].strip()
            
            return {
                "podcast": "Lenny's Podcast",  # Default for old files
                "episode": title_part,
                "guest": guest_clean,
                "category": "learn_from_legends"
            }
    
    return {
        "podcast": "Unknown Podcast",
        "episode": name,
        "guest": "Unknown Guest",
        "category": "learn_from_legends"
    }


def generate_judgment_scenario(insight: dict, guest: str, context: str) -> dict:
    """Use Claude to generate a judgment scenario from an insight."""
    
    if not GENERATE_AI_JUDGMENTS:
        return None
    
    prompt = f"""Based on this product insight, create a judgment training scenario for product managers.

INSIGHT: {insight.get('insight', '')}
WHY VALUABLE: {insight.get('why_valuable', '')}
GUEST: {guest}
CONTEXT: {context}

Create a scenario where a product manager must make a decision. The scenario should:
1. Present a realistic product decision situation
2. Have two clear options (A and B)
3. One option should align with the insight (the "correct" one)
4. Include reasoning that references the original insight

Respond in this exact JSON format:
{{
    "scenario": "You are a PM at [company type]. [Situation description]. What do you do?",
    "optionA": "[First option - concise, 1-2 sentences]",
    "optionB": "[Second option - concise, 1-2 sentences]", 
    "correctOption": "A" or "B",
    "reasoning": "[2-3 sentences explaining why this option is better, referencing the insight from {guest}]"
}}

Only respond with valid JSON, no other text."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = json.loads(response.content[0].text)
        return result
    except Exception as e:
        print(f"    Warning: Could not generate judgment scenario: {e}")
        return None


def obviousness_to_spicy(level: str) -> int:
    """Convert obviousness level to spicy rating."""
    mapping = {
        "truly_non_obvious": 5,
        "moderately_non_obvious": 3,
        "best_available": 1
    }
    return mapping.get(level, 2)


def process_analysis_file(filepath: Path) -> list[dict]:
    """
    Process a single analysis JSON file and extract insights.
    Supports both old format (top_5_takeaways) and new format (insights).
    """
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Extract metadata
    metadata = extract_metadata_from_analysis(data, filepath.name)
    guest = metadata["guest"]
    episode_title = metadata["episode"]
    podcast = metadata["podcast"]
    primary_category = metadata["category"]
    
    print(f"Processing: {guest} - {episode_title[:40]}...")
    print(f"  Podcast: {podcast}")
    print(f"  Category: {primary_category}")
    
    insights = []
    
    # Get episode-level metadata
    scores = data.get("scores", {})
    verdict = data.get("verdict", {})
    characteristics = data.get("characteristics", [])
    summary = data.get("summary", "")
    
    # Support both old and new formats
    # New format: "insights" array with 15-20 items
    # Old format: "top_5_takeaways" array with 5 items
    takeaways = data.get("insights", data.get("top_5_takeaways", []))
    
    print(f"  Found {len(takeaways)} insights")
    
    for i, takeaway in enumerate(takeaways):
        # Get category for this insight (new format) or use episode-level (old format)
        insight_category = takeaway.get("category", primary_category)
        if insight_category not in VALID_CATEGORIES:
            insight_category = primary_category
        
        # Get spicy rating (new format has it directly, old format derives from obviousness)
        spicy_rating = takeaway.get("spicy_rating", 
            obviousness_to_spicy(takeaway.get("obviousness_level", "moderately_non_obvious")))
        
        insight_card = {
            "id": str(uuid.uuid4()),
            "podcastTitle": podcast,
            "episodeTitle": episode_title,
            "guest": guest,
            "insight": takeaway.get("insight", ""),
            "timestamp": takeaway.get("timestamp", ""),
            "whyValuable": takeaway.get("why_valuable", ""),
            "obviousnessLevel": takeaway.get("obviousness_level", "moderately_non_obvious"),
            "spicyRating": spicy_rating,
            "rank": takeaway.get("rank", i + 1),
            
            # Category classification
            "category": insight_category,
            "podcastSourceId": podcast,
            
            # Rich metadata
            "sourceFile": filepath.name,
            "characteristics": characteristics,
            "scores": {
                "freshness": scores.get("freshness", 5),
                "insightDensity": scores.get("insight_density", 5),
                "contrarian": scores.get("contrarian_index", 5),
                "actionability": scores.get("actionability", 5)
            },
            "verdict": {
                "bestQuote": verdict.get("best_quote", ""),
                "bestFor": verdict.get("best_for", ""),
                "skipIf": verdict.get("skip_if", ""),
                "tldr": verdict.get("tldr", "")
            },
            
            # Actionability from new format
            "actionabilityType": takeaway.get("actionability", "strategic"),
            
            # Judgment scenario (will be filled by AI if enabled)
            "judgment": None,
            
            # Metadata
            "createdAt": datetime.now().isoformat(),
            "isPinned": False,
            "isSaved": False
        }
        
        # Generate judgment scenario for top-ranked insights only
        if GENERATE_AI_JUDGMENTS and takeaway.get("rank", i + 1) <= 5:
            print(f"    Generating judgment for insight {i+1}...")
            judgment = generate_judgment_scenario(takeaway, guest, summary)
            if judgment:
                insight_card["judgment"] = judgment
        
        insights.append(insight_card)
    
    return insights


def main():
    """Main function to process all analysis files."""
    
    print("=" * 60)
    print("ProductReps Insight Generator v2")
    print("Supports 15-20 insights per episode with categories")
    print("=" * 60)
    
    # Find all analysis files
    analysis_files = list(TRANSCRIPTS_DIR.glob("*_analysis_hybrid.json"))
    print(f"\nFound {len(analysis_files)} analysis files\n")
    
    all_insights = []
    
    for filepath in sorted(analysis_files):
        try:
            insights = process_analysis_file(filepath)
            all_insights.extend(insights)
            print(f"  ✓ Added {len(insights)} insights\n")
        except Exception as e:
            print(f"  ✗ Error processing {filepath.name}: {e}\n")
            import traceback
            traceback.print_exc()
    
    # Collect unique values for metadata
    all_categories = list(set(i.get("category", "learn_from_legends") for i in all_insights))
    all_characteristics = list(set(
        char for insight in all_insights 
        for char in insight.get("characteristics", [])
    ))
    all_guests = list(set(i["guest"] for i in all_insights))
    all_podcasts = list(set(i["podcastTitle"] for i in all_insights))
    
    # Create output structure
    output = {
        "version": "2.0",
        "generatedAt": datetime.now().isoformat(),
        "totalInsights": len(all_insights),
        "insights": all_insights,
        "metadata": {
            "sources": len(analysis_files),
            "categories": all_categories,
            "characteristics": all_characteristics,
            "guests": all_guests,
            "podcasts": all_podcasts
        }
    }
    
    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("=" * 60)
    print(f"✓ Generated {len(all_insights)} insight cards from {len(analysis_files)} episodes")
    print(f"✓ Saved to {OUTPUT_FILE}")
    print("=" * 60)
    
    # Print category breakdown
    print("\n📁 CATEGORY BREAKDOWN:")
    category_counts = {}
    for insight in all_insights:
        cat = insight.get("category", "learn_from_legends")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    category_icons = {
        "learn_from_legends": "🏆",
        "build_ai_products": "🤖",
        "speak_ai_fluently": "🧠",
        "ai_superpowers": "⚡"
    }
    
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        icon = category_icons.get(cat, "📚")
        print(f"  {icon} {cat}: {count} insights")
    
    # Print podcast breakdown
    print("\n🎙️ PODCAST BREAKDOWN:")
    podcast_counts = {}
    for insight in all_insights:
        pod = insight.get("podcastTitle", "Unknown")
        podcast_counts[pod] = podcast_counts.get(pod, 0) + 1
    
    for pod, count in sorted(podcast_counts.items(), key=lambda x: -x[1]):
        print(f"  • {pod}: {count} insights")
    
    # Print spicy ratings
    print("\n🔥 SPICY RATINGS:")
    for rating in [5, 4, 3, 2, 1]:
        count = sum(1 for i in all_insights if i.get("spicyRating", 0) == rating)
        if count > 0:
            emoji = "🔥" * rating
            print(f"  {emoji}: {count} insights")
    
    # Judgment scenarios
    with_judgment = sum(1 for i in all_insights if i.get("judgment"))
    print(f"\n🎯 JUDGMENT SCENARIOS: {with_judgment}/{len(all_insights)} insights")
    
    print("\n✅ Done! Copy productreps_insights.json to your Xcode project Resources folder.")


if __name__ == "__main__":
    main()
