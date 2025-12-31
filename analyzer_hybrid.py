"""
ProductReps Podcast Analyzer - Extracts 15-20 actionable insights from podcast transcripts
Updated to support metadata headers and category classification

Now uses OpenAI GPT-4 and loads API key from .env file
"""

import json
import os
import re
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

load_env()

# Initialize OpenAI client
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except ImportError:
    print("❌ OpenAI library not installed. Run: pip3 install openai")
    raise

# Valid categories for ProductReps app
VALID_CATEGORIES = [
    "learn_from_legends",  # Product craft, strategy, career wisdom
    "build_ai_products",   # Building AI features, AI product management
    "speak_ai_fluently",   # Understanding AI/ML technology
    "ai_superpowers"       # Using AI tools to work better
]

ANALYSIS_PROMPT = """You are an EXTREMELY CRITICAL expert podcast analyst for "ProductReps" - an app that helps product managers train their product sense with high-quality insights.

**EPISODE METADATA:**
- Podcast: {podcast_name}
- Episode: {episode_title}
- Guest: {guest_name}
- Category: {category}

**CRITICAL CONTEXT:**
You are evaluating for experienced Principal Product Managers and senior leaders who have heard HUNDREDS of podcasts. Your standards are VERY high. Most podcasts recycle the same advice. Extract ONLY insights that would surprise experienced professionals.

---

## PART 1: MULTI-DIMENSIONAL SCORING (BE HARSH)

### CRITICAL SCORING RULES:
- Use the FULL 1-10 scale. Most podcasts ARE mediocre (5-6 range)
- Only truly exceptional content gets 9-10 (think top 5% of all podcasts ever)
- BE HARSH. If you're unsure, round DOWN
- Assume the listener has heard common PM/startup advice 100+ times

---

### 1. INSIGHT DENSITY (40% weight) - "Non-obvious insights per minute"

TRULY NON-OBVIOUS insights (8-10):
- Would genuinely SURPRISE an experienced product/engineering leader
- Backed by SPECIFIC numbers, data, or concrete examples
- DIRECTLY contradicts what most people believe
- Passes: "An expert in this field would say 'I never thought of it that way'"

OBVIOUS insights (1-3) - DO NOT REWARD:
- Iteration over perfection, speed matters
- Talk to users, find PMF
- AI needs eval frameworks
- Generic startup wisdom everyone knows

**Scoring:** 10 = Mind-blowing every few minutes | 5 = Mix of decent and obvious | 1 = Pure platitudes

### 2. SIGNAL-TO-NOISE (20% weight)
10 = Every sentence adds value | 5 = 50/50 | 1 = 90% filler

### 3. ACTIONABILITY (20% weight) - "Can I use this Monday?"
10 = Step-by-step playbook | 5 = Directionally helpful | 1 = Pure theory

### 4. CONTRARIAN INDEX (10% weight)
10 = Genuinely controversial with evidence | 5 = Mildly spicy | 1 = Consensus opinion

### 5. FRESHNESS (5% weight)
10 = Cutting edge, will age in months | 5 = Could be 1-2 years old | 1 = Timeless generic advice

### 6. HOST QUALITY (5% weight)
10 = Masterful interviewer | 5 = Competent | 1 = Makes it worse

---

## PART 2: EXTRACT 15-20 INSIGHTS (TIERED)

Extract 15-20 insights that pass the quality bar. Capture ALL genuinely valuable moments.

**TIERED EXTRACTION:**

TIER 1 (Rank 1-5): "Mind-blowing" - Would surprise a 10+ year PM veteran
- Specific data, numbers, counterintuitive findings
- Makes someone stop and reconsider assumptions

TIER 2 (Rank 6-10): "Sharp" - High-quality tactical insights  
- Specific frameworks, processes, techniques
- Enough detail to replicate

TIER 3 (Rank 11-15): "Useful" - Solid insights worth capturing
- Good examples or case studies
- Fresh angles on familiar concepts

TIER 4 (Rank 16-20): "Foundational" - Best remaining insights
- Context-setting information
- Good quotes or memorable framings

**INSIGHT MINING - Look for these HIGH-SIGNAL patterns:**

Numbers & Specifics:
- "We went from X to Y" → Capture the transformation
- "It took us N months" → Capture the timeline
- "N% of our users..." → Capture the metric

Contrarian Signals:
- "Most people think X, but actually Y"
- "The counterintuitive thing is..."
- "What surprised us was..."

Framework Reveals:
- "We use a framework called..."
- "Our process is..."
- "The way we think about it..."

Origin Stories:
- "The real reason we did X was..."
- "What nobody knows is..."
- "Behind the scenes..."

Failure Lessons:
- "We tried X and it failed because..."
- "Our biggest mistake was..."
- "If I could go back..."

**EXTRACTION RULES:**
1. Extract 15-20 insights (aim for 18)
2. If insight-dense episode, go up to 25
3. If mediocre episode, minimum 12
4. Capture specific numbers, percentages, timeframes
5. Include speaker's exact framing when memorable
6. Timestamp every insight (format: "MM:SS")

**REJECTION CRITERIA - DO NOT include:**
- Generic startup advice (iterate fast, talk to users, find PMF)
- Obvious career advice (be curious, work hard)
- Standard frameworks without novel application
- Anything you've heard in 5+ other podcasts

**CATEGORY ASSIGNMENT:**
Assign each insight to one of these ProductReps categories:
- "learn_from_legends" - Product craft, strategy, career wisdom, leadership
- "build_ai_products" - Building AI features, AI product management, AI UX
- "speak_ai_fluently" - Understanding AI/ML technology, LLMs, technical concepts
- "ai_superpowers" - Using AI tools to work better, AI productivity, prompting

If the insight doesn't clearly fit AI categories, use "learn_from_legends".

---

## OUTPUT FORMAT (JSON):

{{
  "episode_metadata": {{
    "podcast": "{podcast_name}",
    "episode": "{episode_title}",
    "guest": "{guest_name}",
    "primary_category": "{category}"
  }},
  "scores": {{
    "insight_density": <1-10>,
    "signal_to_noise": <1-10>,
    "actionability": <1-10>,
    "contrarian_index": <1-10>,
    "freshness": <1-10>,
    "host_quality": <1-10>,
    "overall": <weighted average, 1 decimal>
  }},
  "verdict": {{
    "tldr": "<One brutal sentence: Is this worth your time?>",
    "best_for": "<Who should listen? Be SPECIFIC>",
    "skip_if": "<Who should avoid?>",
    "worth_it": <true/false>,
    "best_quote": "<One genuinely useful quote>"
  }},
  "insights": [
    {{
      "rank": 1,
      "insight": "Most non-obvious insight with specific details",
      "timestamp": "15:30",
      "why_valuable": "Why this surprises experienced professionals",
      "obviousness_level": "truly_non_obvious",
      "category": "build_ai_products",
      "spicy_rating": 5,
      "actionability": "immediate"
    }},
    {{
      "rank": 2,
      "insight": "Second insight...",
      "timestamp": "23:45",
      "why_valuable": "Why this matters",
      "obviousness_level": "truly_non_obvious",
      "category": "learn_from_legends",
      "spicy_rating": 4,
      "actionability": "strategic"
    }}
    // ... continue for 15-20 insights total
  ],
  "why_these_scores": {{
    "insight_density": "<Why this score?>",
    "signal_to_noise": "<Why this score?>",
    "actionability": "<Why this score?>",
    "contrarian_index": "<Why this score?>",
    "freshness": "<Why this score?>",
    "host_quality": "<Why this score?>"
  }},
  "summary": "<2-3 sentence overview>",
  "characteristics": ["<tag1>", "<tag2>", "<tag3>", "<tag4>", "<tag5>"],
  "obvious_insights_rejected": [
    "<Insight rejected as too common - explain why>"
  ]
}}

---

## TRANSCRIPT TO ANALYZE:

{transcript}

---

## FINAL REMINDERS:

- BE BRUTALLY HARSH with scoring
- Extract 15-20 insights, not just 5
- Assign a category to EACH insight
- Include spicy_rating (1-5) for each insight
- Most podcasts score 4-6 overall
- Return ONLY valid JSON, no other text
"""


