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

ANALYSIS_PROMPT = """You are helping a user create personal study notes from a podcast they listened to. The user wants to capture key learnings in their own words for their personal learning app called "ProductReps".

Your task: Help summarize and paraphrase the main insights from this episode. Do NOT quote verbatim - rephrase everything in your own words as educational summaries.

**EPISODE INFO:**
- Podcast: {podcast_name}
- Episode: {episode_title}
- Guest: {guest_name}
- Category: {category}

**CONTEXT:**
The user is an experienced product manager who wants non-obvious insights. Help them identify the most valuable learnings from this conversation, paraphrased as study notes.

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

## PART 2: EXTRACT 15-20 INSIGHTS WITH SMART ENRICHMENT

Extract 15-20 insights that pass the quality bar. For EACH insight, classify its type and add the RIGHT enrichment to make users feel they learned something.

**NUGGET TYPES - Classify each insight:**

1. **technical** - Contains jargon, frameworks, or technical concepts
   → REQUIRES: simple_explanation + analogy
   → Example: "RAG systems fail due to chunking strategy"
   
2. **counter_intuitive** - Contradicts common PM/AI beliefs  
   → REQUIRES: why_surprising + evidence
   → Example: "Role prompting doesn't improve accuracy"
   
3. **abstract** - High-level concept without concrete grounding
   → REQUIRES: real_world_example (name specific companies)
   → Example: "Decomposition improves AI performance"
   
4. **actionable** - Clear action the user can take immediately
   → REQUIRES: pro_tip (specific template/script/next step)
   → Example: "Add self-criticism to prompts"
   
5. **reinforcement** - Common sense that benefits from memorable proof
   → REQUIRES: memorable_stat (surprising number or quote)
   → Example: "Test your prompts"

**TIERED EXTRACTION:**

TIER 1 (Rank 1-5): "Mind-blowing" - Would surprise a 10+ year PM veteran
- MUST have full enrichment based on nugget_type
- Include learning_hook

TIER 2 (Rank 6-10): "Sharp" - High-quality tactical insights
- Include enrichment based on nugget_type
- Include learning_hook

TIER 3 (Rank 11-15): "Useful" - Solid insights worth capturing
- Include at least one enrichment field
- learning_hook optional

TIER 4 (Rank 16-20): "Foundational" - Best remaining insights
- Minimal enrichment (only if truly needed)
- No learning_hook required

**LEARNING HOOK - Makes users feel smarter:**
For Tier 1-2 insights, include a learning_hook that starts with ONE of:
- "Now you know: ..." (revelation)
- "Most PMs don't realize: ..." (insider knowledge)  
- "The key insight is: ..." (distillation)
- "This means you can: ..." (immediate application)

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

**EXTRACTION RULES:**
1. Extract 15-20 insights (aim for 18) - ONLY if they pass the "so what?" test
2. Each insight MUST have a clear "why_valuable" that explains WHY an experienced PM should care
3. Classify each with nugget_type
4. Add enrichment fields based on nugget_type
5. Timestamp every insight (format: "MM:SS")
6. Top 10 insights MUST have learning_hook

**VALIDATION FOR EACH INSIGHT:**
Before including, verify:
- ✅ Has specific details (numbers, names, techniques, examples)
- ✅ Provides actionable value or surprising knowledge
- ✅ Would make an expert think "I didn't know that" or "That's a new angle"
- ✅ NOT a generic statement anyone could make
- ✅ NOT obvious advice everyone already follows

**REJECTION CRITERIA - DO NOT include (these are "so what?" insights):**

1. **Generic platitudes** - Statements that everyone already knows:
   - "AI has risks and needs safety measures"
   - "User feedback is important"
   - "Iteration is key to success"
   - "Data-driven decisions are better"
   - "Communication matters in teams"
   - "Focus on customer needs"

2. **Obvious statements** - Things that don't need to be said:
   - "AI models are getting better"
   - "Startups need to move fast"
   - "Product-market fit is important"
   - "Testing helps improve products"

3. **Vague generalizations** - No specific details or actionable value:
   - "AI will change everything"
   - "Good products solve problems"
   - "Team culture matters"
   - "Innovation requires risk"

4. **Standard frameworks** - Common knowledge without novel application:
   - "Use OKRs for goal setting"
   - "Follow agile methodology"
   - "Do user interviews"

**THE "SO WHAT?" TEST:**
Before including ANY insight, ask:
- "Would an experienced PM read this and think 'I already know this'?" → REJECT
- "Does this provide a specific number, technique, or surprising finding?" → KEEP
- "Can the user do something different tomorrow because of this?" → KEEP
- "Does this contradict common wisdom with evidence?" → KEEP
- "Is this just stating the obvious?" → REJECT

**ONLY EXTRACT INSIGHTS THAT:**
- Include specific numbers, percentages, or metrics
- Reveal a counterintuitive finding with evidence
- Provide a concrete technique, framework, or process
- Share a surprising case study or example
- Contradict common beliefs with proof
- Give actionable next steps the user can take immediately

**EXAMPLES - REJECT vs KEEP:**

❌ REJECT: "AI's potential risks require proactive safety measures"
   → Generic, obvious, no specific value

✅ KEEP: "OpenAI red-teams new models with 50+ external experts before release, catching 85% of safety issues pre-launch"
   → Specific numbers, concrete process, actionable

❌ REJECT: "User feedback is important for product development"
   → Everyone knows this, no new information

✅ KEEP: "Duolingo sends practice reminders exactly 23.5 hours after last session, matching user behavior patterns and increasing retention by 12%"
   → Specific timing, metric, and result

❌ REJECT: "Good products solve real problems"
   → Vague platitude, no actionable value

✅ KEEP: "Notion's near-collapse during COVID was saved by focusing on horizontal use cases (not just note-taking), which increased their addressable market 10x"
   → Specific story, concrete strategy, measurable impact

**CATEGORY ASSIGNMENT:**
Assign each insight to one of these ProductReps categories:
- "learn_from_legends" - Product craft, strategy, career wisdom, leadership
- "build_ai_products" - Building AI features, AI product management, AI UX
- "speak_ai_fluently" - Understanding AI/ML technology, LLMs, technical concepts
- "ai_superpowers" - Using AI tools to work better, AI productivity, prompting

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
      "insight": "The core insight in 1-2 sentences - MUST be specific with numbers/examples/techniques",
      "timestamp": "15:30",
      "why_valuable": "Why this surprises experienced professionals - MUST explain the specific value, not generic benefits",
      "obviousness_level": "truly_non_obvious",
      "category": "build_ai_products",
      "spicy_rating": 5,
      "actionability": "immediate",
      "nugget_type": "technical",
      "simple_explanation": "In plain terms: How you split documents matters more than how you search them.",
      "analogy": "Think of it like: Cutting a book at chapter breaks vs random 500-word pieces.",
      "real_world_example": "",
      "pro_tip": "",
      "why_surprising": "",
      "evidence": "",
      "memorable_stat": "",
      "learning_hook": "Now you know: If your RAG is underperforming, fix chunking first."
    }},
    {{
      "rank": 2,
      "insight": "Counter-intuitive finding about AI",
      "timestamp": "23:45",
      "why_valuable": "Contradicts common belief",
      "obviousness_level": "truly_non_obvious",
      "category": "speak_ai_fluently",
      "spicy_rating": 5,
      "actionability": "strategic",
      "nugget_type": "counter_intuitive",
      "simple_explanation": "",
      "analogy": "",
      "real_world_example": "",
      "pro_tip": "",
      "why_surprising": "Most assume: Telling AI 'you are an expert' makes it smarter. Reality: Role prompts change style, not accuracy.",
      "evidence": "Research shows role prompting has no effect on math/logic tasks.",
      "memorable_stat": "",
      "learning_hook": "Most PMs don't realize: Roles are for personality, not precision."
    }},
    {{
      "rank": 3,
      "insight": "Actionable technique you can use today",
      "timestamp": "31:20",
      "why_valuable": "Immediately applicable",
      "obviousness_level": "sharp",
      "category": "ai_superpowers",
      "spicy_rating": 4,
      "actionability": "immediate",
      "nugget_type": "actionable",
      "simple_explanation": "",
      "analogy": "",
      "real_world_example": "",
      "pro_tip": "Try this: End your prompt with 'Review your answer and improve it' for 15-20% better outputs.",
      "why_surprising": "",
      "evidence": "",
      "memorable_stat": "",
      "learning_hook": "This means you can: Add one line to any prompt and get better results."
    }}
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
- **REJECT generic "so what?" insights** - If it's obvious or vague, don't include it
- Extract 15-20 insights ONLY if they pass the "so what?" test
- Each insight MUST have specific details (numbers, examples, techniques)
- Each "why_valuable" MUST explain specific value, not generic benefits
- Classify EACH insight with nugget_type
- Add enrichment based on nugget_type (see requirements above)
- Top 10 insights MUST have learning_hook
- Assign a category to EACH insight
- Include spicy_rating (1-5) for each insight
- Return ONLY valid JSON, no other text

**CRITICAL: If an insight makes you think "so what?" or "everyone knows that", REJECT IT. Only include insights that provide genuine, specific value.**
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
