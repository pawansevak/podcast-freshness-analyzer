"""
Mostly Mid Hybrid Analyzer - Combines V1's Critical Analysis with V2's Multi-Dimensional Scoring
"""

import anthropic
import json
import os
from typing import Dict, Any
from datetime import datetime

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

ANALYSIS_PROMPT = """You are an EXTREMELY CRITICAL expert podcast analyst for "Mostly Mid" - a platform that saves experienced professionals from wasting time on mediocre content.

**CRITICAL CONTEXT:**
You are evaluating for experienced Principal Product Managers and senior leaders who have heard HUNDREDS of podcasts and read extensively. Your standards are VERY high. Most podcasts recycle the same advice. The listeners you're serving want insights that would surprise THEM.

---

## PART 1: MULTI-DIMENSIONAL SCORING (BE HARSH)

### CRITICAL SCORING RULES:
- Use the FULL 1-10 scale. Most podcasts ARE mediocre (5-6 range)
- Only truly exceptional content gets 9-10 (think top 5% of all podcasts ever)
- Only truly terrible content gets 1-3
- BE HARSH. If you're unsure, round DOWN
- Your scores should spread across 3-9 range, NOT cluster at 6-8
- Assume the listener is sophisticated, experienced, and has heard common advice 100+ times

---

### 1. INSIGHT DENSITY (40% weight) - "Non-obvious insights per minute"

**What counts as a REAL insight for experienced professionals:**

TRULY NON-OBVIOUS insights (8-10):
- Would genuinely SURPRISE an experienced product/engineering leader
- Backed by SPECIFIC numbers, data, or concrete examples (not vague)
- DIRECTLY contradicts what most people believe (not just "nuances" it)
- Something you couldn't find in 10+ other popular podcasts or blogs
- Makes you completely rethink a fundamental assumption
- Passes the test: "An expert in this field would say 'I never thought of it that way'"

Examples of 8-10 insights:
- "PageRank died in 2005, click behavior became Google's real power"
- "Foundation model companies are empires that haven't met their oceans yet"
- "Winning Product Hunt can be a vanity metric trap - we achieved product of month but recognized it wasn't sustainable growth and made a 'bet the company' decision to rebuild onboarding entirely"

MODERATE insights (4-7):
- Useful tactical advice with some specificity
- Interesting examples or case studies
- Familiar concepts explained well or with a fresh angle
- Would be helpful to someone less experienced
- You've heard the core idea before but the execution details are good

OBVIOUS insights (1-3) - DO NOT REWARD THESE:
- Iteration over perfection, speed over strategy
- Squad/pod structures, reducing layers
- Small experiments over big bets
- Build internal tools first, find PMF, focus on value creation
- AI needs eval frameworks, subscription fatigue, consumption pricing
- Generic startup/product wisdom
- Common knowledge restated nicely
- "Best practices" everyone already knows

**Scoring:**
- **10 = Mind-blowing non-obvious insights every few minutes**
- **5 = Mix of decent insights and obvious advice**
- **1 = Pure platitudes, generic motivational content**

Density calculation: 1 genuinely non-obvious insight per 10 min = 5/10, per 5 min = 8/10, per 2 min = 10/10

---

### 2. SIGNAL-TO-NOISE RATIO (20% weight) - "How much rambling?"

Score 1-10 based on:
- Time spent on: useful content vs. self-promotion, tangents, filler
- Editing quality (tight vs. meandering)
- Host's ability to extract value (crisp questions vs. aimless chat)

**10 = Every sentence adds value**, zero fat
**5 = 50/50 good content and rambling**
**1 = 90% filler, ads, stories that go nowhere**

---

### 3. ACTIONABILITY (20% weight) - "Can I use this Monday?"

Score 1-10 based on:
- Specific tactics with implementation steps (not just philosophy)
- Examples with enough detail to replicate
- Frameworks you can apply immediately

**10 = Step-by-step playbook** (e.g., "Here's the email template, send it at 10am Tuesday")
**5 = Directionally helpful** (e.g., "Try using customer interviews to find insights")
**1 = Pure theory, zero practical value**

---

### 4. CONTRARIAN INDEX (10% weight) - "Does this challenge groupthink?"

Score 1-10 based on:
- Says things that would make peers uncomfortable
- Challenges industry orthodoxy with evidence
- Goes against current trends with reasoning

**10 = Genuinely controversial take** that changes how you think
**5 = Mildly spicy** but still safe
**1 = Complete consensus opinion** everyone already agrees with

---

### 5. FRESHNESS (5% weight) - "Is this still relevant?"

**BE CRITICAL about what counts as "fresh":**

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

**10 = Cutting edge**, recorded recently, highly relevant now, will age within months
**5 = Somewhat dated** but core ideas still apply, could be from 1-2 years ago
**1 = Completely obsolete** (e.g., "Use Google+ for marketing") or completely timeless generic advice

---

### 6. HOST QUALITY (5% weight) - "Does the host elevate or drag it down?"

Score 1-10 based on:
- Asks probing follow-ups (vs. scripted questions)
- Challenges weak answers (vs. accepts everything)
- Manages time well (vs. lets guest ramble)

**10 = Masterful interviewer** who draws out gold
**5 = Competent but unremarkable**
**1 = Actively makes the episode worse**

---

## PART 2: TOP 5 NON-OBVIOUS TAKEAWAYS

Extract EXACTLY 5 insights that pass the harsh filter for experienced listeners:

**REJECTION CRITERIA - DO NOT include takeaways about:**
- Iteration over perfection, speed/execution over strategy
- Reducing organizational layers/pods/squads
- Small experiments before big bets
- Building internal tools first
- Finding product-market fit, focus on customer value
- AI needs eval frameworks
- Consumption vs subscription pricing
- Any advice you've heard in multiple other podcasts

**INCLUSION CRITERIA - ONLY include:**
- Insights that would make an experienced PM/leader think "Wow, I never considered that"
- Specific numbers, data, or concrete examples
- Contrarian takes with evidence
- Tactical details with enough specificity to replicate

**If the podcast doesn't have 5 truly non-obvious insights:**
- Still provide 5 takeaways
- Mark the weaker ones with obviousness_level: "best_available"
- Note in why_valuable that they're more obvious but best available

Each takeaway must include:
- Specific timestamp (estimate if needed)
- Why it's genuinely non-obvious/valuable
- Obviousness level: "truly_non_obvious", "moderately_non_obvious", or "best_available"

---

## OUTPUT FORMAT (JSON):

Return a JSON object with this EXACT structure:

{{
  "scores": {{
    "insight_density": <1-10>,
    "signal_to_noise": <1-10>,
    "actionability": <1-10>,
    "contrarian_index": <1-10>,
    "freshness": <1-10>,
    "host_quality": <1-10>,
    "overall": <calculated weighted average, 1 decimal>
  }},
  "verdict": {{
    "tldr": "<One brutal sentence: Is this worth 60 minutes of your life? Be honest.>",
    "best_for": "<Who should listen? Be SPECIFIC: 'Series B founders struggling with pricing' not 'product people'>",
    "skip_if": "<Who should avoid? Be HONEST: 'If you're past beginner stage' or 'If you've heard standard PM advice'>",
    "worth_it": <true/false>,
    "best_quote": "<One genuinely useful/interesting quote from the episode>"
  }},
  "top_5_takeaways": [
    {{
      "rank": 1,
      "insight": "Most non-obvious insight from the entire podcast",
      "timestamp": "15:30",
      "why_valuable": "Why this is genuinely surprising to an experienced professional",
      "obviousness_level": "truly_non_obvious"
    }},
    {{
      "rank": 2,
      "insight": "Second most non-obvious insight",
      "timestamp": "23:45",
      "why_valuable": "Why this matters to experienced listeners",
      "obviousness_level": "truly_non_obvious"
    }},
    {{
      "rank": 3,
      "insight": "Third insight",
      "timestamp": "31:20",
      "why_valuable": "Why valuable",
      "obviousness_level": "moderately_non_obvious"
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
  "why_these_scores": {{
    "insight_density": "<Why this score? Be specific about insight quality and how many were truly non-obvious vs obvious>",
    "signal_to_noise": "<Why this score? Mention ratio of value to filler>",
    "actionability": "<Why this score? Can you actually use this? Be honest about specificity>",
    "contrarian_index": "<Why this score? Does it challenge orthodoxy or repeat consensus?>",
    "freshness": "<Why this score? Is it current/time-sensitive or could be from any year?>",
    "host_quality": "<Why this score? Does host elevate it or enable rambling?>"
  }},
  "summary": "<2-3 sentence overview of key themes and whether it's worth listening>",
  "characteristics": ["<tag1>", "<tag2>", "<tag3>", "<tag4>", "<tag5>"],
  "obvious_insights_rejected": [
    "<Insight 1 you found but rejected as too common/obvious>",
    "<Insight 2 rejected - explain why it's heard everywhere>",
    "<Insight 3 rejected - standard advice everyone knows>"
  ]
}}

---

## TRANSCRIPT TO ANALYZE:

{transcript}

---

## FINAL REMINDERS:

**For Scoring:**
- BE BRUTALLY HARSH. Use the full 1-10 scale
- Most episodes are 4-6 overall (mediocre)
- Only exceptional content gets 8+
- If you're tempted to give all 7s and 8s, you're being too generous
- The goal is DIFFERENTIATION so experienced listeners know what to skip
- Assume listener has heard common PM/startup/product advice 100+ times

**For Top 5 Takeaways:**
- Default to assuming insights are OBVIOUS unless proven otherwise
- If it sounds like something from a business book → REJECT IT
- If you've heard similar advice in other contexts → mark as "best_available" at most
- Reserve "truly_non_obvious" for genuine surprises
- Be willing to admit when a podcast lacks depth

**Quality bar:**
- Most podcasts should score 4-6 on insights
- Most should score 5-7 on freshness
- Only rare podcasts achieve 8+ on insight density
- Timeless generic advice should score 1-4 on freshness

Return ONLY the JSON, no other text.
"""


