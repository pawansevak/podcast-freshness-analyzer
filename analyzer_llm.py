"""
Podcast Analyzer - LLM-Powered Version
Uses Claude API for sophisticated analysis of freshness and insights
"""

import anthropic
import json
import os
from datetime import datetime

# Your Claude API key - REPLACE THIS WITH YOUR FULL KEY
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

ANALYSIS_PROMPT = """You are an expert at analyzing podcast content for freshness and insight quality.

Analyze this podcast transcript and score it on two critical dimensions:

**FRESHNESS SCORING (1-10):**

FRESH content (8-10):
- References events/technologies from last 6-12 months
- Discusses emerging trends not yet mainstream
- Challenges conventional wisdom with NEW data
- Time-sensitive insights that will age quickly
- Uses current terminology and frameworks

MODERATELY FRESH (5-7):
- Mix of timely and evergreen content
- Some recent references but mostly timeless
- Updates to established frameworks
- Could be relevant for 2-3 years

STALE content (1-4):
- Evergreen advice repeated for years
- No time-sensitive references
- Generic frameworks everyone knows
- Could have been recorded 5+ years ago
- Timeless but not novel

**INSIGHT QUALITY SCORING (1-10):**

NON-OBVIOUS insights (8-10):
- Counterintuitive findings ("everyone thinks X, but data shows Y")
- Specific numbers/data that contradict beliefs
- Novel mental models or unique frameworks
- Concrete examples with surprising outcomes
- Makes you rethink fundamental assumptions
- "Aha moments" backed by evidence

MODERATE insights (5-7):
- Useful but not revolutionary
- Good examples of known principles
- Tactical advice with some specificity
- Helpful but predictable takeaways

OBVIOUS insights (1-4):
- Generic advice ("focus on users", "move fast", "test your ideas")
- Platitudes without specifics or evidence
- Common knowledge restated nicely
- Surface-level observations
- Could find in any business book

**YOUR ANALYSIS TASK:**

1. **Freshness Score (1-10)**: Rate how timely and current the content is
2. **Freshness Reasoning**: 2-3 sentences explaining your score
3. **Insight Score (1-10)**: Rate how non-obvious and valuable the insights are
4. **Insight Reasoning**: 2-3 sentences explaining your score
5. **Top Highlights**: Extract 3-5 most valuable non-obvious insights with approximate timestamps
6. **Summary**: 2-3 sentence overview of key takeaways
7. **Key Characteristics**: 3-5 tags describing the podcast (e.g., data-driven, contrarian, tactical, theoretical, storytelling, research-backed)

**IMPORTANT GUIDELINES:**
- Be critical - most content is 5-7/10, not 8-10
- Reward specificity and data over vague advice
- Reward contrarian views backed by evidence
- Penalize generic platitudes and common wisdom
- Look for the "non-obvious" - what would surprise an expert?

Return your analysis as valid JSON with this exact structure:
{{
  "freshness_score": 7,
  "freshness_reasoning": "Your explanation here",
  "insight_score": 6,
  "insight_reasoning": "Your explanation here",
  "highlights": [
    {{
      "insight": "Specific non-obvious insight here",
      "timestamp": "15:30",
      "why_valuable": "Why this is surprising or counterintuitive"
    }}
  ],
  "summary": "2-3 sentence summary of key takeaways",
  "characteristics": ["tag1", "tag2", "tag3"]
}}

TRANSCRIPT TO ANALYZE:
{transcript}

Respond ONLY with valid JSON. Do not include any text before or after the JSON.
"""


def analyze_podcast_with_llm(transcript: str, podcast_metadata: dict = None) -> dict:
    """
    Analyze a podcast transcript using Claude API
    
    Args:
        transcript: The full podcast transcript text
        podcast_metadata: Optional metadata (title, host, guest, etc.)
    
    Returns:
        dict: Analysis results with scores, highlights, and insights
    """
    
    # Prepare the prompt
    prompt = ANALYSIS_PROMPT.format(transcript=transcript[:50000])  # Limit to ~50k chars
    
    try:
        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the response
        response_text = message.content[0].text
        
        # Parse JSON response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(response_text)
        
        # Add metadata
        analysis["analyzed_at"] = datetime.now().isoformat()
        analysis["model"] = "claude-sonnet-4-20250514"
        
        if podcast_metadata:
            analysis["podcast_metadata"] = podcast_metadata
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing podcast: {e}")
        return {
            "freshness_score": 5,
            "freshness_reasoning": "Analysis failed",
            "insight_score": 5,
            "insight_reasoning": "Analysis failed",
            "highlights": [],
            "summary": "Analysis could not be completed.",
            "characteristics": ["error"],
            "error": str(e)
        }


def load_transcript(podcast_id: str) -> str:
    """Load transcript from file"""
    transcript_path = f"transcripts/{podcast_id}.txt"
    
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript not found: {transcript_path}")
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_metadata(podcast_id: str) -> dict:
    """Load podcast metadata"""
    try:
        with open('transcripts_metadata.json', 'r') as f:
            all_metadata = json.load(f)
            return all_metadata.get(podcast_id, {})
    except:
        return {}


def save_analysis_cache(podcast_id: str, analysis: dict):
    """Cache analysis results"""
    os.makedirs('cache', exist_ok=True)
    cache_path = f'cache/{podcast_id}_analysis.json'
    
    with open(cache_path, 'w') as f:
        json.dump(analysis, f, indent=2)


def load_analysis_cache(podcast_id: str) -> dict:
    """Load cached analysis if it exists"""
    cache_path = f'cache/{podcast_id}_analysis.json'
    
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    
    return None


def analyze_podcast(podcast_id: str, use_cache: bool = True) -> dict:
    """
    Main function to analyze a podcast
    """
    
    # Check cache first
    if use_cache:
        cached = load_analysis_cache(podcast_id)
        if cached:
            print(f"Using cached analysis for {podcast_id}")
            return cached
    
    # Load transcript and metadata
    print(f"Analyzing {podcast_id} with Claude API...")
    transcript = load_transcript(podcast_id)
    metadata = load_metadata(podcast_id)
    
    # Analyze with LLM
    analysis = analyze_podcast_with_llm(transcript, metadata)
    
    # Cache the results
    save_analysis_cache(podcast_id, analysis)
    
    print(f"✓ Analysis complete for {podcast_id}")
    print(f"  Freshness: {analysis['freshness_score']}/10")
    print(f"  Insights: {analysis['insight_score']}/10")
    
    return analysis


if __name__ == "__main__":
    # Test the analyzer
    print("Testing LLM Analyzer...")
    
    # Test with podcast_1
    result = analyze_podcast("snowflake_ceo", use_cache=False)
    
    print("\n" + "="*60)
    print("ANALYSIS RESULTS:")
    print("="*60)
    print(f"\nFreshness Score: {result['freshness_score']}/10")
    print(f"Reasoning: {result['freshness_reasoning']}\n")
    print(f"Insight Score: {result['insight_score']}/10")
    print(f"Reasoning: {result['insight_reasoning']}\n")
    print(f"Summary: {result['summary']}\n")
    print("Top Highlights:")
    for i, highlight in enumerate(result['highlights'][:3], 1):
        print(f"\n{i}. {highlight['insight']}")
        if 'why_valuable' in highlight:
            print(f"   Why valuable: {highlight['why_valuable']}")
