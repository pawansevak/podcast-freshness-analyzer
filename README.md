# 🎙️ Podcast Analyzer MVP

A web application that analyzes podcast transcripts and scores them on "freshness" (how current the content is) and "insights" (how non-obvious and valuable the insights are). It also highlights the most valuable segments worth listening to.

## Features

✅ **Freshness Scoring (1-10)**: Evaluates how recent, timely, and cutting-edge the information is
✅ **Insight Scoring (1-10)**: Measures how non-obvious, specific, and valuable the insights are  
✅ **Top 3 Highlights**: Identifies the most valuable segments to listen to
✅ **Content Characteristics**: Flags whether content has specific data, examples, novel frameworks, etc.
✅ **Personalization Ready**: User preferences system for customized analysis
✅ **Feedback Loop**: Users can rate analyses to improve future personalization

## Project Structure

```
podcast-analyzer/
├── app.py                      # FastAPI backend server
├── analyzer.py                 # Core analysis logic with LLM
├── transcripts/                # Podcast transcript files
│   ├── podcast_1.txt
│   ├── podcast_2.txt
│   └── podcast_3.txt
├── transcripts_metadata.json   # Podcast metadata (title, duration, etc.)
├── users/                      # User preferences and ratings
│   └── default_preferences.json
├── cache/                      # Cached analysis results
├── static/
│   └── index.html             # Frontend web interface
└── requirements.txt           # Python dependencies
```

## Quick Start

### 1. Install Dependencies

```bash
cd podcast-analyzer
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The server will start on `http://localhost:8000`

### 3. Use the Web Interface

1. Open `http://localhost:8000` in your browser
2. Select a podcast from the dropdown
3. Click "Analyze Podcast"
4. View the freshness/insight scores and highlights
5. Optionally submit feedback

## How It Works

### Analysis Pipeline

1. **Transcript Loading**: Reads transcript from the `/transcripts` folder
2. **User Preferences**: Loads user preferences (topics of interest, insight style, etc.)
3. **LLM Analysis**: Sends transcript + preferences to Claude API for analysis
4. **Scoring**: Receives freshness score, insight score, and highlights
5. **Caching**: Saves results to avoid re-analyzing the same content
6. **Display**: Shows results in the web interface

### Scoring Criteria

**Freshness Score:**
- 1-3: Outdated or generic timeless content
- 4-6: Somewhat current
- 7-8: Recent information (last 6-12 months)
- 9-10: Very recent, cutting-edge topics

**Insight Score:**
- 1-3: Generic advice, platitudes, no specifics
- 4-6: Moderately interesting
- 7-8: Counter-intuitive, novel frameworks, specific data
- 9-10: Highly novel, surprising data, actionable insights

## API Endpoints

### `GET /api/podcasts`
Returns list of available podcasts

### `GET /api/analyze/{podcast_id}?user_id=default`
Analyzes a podcast and returns scores + highlights

**Response:**
```json
{
  "freshness_score": 8,
  "freshness_reasoning": "...",
  "insight_score": 7,
  "insight_reasoning": "...",
  "highlights": [
    {"segment": "...", "value": "..."},
    ...
  ],
  "key_characteristics": {
    "has_specific_data": true,
    "has_concrete_examples": true,
    "has_novel_frameworks": true,
    "has_contrarian_takes": false,
    "has_actionable_advice": true
  },
  "summary": "...",
  "cached": false
}
```

### `GET /api/preferences/{user_id}`
Gets user preferences

### `POST /api/preferences/{user_id}`
Updates user preferences

### `POST /api/rating`
Submits user rating and feedback

## Adding Your Own Transcripts

1. Add transcript file to `/transcripts/` folder (e.g., `podcast_4.txt`)
2. Update `transcripts_metadata.json`:

```json
{
  "podcast_4": {
    "title": "Your Podcast Title",
    "duration": "45:30",
    "date": "2024-11-10",
    "topics": ["topic1", "topic2"]
  }
}
```

3. Refresh the web interface

## Connecting to Real Claude API

The current version uses simulated analysis for demo purposes. To connect to the real Claude API:

1. Get an API key from https://console.anthropic.com/
2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

3. In `analyzer.py`, uncomment the real API code:
   ```python
   import anthropic
   client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
   message = client.messages.create(
       model="claude-sonnet-4-20250514",
       max_tokens=2000,
       messages=[{"role": "user", "content": prompt}]
   )
   response_text = message.content[0].text
   ```

4. Remove or comment out the `simulate_analysis()` call

## Personalization System

### Setting User Preferences

Users can set preferences in `users/{user_id}_preferences.json`:

```json
{
  "topics_of_interest": ["AI", "Technology", "Science"],
  "freshness_priority": "high",
  "insight_style": "data-driven",
  "avoid_topics": ["politics", "sports"]
}
```

These preferences are included in the analysis prompt to personalize scoring.

### Learning from Feedback

When users rate analyses, the system stores:
- Which podcasts they rated highly
- Which segments they found valuable
- Their feedback comments

This data can be used to:
1. Include examples in future prompts (few-shot learning)
2. Build a taste profile over time
3. Fine-tune models (with sufficient data)

## Next Steps / Roadmap

### Phase 1: YouTube Integration
- [ ] Add YouTube URL input
- [ ] Extract audio with `yt-dlp`
- [ ] Transcribe with Whisper API
- [ ] Store transcripts automatically

### Phase 2: Enhanced Personalization
- [ ] Onboarding quiz to capture initial preferences
- [ ] Use past ratings in analysis prompts (few-shot)
- [ ] Generate natural language "taste profile"
- [ ] Show why analysis matches user's taste

### Phase 3: Advanced Features
- [ ] Timestamp extraction for highlights
- [ ] Direct links to YouTube moments
- [ ] User clustering (find similar taste)
- [ ] "People with similar taste also liked..."
- [ ] Export analysis reports

### Phase 4: Production Ready
- [ ] User authentication
- [ ] Database instead of file storage
- [ ] Job queue for long-running analyses
- [ ] Rate limiting and caching strategy
- [ ] Analytics dashboard

## Sample Transcripts Included

The MVP includes 3 sample transcripts:

1. **podcast_1**: Tech/AI focused (high freshness, high insights)
2. **podcast_2**: Generic productivity (low freshness, low insights)
3. **podcast_3**: Science research (high freshness, high insights)

These demonstrate how the analyzer distinguishes between high-quality, data-driven content vs. generic advice.

## Technology Stack

- **Backend**: Python, FastAPI
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **LLM**: Anthropic Claude API (or simulated)
- **Storage**: File-based (JSON) for MVP

## Cost Considerations

If using real Claude API:
- ~2-3 cents per podcast analysis (depending on length)
- Cache aggressively to avoid re-analyzing
- Consider using smaller models for initial filtering

## Development Tips

**Testing the analyzer directly:**
```bash
python analyzer.py
```

**Running tests on different transcripts:**
```python
from analyzer import analyze_podcast, load_transcript
transcript = load_transcript("podcast_1")
result = analyze_podcast(transcript)
print(result)
```

**Clearing cache:**
```bash
rm -rf cache/*
```

## Contributing

To extend this MVP:
1. Add more sophisticated NLP analysis
2. Implement actual YouTube integration
3. Build user authentication
4. Add database support
5. Create more advanced personalization algorithms

## License

MIT License - feel free to use and modify for your projects!

---

Built with ❤️ using Claude AI and FastAPI
