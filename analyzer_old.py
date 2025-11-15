"""
Podcast Analyzer - Core Analysis Module
Uses Claude API to analyze podcast transcripts
"""

import json
import os
from datetime import datetime


def extract_unique_insights(transcript_text):
    """
    Extract unique insights with exact quotes from the transcript
    """
    insights = []
    lines = transcript_text.split('\n')
    
    # Keywords that indicate insights
    insight_keywords = [
        'counterintuitive', 'counter-intuitive', 'surprising', 'unexpected',
        'interesting', 'novel', 'key insight', 'important', 'fascinating',
        'contrarian', 'non-obvious', 'the data shows', 'we found that',
        'what we discovered', 'turns out', 'actually'
    ]
    
    # Look for sentences with numbers/data
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Check for insight indicators
        has_insight_keyword = any(keyword in line_lower for keyword in insight_keywords)
        has_data = any(char.isdigit() for char in line) and any(word in line_lower for word in ['percent', '%', 'study', 'research'])
        
        # Extract sentences that contain insights
        if has_insight_keyword or has_data:
            # Get context (this line and potentially next line)
            quote = line.strip()
            if quote and len(quote) > 20:  # Meaningful length
                # Clean up quote
                quote = quote.replace('Host:', '').replace('Guest:', '').strip()
                
                # Determine insight type
                if 'counterintuitive' in line_lower or 'counter-intuitive' in line_lower or 'surprising' in line_lower:
                    insight_type = "Counter-intuitive Finding"
                elif has_data:
                    insight_type = "Data-Backed Insight"
                elif 'framework' in line_lower or 'model' in line_lower or 'pattern' in line_lower:
                    insight_type = "Novel Framework"
                else:
                    insight_type = "Key Insight"
                
                insights.append({
                    "type": insight_type,
                    "quote": quote[:300]  # Limit quote length
                })
    
    # Remove duplicates and limit to top 5
    seen_quotes = set()
    unique_insights = []
    for insight in insights:
        if insight['quote'] not in seen_quotes and len(unique_insights) < 5:
            seen_quotes.add(insight['quote'])
            unique_insights.append(insight)
    
    return unique_insights


def analyze_podcast(transcript_text, user_preferences=None):
    """
    Analyze a podcast transcript using Claude API
    
    Args:
        transcript_text: The full transcript text
        user_preferences: Optional dict with user preferences
        
    Returns:
        Dict with freshness_score, insight_score, highlights, and reasoning
    """
    
    # Build preference context if provided
    preference_context = ""
    if user_preferences:
        topics = user_preferences.get('topics_of_interest', [])
        freshness = user_preferences.get('freshness_priority', 'medium')
        insight_style = user_preferences.get('insight_style', 'general')
        
        preference_context = f"""
USER PREFERENCES:
- Topics of interest: {', '.join(topics)}
- Freshness priority: {freshness} (how much they care about recency)
- Preferred insight style: {insight_style}

Consider these preferences when scoring. Content matching their interests should be weighted more heavily.
"""
    
    prompt = f"""Analyze this podcast transcript and provide a detailed scoring:

{preference_context}

1. **Freshness Score (1-10)**: How recent, timely, or cutting-edge is the information?
   - 1-3: Outdated information, old examples, or timeless/generic content
   - 4-6: Somewhat current, but not particularly time-sensitive
   - 7-8: Recent information, current examples (within last 6-12 months)
   - 9-10: Very recent developments, breaking trends, cutting-edge topics

2. **Insight Score (1-10)**: How non-obvious, valuable, and specific are the insights?
   - 1-3: Generic advice, common platitudes, no specific examples
   - 4-6: Moderately interesting, some specific examples
   - 7-8: Counter-intuitive ideas, novel frameworks, specific data/examples
   - 9-10: Highly novel perspectives, surprising data, actionable + specific insights

3. **Top 3 Highlights**: Identify the 3 most valuable segments worth listening to
   - Include what makes each segment valuable
   - Be specific about what insight or information is shared

4. **Key Characteristics**: Note if the podcast includes:
   - Specific data/numbers vs. vague claims
   - Concrete examples vs. generic statements  
   - Novel frameworks or mental models
   - Contrarian or counter-intuitive takes
   - Actionable advice vs. motivational platitudes

TRANSCRIPT:
{transcript_text[:50000]}

Provide your response as valid JSON (no markdown formatting):
{{
  "freshness_score": <number 1-10>,
  "freshness_reasoning": "<2-3 sentence explanation>",
  "insight_score": <number 1-10>,
  "insight_reasoning": "<2-3 sentence explanation>",
  "highlights": [
    {{"segment": "<brief description>", "value": "<why it's worth listening to>"}},
    {{"segment": "<brief description>", "value": "<why it's worth listening to>"}},
    {{"segment": "<brief description>", "value": "<why it's worth listening to>"}}
  ],
  "key_characteristics": {{
    "has_specific_data": <boolean>,
    "has_concrete_examples": <boolean>,
    "has_novel_frameworks": <boolean>,
    "has_contrarian_takes": <boolean>,
    "has_actionable_advice": <boolean>
  }},
  "summary": "<1-2 sentence overall assessment>"
}}

Remember: Be critical and honest. Most podcasts should score 4-6. Reserve 8+ for truly exceptional content.
"""

    # For demo purposes, we'll simulate the API call
    # In production, you would use: 
    # import anthropic
    # client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    # message = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=2000, messages=[{"role": "user", "content": prompt}])
    # response_text = message.content[0].text
    
    # For this demo, we'll return mock analysis based on transcript content
    return simulate_analysis(transcript_text, user_preferences)