def calculate_overall_score(scores: Dict[str, float]) -> float:
    """
    Calculate weighted overall score based on the 6 dimensions.
    
    Weights:
    - Insight Density: 40%
    - Signal-to-Noise: 20%
    - Actionability: 20%
    - Contrarian Index: 10%
    - Freshness: 5%
    - Host Quality: 5%
    """
    weights = {
        'insight_density': 0.40,
        'signal_to_noise': 0.20,
        'actionability': 0.20,
        'contrarian_index': 0.10,
        'freshness': 0.05,
        'host_quality': 0.05
    }
    
    overall = sum(scores[dim] * weights[dim] for dim in weights.keys())
    return round(overall, 1)


def analyze_podcast(transcript: str, model: str = "claude-sonnet-4-20250514") -> Dict[str, Any]:
    """
    Analyze a podcast transcript with hybrid critical multi-dimensional scoring.
    
    Args:
        transcript: The podcast transcript text
        model: Claude model to use (default: sonnet-4)
        
    Returns:
        Dictionary with scores, verdict, insights, top 5 takeaways, and reasoning
    """
    
    prompt = ANALYSIS_PROMPT.format(transcript=transcript)
    
    print("🎯 Analyzing podcast with hybrid critical scoring system...")
    
    response = client.messages.create(
        model=model,
        max_tokens=4000,
        temperature=0.3,  # Lower temperature for more consistent scoring
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract JSON from response
    response_text = response.content[0].text
    
    # Handle markdown code blocks if present
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
    
    try:
        result = json.loads(response_text)
        
        # Verify and recalculate overall score to ensure correct weighting
        if 'scores' in result:
            scores = result['scores']
            calculated_overall = calculate_overall_score({
                'insight_density': scores['insight_density'],
                'signal_to_noise': scores['signal_to_noise'],
                'actionability': scores['actionability'],
                'contrarian_index': scores['contrarian_index'],
                'freshness': scores['freshness'],
                'host_quality': scores['host_quality']
            })
            result['scores']['overall'] = calculated_overall
        
        # Add metadata
        result['analyzed_at'] = datetime.now().isoformat()
        result['model'] = model
        result['scoring_mode'] = 'hybrid_critical'
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        print(f"Raw response: {response_text[:500]}")
        raise


def analyze_and_save(transcript_path: str, output_path: str = None):
    """
    Analyze a transcript file and save results to JSON.
    
    Args:
        transcript_path: Path to transcript text file
        output_path: Optional path to save results (default: same name with .json extension)
    """
    
    # Read transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    # Analyze
    result = analyze_podcast(transcript)
    
    # Determine output path
    if output_path is None:
        output_path = transcript_path.rsplit('.', 1)[0] + '_analysis_hybrid.json'
    
    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Analysis saved to: {output_path}")
    print(f"\n📊 SCORES:")
    print(f"   Overall: {result['scores']['overall']}/10")
    print(f"   Insight Density: {result['scores']['insight_density']}/10")
    print(f"   Signal-to-Noise: {result['scores']['signal_to_noise']}/10")
    print(f"   Actionability: {result['scores']['actionability']}/10")
    print(f"   Contrarian Index: {result['scores']['contrarian_index']}/10")
    print(f"   Freshness: {result['scores']['freshness']}/10")
    print(f"   Host Quality: {result['scores']['host_quality']}/10")
    print(f"\n💡 VERDICT: {result['verdict']['tldr']}")
    print(f"   Worth it? {result['verdict']['worth_it']}")
    print(f"\n🎯 TOP INSIGHT: {result['top_5_takeaways'][0]['insight']}")
    
    return result


if __name__ == "__main__":
    # Test mode: analyze a sample transcript
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyzer_hybrid.py <transcript_file.txt>")
        sys.exit(1)
    
    analyze_and_save(sys.argv[1])
