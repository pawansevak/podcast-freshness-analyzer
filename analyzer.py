"""
Podcast Analyzer - LLM-Powered Version (CRITICAL SCORING + TOP 5 TAKEAWAYS)
Uses Claude API with HARSH criteria for freshness and insights
Always returns Top 5 non-obvious takeaways with timestamps
"""

import anthropic
import json
import os
from datetime import datetime

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def get_client():
    """Lazy load the Anthropic client"""
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


ANALYSIS_PROMPT = """You are an EXTREMELY CRITICAL expert at analyzing podcast content for freshness and insight quality. You are evaluating for an experienced Principal Product Manager in AI/ML who has heard HUNDREDS of podcasts and read extensively. Your standards are very high.

**CRITICAL CONTEXT:**
Most podcasts recycle the same advice. Iteration, speed, customer focus, building MVPs, finding PMF - these are OBVIOUS. The PM you're analyzing for has heard all of this dozens of times. They want insights that would surprise THEM.

Analyze this podcast transcript with HARSH scoring:

**FRESHNESS SCORING (1-10) - BE CRITICAL:**

TRULY FRESH content (8-10):
- References specific events/technologies from last 3-6 months
- Discusses emerging trends NOT yet covered in mainstream podcasts
- Challenges conventional wisdom with BRAND NEW data or findings
- Time-sensitive insights that will age within 6-12 months
- Uses terminology or frameworks that emerged recently

MODERATELY FRESH (5-7):
- Some recent references (last 6-12 months) mixed with timeless content
- Updates to well-known frameworks with new twists
- Could stay relevant for 1-2 years
- Mentions current events but insights are somewhat timeless

STALE content (1-4):
- Evergreen advice that's been repeated for 5+ years
- No time-sensitive references at all
- Generic frameworks everyone knows (agile, lean, user-focused, iterate fast)
- Could have been recorded anytime in the last decade
- Timeless platitudes dressed up with current examples

**INSIGHT QUALITY SCORING (1-10) - BE EXTREMELY HARSH:**

TRULY NON-OBVIOUS insights (8-10):
- Would genuinely SURPRISE an experienced product/engineering leader
- Backed by SPECIFIC numbers, data, or concrete examples (not vague)
- DIRECTLY contradicts what most people believe (not just "nuances" it)
- Something you couldn't find in 10+ other popular podcasts or blogs
- Makes you completely rethink a fundamental assumption
- Passes the test: "An expert in this field would say 'I never thought of it that way'"

Examples of truly non-obvious:
- "PageRank died in 2005, click behavior became Google's real power"
- "Foundation model companies are empires that haven't met their oceans yet"
- Specific data that contradicts industry consensus

MODERATE insights (4-7):
- Useful tactical advice with some specificity
- Interesting examples or case studies
- Familiar concepts explained well or with a fresh angle
- Would be helpful to someone less experienced
- You've heard the core idea before but the execution details are good

OBVIOUS insights (1-3):
- Advice repeated across multiple podcasts/blogs:
  * Squad/pod structures, reducing layers
  * Iterate don't perfect, speed over strategy
  * Small experiments over big bets
  * Build internal tools first
  * Find PMF, focus on value creation
  * AI needs eval frameworks
  * Subscription fatigue, consumption pricing
- Generic startup/product wisdom
- Common knowledge restated nicely
- "Best practices" everyone already knows
- Familiar advice with slightly different words

**CRITICAL SCORING GUIDELINES:**
- DEFAULT to 4-6/10 for most content
- Reserve 7-8/10 for genuinely good insights
- Reserve 9-10/10 for mind-blowing, paradigm-shifting insights (rare!)
- If you've heard the advice in other contexts, it's OBVIOUS (score 1-4)
- If it sounds like something from a business book, it's OBVIOUS
- Be HARSH - assume the listener is sophisticated and well-read
- Most podcasts should score 4-6 on insights, 5-7 on freshness

**YOUR ANALYSIS TASK:**

1. **Freshness Score (1-10)**: Rate how timely and current (BE CRITICAL)
2. **Freshness Reasoning**: 2-3 sentences explaining your harsh score
3. **Insight Score (1-10)**: Rate how non-obvious and valuable (BE EXTREMELY CRITICAL)
4. **Insight Reasoning**: 2-3 sentences explaining why you scored harshly
5. **Top 5 Non-Obvious Takeaways**: Extract EXACTLY 5 insights that pass the harsh filter
   - Each MUST have a specific timestamp (estimate if needed)
   - Each MUST be genuinely non-obvious to experienced PMs
   - Rank them from most to least non-obvious
   - Reject any obvious advice (iteration, speed, pods, MVPs, etc.)
   - If you can't find 5 truly non-obvious insights, still provide 5, but mark the weaker ones as "best_available" and note they're somewhat obvious
6. **Summary**: 2-3 sentence overview
7. **Key Characteristics**: 3-5 tags
8. **Obvious Insights Rejected**: List 3-5 insights you found but rejected as too common

**REJECTION CRITERIA FOR THE TOP 5:**
DO NOT include takeaways about:
- Iteration over perfection
- Speed/execution over strategy  
- Reducing organizational layers/pods/squads
- Small experiments before big bets
- Building internal tools first
- Finding product-market fit
- Focus on customer value
- AI needs eval frameworks
- Consumption vs subscription pricing
- Any advice you've heard in multiple other podcasts

ONLY include takeaways that would make an experienced PM think "Wow, I never considered that."

If the podcast doesn't have 5 truly non-obvious insights, still provide 5, but mark the weaker ones with obviousness_level: "best_available" and note they're somewhat obvious.

Return your analysis as valid JSON with this exact structure:
{{
  "freshness_score": 5,
  "freshness_reasoning": "Your critical explanation here",
  "insight_score": 4,
  "insight_reasoning": "Your harsh explanation here",
  "top_5_takeaways": [
    {{
      "rank": 1,
      "insight": "Most non-obvious insight from the entire podcast",
      "timestamp": "15:30",
      "why_valuable": "Why this is genuinely surprising to an expert",
      "obviousness_level": "truly_non_obvious"
    }},
    {{
      "rank": 2,
      "insight": "Second most non-obvious insight",
      "timestamp": "23:45",
      "why_valuable": "Why this matters to experienced PMs",
      "obviousness_level": "truly_non_obvious"
    }},
    {{
      "rank": 3,
      "insight": "Third insight",
      "timestamp": "31:20",
      "why_valuable": "Why valuable",
      "obviousness_level": "truly_non_obvious"
    }},
    {{
      "rank": 4,
      "insight": "Fourth insight",
      "timestamp": "42:10",
      "why_valuable": "Why it matters",
      "obviousness_level": "moderately_non_obvious"
    }},
    {{
      "rank": 5,
      "insight": "Fifth insight (may be best available if podcast lacks depth)",
      "timestamp": "55:30",
      "why_valuable": "Why included despite being more obvious",
      "obviousness_level": "best_available"
    }}
  ],
  "summary": "2-3 sentence summary of key themes",
  "characteristics": ["tag1", "tag2", "tag3"],
  "obvious_insights_rejected": [
    "Iteration beats perfection (heard in 20+ podcasts)",
    "Build internal tools first (common advice)",
    "Small experiments over big bets (repeated constantly)"
  ]
}}

TRANSCRIPT TO ANALYZE:
{transcript}

Remember: BE HARSH. Most content is mediocre. Reserve high scores for truly exceptional insights. Respond ONLY with valid JSON. Do not include any text before or after the JSON.
"""