def parse_transcript_header(content: str) -> Tuple[Dict[str, str], str]:
    """
    Extract metadata header from transcript file.
    
    Header format:
    ---
    podcast: Lenny's Podcast
    episode: Building Products Users Love
    guest: Shreyas Doshi
    category: learn_from_legends
    date: 2024-01-15
    ---
    
    [Transcript content...]
    
    Returns:
        Tuple of (metadata dict, transcript text)
    """
    content = content.strip()
    
    if not content.startswith('---'):
        return {}, content
    
    # Find the closing ---
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', content, re.DOTALL)
    
    if not match:
        return {}, content
    
    header_text = match.group(1)
    transcript = match.group(2).strip()
    
    # Parse YAML-like header
    metadata = {}
    for line in header_text.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip().lower()] = value.strip()
    
    return metadata, transcript


def infer_metadata_from_filename(filepath: str) -> Dict[str, str]:
    """
    Attempt to infer metadata from filename if no header present.
    
    Expected format: podcast_guest_episode.txt
    Example: lennys_podcast_shreyas_doshi_building_products.txt
    """
    filename = os.path.basename(filepath)
    name = filename.rsplit('.', 1)[0]  # Remove extension
    
    # Remove common suffixes
    for suffix in ['_analysis_hybrid', '_analysis', '_transcript']:
        name = name.replace(suffix, '')
    
    parts = name.split('_')
    
    # Best effort parsing
    metadata = {
        'podcast': 'Unknown Podcast',
        'guest': 'Unknown Guest',
        'episode': 'Unknown Episode',
        'category': 'learn_from_legends'  # Default
    }
    
    if len(parts) >= 2:
        # Assume first part(s) are podcast, last part(s) are guest
        metadata['podcast'] = ' '.join(parts[:2]).title().replace('_', ' ')
        metadata['guest'] = ' '.join(parts[2:4]).title().replace('_', ' ') if len(parts) > 2 else 'Unknown Guest'
        metadata['episode'] = ' '.join(parts[4:]).title().replace('_', ' ') if len(parts) > 4 else metadata['guest']
    
    return metadata


