#!/usr/bin/env python3
"""Add hand-crafted judgment scenarios to top insights from each episode."""

import json
from pathlib import Path

# Hand-crafted judgment scenarios for top insights (rank 1 from each episode)
# Keys are unique substrings that appear in the insight text
JUDGMENT_SCENARIOS = {
    # Intercom - Eoghan McCabe
    "Intercom rewrote company values specifically as 'a sharp knife": {
        "scenario": "Your company culture has drifted and performance is declining. How do you address it?",
        "optionA": "Rewrite company values and use them as a strict hiring/firing rubric with mathematical precision",
        "optionB": "Run workshops and training to gradually shift culture over 12-18 months",
        "correctOption": "A",
        "reasoning": "Eoghan McCabe took the 'sharp knife' approach - using values as an actual firing mechanism. He argues that gradual culture change is too slow when competing with AI-native startups working 12 hours a day."
    },
    
    # Notion - Steve Jobs missed the real innovation
    "Steve Jobs missed the real innovation at Xerox PARC": {
        "scenario": "You're designing a new productivity tool. What's your core design philosophy?",
        "optionA": "Create polished, opinionated features that work well out of the box",
        "optionB": "Build malleable primitives that users can modify and combine themselves",
        "correctOption": "B",
        "reasoning": "Notion's founder argues that Jobs took the wrong lesson from Xerox PARC - he copied the GUI but missed SmallTalk's malleability. Notion's success comes from letting users build their own tools."
    },
    
    # Dan Shipper - AI Operations
    "Hire a dedicated 'Head of AI Operations'": {
        "scenario": "How should you structure your team to leverage AI for productivity?",
        "optionA": "Train all employees on AI tools and let them adopt organically",
        "optionB": "Hire a dedicated person whose only job is finding and automating repetitive tasks with AI",
        "correctOption": "B",
        "reasoning": "Dan Shipper's insight: A dedicated AI Operations role can systematically identify automation opportunities across the company. This person hunts for repetitive tasks and builds AI solutions, multiplying everyone's productivity."
    },
    
    # Snowflake CEO - PageRank died
    "PageRank died in 2004-2005": {
        "scenario": "You're building an AI product. Where should you invest for long-term moat?",
        "optionA": "Better models and algorithms",
        "optionB": "User behavior data and feedback loops",
        "correctOption": "B",
        "reasoning": "The Snowflake CEO reveals that Google's algorithm wasn't their moat - the click behavior data was. Similarly, AI products should focus on building feedback loops, not just better models."
    },
    
    # monday.com - Column velocity
    "competitors launched 30 new column types while Monday took 4 months per column": {
        "scenario": "Your team is shipping slowly compared to competitors. What's your approach?",
        "optionA": "Focus on quality and keep your careful, thorough process",
        "optionB": "Set aggressive shipping velocity targets and restructure to match competitor speed",
        "correctOption": "B",
        "reasoning": "Monday.com realized they needed to match competitor velocity. They set a goal of 2-3 columns per month and restructured their entire approach. Sometimes you need to match the pace of competition, not just beat them on quality."
    },
    
    # Devin / Scott Wu
    "Cognition's 15-person engineering team has Devon merge": {
        "scenario": "How should you structure engineering to leverage AI coding agents?",
        "optionA": "Use AI as a coding assistant that engineers supervise in real-time",
        "optionB": "Assign multiple AI agents tasks asynchronously while engineers context-switch between them",
        "correctOption": "B",
        "reasoning": "Scott Wu's team works with multiple AI agents simultaneously per engineer. The key insight: treat AI as async team members, not real-time assistants. This multiplies throughput - 25% of their PRs now come from AI."
    },
    
    # Kevin Weil / OpenAI - Ensembles
    "OpenAI uses ensembles of different models internally": {
        "scenario": "You're building an AI-powered product. How do you approach model selection?",
        "optionA": "Use the best single model for everything",
        "optionB": "Use different models for different tasks and combine them strategically",
        "correctOption": "B",
        "reasoning": "Kevin Weil reveals OpenAI uses ensembles internally - different model sizes, fine-tuned versions, and reasoning models for different purposes. The best results come from orchestrating multiple models, not just using one."
    },
    
    # Yelp AI PM - Golden conversations
    "Start AI product development with 'golden conversations'": {
        "scenario": "You're starting a new AI feature. Where do you begin?",
        "optionA": "Design the UI wireframes and user flows first",
        "optionB": "Write out ideal example conversations between user and AI first",
        "correctOption": "B",
        "reasoning": "The Yelp PM's approach: write complete example dialogues before any other work. These 'golden conversations' become your spec - work backwards to system prompts and UI from there."
    },
    
    # Bret Taylor - Python comically bad
    "Python is 'comically bad' for AI to generate": {
        "scenario": "You're designing a programming interface for AI agents. What do you prioritize?",
        "optionA": "Use popular languages like Python for ecosystem compatibility",
        "optionB": "Design for machine verification and type safety over human readability",
        "correctOption": "B",
        "reasoning": "Bret Taylor argues we need programming systems designed for AI-generated code that prioritize compile-time verification over human readability. Python's whitespace-significance is particularly problematic for AI."
    },
    
    # AI Evals - Hamel & Shreya - Open coding
    "Start evals with manual 'open coding' error analysis": {
        "scenario": "Your AI product is making errors. How do you analyze them?",
        "optionA": "Build automated evaluation pipelines to catch errors at scale",
        "optionB": "Manually review 100+ traces and write notes before automating anything",
        "correctOption": "B",
        "reasoning": "Hamel and Shreya argue that LLMs cannot effectively identify product-context errors. Start with manual 'open coding' from qualitative research - look at real traces and understand patterns before building automation."
    },
    
    # ChatGPT / Nick Turley - $20 pricing
    "ChatGPT's $20 pricing came from a desperate Google Form survey": {
        "scenario": "You're launching an AI product tomorrow but haven't validated pricing. What do you do?",
        "optionA": "Delay launch by 2 weeks to run comprehensive pricing research",
        "optionB": "Quick survey to early users tonight and launch with your best guess",
        "correctOption": "B",
        "reasoning": "OpenAI set ChatGPT's $20 price with a hasty survey sent to Discord users the night before launch. Sometimes speed beats perfection - this became the most copied pricing in AI history."
    },
    
    # monday.com AI PM - Scraping
    "Use Claude to write step-by-step Python scraping scripts": {
        "scenario": "You need customer insights but don't have engineering resources. What do you do?",
        "optionA": "Wait for engineering to build a proper data pipeline",
        "optionB": "Use AI to write scraping scripts yourself, even as a non-technical PM",
        "correctOption": "B",
        "reasoning": "The monday.com PM used Claude to write Python scraping scripts, gathering 34,000 Reddit posts for customer insights. AI enables non-technical PMs to do technical work - don't wait for engineering."
    },
    
    # Gamma / Grant Lee - Product Hunt trap
    "Winning Product Hunt can be a vanity metric trap": {
        "scenario": "Your product just won Product Hunt Product of the Day. What's your next move?",
        "optionA": "Double down on the momentum - launch more products on PH, focus on viral growth",
        "optionB": "Recognize it as validation but rebuild fundamentals like onboarding that drive sustainable growth",
        "correctOption": "B",
        "reasoning": "Grant Lee won PH Product of Day/Week/Month but recognized it wasn't sustainable growth. They made a 'bet the company' decision to completely rebuild onboarding instead of chasing more viral wins."
    },
    
    # SEO / Eli Schwartz - Keyword research wrong
    "Keyword research tools are wrong by factors of 10x": {
        "scenario": "You're planning SEO strategy. How do you approach keyword research?",
        "optionA": "Use industry-standard keyword research tools to identify opportunities",
        "optionB": "Treat keyword tools as directionally useful but wildly inaccurate, validate with real traffic data",
        "correctOption": "B",
        "reasoning": "Eli Schwartz reveals keyword tools are guessing because Google can't legally share real data. They can be off by 10x. Use them for direction, but validate opportunities with actual traffic experiments."
    },
    
    # Uber CPO / Sachin Kansal - Dogfooding OKRs
    "Uber sets OKRs to fix 300 'dogfooding issues' per team every 6 months": {
        "scenario": "How do you ensure product teams stay connected to user pain points?",
        "optionA": "Regular user research sessions and feedback reviews",
        "optionB": "Set OKRs requiring each team to personally use the product and fix a quota of issues they find",
        "correctOption": "B",
        "reasoning": "Uber's CPO mandates dogfooding with teeth - 300 issues per team every 6 months as an OKR. This makes user experience improvement systematic rather than optional, building empathy through direct experience."
    }
}


def add_judgments():
    """Add judgment scenarios to the insights JSON."""
    
    input_file = Path("productreps_insights.json")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    added_count = 0
    
    for insight in data["insights"]:
        # Only add to rank 1 insights (top insight from each episode)
        if insight["rank"] != 1:
            continue
            
        # Check if this insight matches any of our scenarios
        for key_phrase, judgment in JUDGMENT_SCENARIOS.items():
            if key_phrase in insight["insight"]:
                insight["judgment"] = judgment
                added_count += 1
                print(f"✓ Added judgment for: {insight['guest'][:30]} - {key_phrase[:40]}...")
                break
    
    # Save the updated file
    with open(input_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Added {added_count} judgment scenarios to top insights")
    print(f"✓ Saved to {input_file}")


if __name__ == "__main__":
    add_judgments()