def simulate_analysis(transcript_text, user_preferences=None):
    """
    Simulate LLM analysis for demo purposes
    In production, replace this with actual Claude API calls
    """
    
    # Simple heuristics to demonstrate functionality
    transcript_lower = transcript_text.lower()
    
    # Check for specific indicators
    has_data = any(word in transcript_lower for word in ['study', 'research', 'data', 'percent', '%', 'participants'])
    has_examples = any(word in transcript_lower for word in ['example', 'specifically', 'instance', 'for instance'])
    has_recent = any(word in transcript_lower for word in ['2024', '2025', 'recent', 'latest', 'emerging'])
    has_generic = any(phrase in transcript_lower for phrase in ['work hard', 'stay focused', 'never give up', 'hustle'])
    
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
    
    # Extract highlights (simplified)
    highlights = []
    if 'counterintuitive' in transcript_lower or 'counter-intuitive' in transcript_lower:
        highlights.append({
            "segment": "Counter-intuitive insight shared",
            "value": "Challenges conventional thinking with surprising perspective"
        })
    if any(str(i) in transcript_text for i in range(20, 100)):
        highlights.append({
            "segment": "Data-backed claim with specific numbers",
            "value": "Provides concrete metrics and research findings"
        })
    if 'example' in transcript_lower:
        highlights.append({
            "segment": "Concrete example or case study",
            "value": "Real-world application of concepts discussed"
        })
    
    # Ensure we have 3 highlights
    while len(highlights) < 3:
        highlights.append({
            "segment": "Key discussion point",
            "value": "Important concept covered in this section"
        })
    
    # Extract unique insights with quotes
    unique_insights = extract_unique_insights(transcript_text)
    
    return {
        "freshness_score": freshness,
        "freshness_reasoning": f"Content appears {'very recent and timely' if freshness >= 7 else 'somewhat dated or generic'} based on references and examples used.",
        "insight_score": insight,
        "insight_reasoning": f"{'Strong specific insights with data and examples' if insight >= 7 else 'More generic advice without much specificity or novel perspectives'}.",
        "highlights": highlights[:3],
        "unique_insights": unique_insights,  # NEW: Add unique insights with quotes
        "key_characteristics": {
            "has_specific_data": has_data,
            "has_concrete_examples": has_examples,
            "has_novel_frameworks": 'framework' in transcript_lower or 'model' in transcript_lower,
            "has_contrarian_takes": 'counterintuitive' in transcript_lower or 'contrarian' in transcript_lower,
            "has_actionable_advice": has_examples and not has_generic
        },
        "summary": summary
    }


def load_transcript(podcast_id):
    """Load a transcript file"""
    filepath = f"transcripts/{podcast_id}.txt"
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Transcript {podcast_id} not found")
    
    with open(filepath, 'r') as f:
        return f.read()


def load_user_preferences(user_id="default"):
    """Load user preferences"""
    filepath = f"users/{user_id}_preferences.json"
    if not os.path.exists(filepath):
        # Return default preferences
        return {
            "topics_of_interest": [],
            "freshness_priority": "medium",
            "insight_style": "general"
        }
    
    with open(filepath, 'r') as f:
        return json.load(f)


def save_analysis_cache(podcast_id, user_id, analysis_result):
    """Cache analysis results"""
    os.makedirs("cache", exist_ok=True)
    filepath = f"cache/{podcast_id}_{user_id}.json"
    
    cache_data = {
        "podcast_id": podcast_id,
        "user_id": user_id,
        "analyzed_at": datetime.now().isoformat(),
        "analysis": analysis_result
    }
    
    with open(filepath, 'w') as f:
        json.dump(cache_data, f, indent=2)


def load_analysis_cache(podcast_id, user_id):
    """Load cached analysis if exists"""
    filepath = f"cache/{podcast_id}_{user_id}.json"
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r') as f:
        cache_data = json.load(f)
        return cache_data["analysis"]


if __name__ == "__main__":
    # Test the analyzer
    print("Testing Podcast Analyzer...")
    print("-" * 50)
    
    # Load and analyze a transcript
    transcript = load_transcript("podcast_1")
    user_prefs = load_user_preferences("default")
    
    print(f"Analyzing podcast_1...")
    result = analyze_podcast(transcript, user_prefs)
    
    print(f"\n✓ Freshness Score: {result['freshness_score']}/10")
    print(f"  {result['freshness_reasoning']}")
    
    print(f"\n✓ Insight Score: {result['insight_score']}/10")
    print(f"  {result['insight_reasoning']}")
    
    print(f"\n✓ Top Highlights:")
    for i, highlight in enumerate(result['highlights'], 1):
        print(f"  {i}. {highlight['segment']}")
        print(f"     → {highlight['value']}")
    
    print(f"\n✓ Summary: {result['summary']}")
    
    # Save to cache
    save_analysis_cache("podcast_1", "default", result)
    print(f"\n✓ Analysis cached successfully")