def calculate_overall_score(scores: Dict[str, float]) -> float:
    """
    Calculate weighted overall score based on the 6 dimensions.
    """
    weights = {
        'insight_density': 0.40,
        'signal_to_noise': 0.20,
        'actionability': 0.20,
        'contrarian_index': 0.10,
        'freshness': 0.05,
        'host_quality': 0.05
    }
    
    overall = sum(scores.get(dim, 5) * weights[dim] for dim in weights.keys())
    return round(overall, 1)


def analyze_podcast(
    transcript: str, 
    metadata: Optional[Dict[str, str]] = None,
    model: str = "gpt-4o"
) -> Dict[str, Any]:
    """
    Analyze a podcast transcript with hybrid critical multi-dimensional scoring.
    
    Args:
        transcript: The podcast transcript text
        metadata: Optional dict with podcast, episode, guest, category
        model: OpenAI model to use (default: gpt-4o)
        
    Returns:
        Dictionary with scores, verdict, insights (15-20), and reasoning
    """
    
    # Use provided metadata or defaults
    if metadata is None:
        metadata = {}
    
    podcast_name = metadata.get('podcast', 'Unknown Podcast')
    episode_title = metadata.get('episode', 'Unknown Episode')
    guest_name = metadata.get('guest', 'Unknown Guest')
    category = metadata.get('category', 'learn_from_legends')
    
    # Validate category
    if category not in VALID_CATEGORIES:
        category = 'learn_from_legends'
    
    prompt = ANALYSIS_PROMPT.format(
        podcast_name=podcast_name,
        episode_title=episode_title,
        guest_name=guest_name,
        category=category,
        transcript=transcript
    )
    
    print(f"🎯 Analyzing: {podcast_name} - {guest_name}")
    print(f"   Episode: {episode_title}")
    print(f"   Category: {category}")
    print(f"   Model: {model}")
    print("   Extracting 15-20 insights...")
    
    response = client.chat.completions.create(
        model=model,
        max_tokens=8000,
        temperature=0.3,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = response.choices[0].message.content
    
    # Handle markdown code blocks if present
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
    
    try:
        result = json.loads(response_text)
        
        # Verify and recalculate overall score
        if 'scores' in result:
            scores = result['scores']
            calculated_overall = calculate_overall_score(scores)
            result['scores']['overall'] = calculated_overall
        
        # Ensure episode metadata is included
        if 'episode_metadata' not in result:
            result['episode_metadata'] = {
                'podcast': podcast_name,
                'episode': episode_title,
                'guest': guest_name,
                'primary_category': category
            }
        
        # Add processing metadata
        result['analyzed_at'] = datetime.now().isoformat()
        result['model'] = model
        result['provider'] = 'openai'
        result['scoring_mode'] = 'hybrid_critical_v2'
        
        # Count insights
        insight_count = len(result.get('insights', []))
        print(f"   ✓ Extracted {insight_count} insights")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        print(f"Raw response (first 1000 chars): {response_text[:1000]}")
        raise


def analyze_and_save(transcript_path: str, output_path: str = None) -> Dict[str, Any]:
    """
    Analyze a transcript file and save results to JSON.
    
    Supports metadata header in transcript file:
    ---
    podcast: Lenny's Podcast
    episode: Building Products
    guest: Shreyas Doshi
    category: learn_from_legends
    ---
    [transcript content]
    
    Args:
        transcript_path: Path to transcript text file
        output_path: Optional path to save results
        
    Returns:
        Analysis result dictionary
    """
    
    print(f"\n📄 Reading: {transcript_path}")
    
    # Read file
    with open(transcript_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse metadata header
    metadata, transcript = parse_transcript_header(content)
    
    # If no header, try to infer from filename
    if not metadata:
        print("   ⚠️  No metadata header found, inferring from filename...")
        metadata = infer_metadata_from_filename(transcript_path)
        transcript = content  # Use full content as transcript
    else:
        print(f"   ✓ Found metadata: {metadata.get('guest', 'Unknown')} on {metadata.get('podcast', 'Unknown')}")
    
    # Analyze
    result = analyze_podcast(transcript, metadata)
    
    # Determine output path
    if output_path is None:
        output_path = transcript_path.rsplit('.', 1)[0] + '_analysis_hybrid.json'
    
    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    # Print summary
    print(f"\n✅ Analysis saved to: {output_path}")
    print(f"\n{'='*50}")
    print(f"📊 SCORES:")
    print(f"   Overall: {result['scores']['overall']}/10")
    print(f"   Insight Density: {result['scores']['insight_density']}/10")
    print(f"   Signal-to-Noise: {result['scores']['signal_to_noise']}/10")
    print(f"   Actionability: {result['scores']['actionability']}/10")
    print(f"   Contrarian: {result['scores']['contrarian_index']}/10")
    print(f"   Freshness: {result['scores']['freshness']}/10")
    
    print(f"\n💡 VERDICT: {result['verdict']['tldr']}")
    print(f"   Worth it? {'✅ Yes' if result['verdict']['worth_it'] else '❌ No'}")
    
    insights = result.get('insights', [])
    print(f"\n🎯 TOP 3 INSIGHTS (of {len(insights)} total):")
    for insight in insights[:3]:
        print(f"   {insight['rank']}. [{insight.get('category', 'unknown')}] {insight['insight'][:80]}...")
    
    # Category breakdown
    categories = {}
    for insight in insights:
        cat = insight.get('category', 'learn_from_legends')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📁 CATEGORY BREAKDOWN:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count} insights")
    
    print(f"{'='*50}\n")
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
ProductReps Podcast Analyzer
============================

Usage: python analyzer_hybrid.py <transcript_file.txt>

The transcript file can optionally include a metadata header:

---
podcast: Lenny's Podcast
episode: Building Products Users Love
guest: Shreyas Doshi
category: learn_from_legends
date: 2024-01-15
---

[Paste transcript content here]

Categories:
- learn_from_legends: Product craft, strategy, career wisdom
- build_ai_products: Building AI features, AI product management
- speak_ai_fluently: Understanding AI/ML technology
- ai_superpowers: Using AI tools to work better
        """)
        sys.exit(1)
    
    analyze_and_save(sys.argv[1])