def analyze_podcast_with_llm(transcript: str, podcast_metadata: dict = None) -> dict:
    """
    Analyze a podcast transcript using Claude API with CRITICAL scoring
    """
    
    # Prepare the prompt
    prompt = ANALYSIS_PROMPT.format(transcript=transcript[:50000])
    
    try:
        # Call Claude API
        client = get_client()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2500,
            temperature=0.2,  # Lower for more consistent harsh scoring
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
        analysis["scoring_mode"] = "critical"
        
        if podcast_metadata:
            analysis["podcast_metadata"] = podcast_metadata
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing podcast: {e}")
        print(f"Response was: {response_text if 'response_text' in locals() else 'No response'}")
        return {
            "freshness_score": 5,
            "freshness_reasoning": "Analysis failed",
            "insight_score": 5,
            "insight_reasoning": "Analysis failed",
            "top_5_takeaways": [],
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
    cache_path = f'cache/{podcast_id}_analysis_critical.json'
    
    with open(cache_path, 'w') as f:
        json.dump(analysis, f, indent=2)


def load_analysis_cache(podcast_id: str) -> dict:
    """Load cached analysis if it exists"""
    cache_path = f'cache/{podcast_id}_analysis_critical.json'
    
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    
    return None


def analyze_podcast(podcast_id: str, use_cache: bool = True) -> dict:
    """
    Main function to analyze a podcast with CRITICAL scoring
    """
    
    # Check cache first
    if use_cache:
        cached = load_analysis_cache(podcast_id)
        if cached:
            print(f"Using cached CRITICAL analysis for {podcast_id}")
            return cached
    
    # Load transcript and metadata
    print(f"Analyzing {podcast_id} with CRITICAL Claude API scoring...")
    transcript = load_transcript(podcast_id)
    metadata = load_metadata(podcast_id)
    
    # Analyze with LLM
    analysis = analyze_podcast_with_llm(transcript, metadata)
    
    # Cache the results
    save_analysis_cache(podcast_id, analysis)
    
    print(f"✓ CRITICAL Analysis complete for {podcast_id}")
    print(f"  Freshness: {analysis['freshness_score']}/10 (HARSH)")
    print(f"  Insights: {analysis['insight_score']}/10 (HARSH)")
    
    return analysis


if __name__ == "__main__":
    # Test the analyzer
    print("Testing CRITICAL LLM Analyzer with Top 5 Takeaways")
    print("="*60)
    print("NOTE: This version is MUCH harsher than the standard analyzer")
    print("Most podcasts will score 4-6/10 on insights")
    print("="*60)
    
    # Test with snowflake_ceo
    result = analyze_podcast("anthropic_cpo", use_cache=False)
    
    print("\n" + "="*60)
    print("CRITICAL ANALYSIS RESULTS:")
    print("="*60)
    print(f"\nFreshness Score: {result['freshness_score']}/10")
    print(f"Reasoning: {result['freshness_reasoning']}\n")
    print(f"Insight Score: {result['insight_score']}/10")
    print(f"Reasoning: {result['insight_reasoning']}\n")
    print(f"Summary: {result['summary']}\n")
    
    if 'obvious_insights_rejected' in result:
        print("Obvious Insights REJECTED:")
        for rejected in result['obvious_insights_rejected']:
            print(f"  ✗ {rejected}")
    
    print("\n" + "="*60)
    print("TOP 5 NON-OBVIOUS TAKEAWAYS (with timestamps):")
    print("="*60)
    for takeaway in result.get('top_5_takeaways', []):
        print(f"\n#{takeaway['rank']} [{takeaway['timestamp']}] - ({takeaway.get('obviousness_level', 'N/A')})")
        print(f"   {takeaway['insight']}")
        print(f"   → Why valuable: {takeaway['why_valuable']}")
