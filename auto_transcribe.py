#!/usr/bin/env python3
"""
Auto-Transcription Pipeline for Mostly Mid
Downloads YouTube audio → Transcribes with Deepgram → Analyzes with hybrid analyzer
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import requests
from urllib.parse import urlparse, parse_qs

# Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TRANSCRIPTS_DIR = Path("transcripts")
TEMP_DIR = Path("temp_audio")

# Ensure directories exist
TRANSCRIPTS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


def get_youtube_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    parsed = urlparse(url)
    
    if parsed.hostname in ['youtu.be']:
        return parsed.path[1:]
    
    if parsed.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
        if parsed.path == '/watch':
            return parse_qs(parsed.query)['v'][0]
        if parsed.path.startswith('/embed/'):
            return parsed.path.split('/')[2]
        if parsed.path.startswith('/v/'):
            return parsed.path.split('/')[2]
    
    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_video_metadata(video_id: str) -> dict:
    """Get video title and metadata using yt-dlp"""
    try:
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-playlist', f'https://www.youtube.com/watch?v={video_id}'],
            capture_output=True,
            text=True,
            check=True
        )
        metadata = json.loads(result.stdout)
        return {
            'video_id': video_id,
            'title': metadata.get('title', 'Unknown'),
            'channel': metadata.get('channel', 'Unknown'),
            'duration': metadata.get('duration', 0),
            'upload_date': metadata.get('upload_date', ''),
            'description': metadata.get('description', '')
        }
    except Exception as e:
        print(f"Warning: Could not fetch metadata: {e}")
        return {
            'video_id': video_id,
            'title': f'Video_{video_id}',
            'channel': 'Unknown',
            'duration': 0,
            'upload_date': '',
            'description': ''
        }


def download_audio(video_id: str, output_path: Path) -> bool:
    """Download audio from YouTube using yt-dlp"""
    print(f"📥 Downloading audio for {video_id}...")
    
    try:
        # Download as MP3 for better compatibility
        subprocess.run([
            'yt-dlp',
            '-x',  # Extract audio
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # Best quality
            '-o', str(output_path),
            '--no-playlist',
            f'https://www.youtube.com/watch?v={video_id}'
        ], check=True, capture_output=True)
        
        print(f"✅ Audio downloaded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading audio: {e.stderr.decode()}")
        return False


def chunk_audio_if_needed(audio_path: Path, max_size_mb: int = 20) -> list:
    """Split audio into chunks if file is larger than max_size_mb"""
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    
    if file_size_mb <= max_size_mb:
        return [audio_path]
    
    print(f"📦 File is {file_size_mb:.1f}MB (limit: {max_size_mb}MB), splitting into chunks...")
    
    import subprocess
    
    # Calculate optimal chunk duration to keep under 20MB
    # Rough estimate: 90 min podcast = 128MB means ~1.4MB per minute
    # To stay under 20MB: 20MB / 1.4MB/min = ~14 minutes
    # Use 10 minutes to be safe
    chunk_duration = 600  # 10 minutes in seconds
    
    output_pattern = audio_path.parent / f"{audio_path.stem}_chunk_%03d{audio_path.suffix}"
    
    try:
        # Use ffmpeg to split by time
        subprocess.run([
            "ffmpeg",
            "-i", str(audio_path),
            "-f", "segment",
            "-segment_time", str(chunk_duration),
            "-c", "copy",
            "-loglevel", "error",  # Suppress verbose output
            str(output_pattern)
        ], check=True, capture_output=True)
        
        chunks = sorted(audio_path.parent.glob(f"{audio_path.stem}_chunk_*{audio_path.suffix}"))
        print(f"📦 Created {len(chunks)} chunks (~{chunk_duration/60:.0f} min each)")
        
        # Verify chunk sizes
        for i, chunk in enumerate(chunks, 1):
            chunk_size = chunk.stat().st_size / (1024 * 1024)
            print(f"   Chunk {i}: {chunk_size:.1f}MB")
            if chunk_size > 24:  # Still too large
                print(f"   ⚠️  Warning: Chunk {i} is still large, may fail")
        
        return chunks
    except Exception as e:
        print(f"⚠️  Could not chunk file: {e}")
        print(f"   Attempting to transcribe anyway...")
        return [audio_path]


def transcribe_with_whisper_api(audio_path: Path, api_key: str) -> dict:
    """
    Transcribe audio using OpenAI Whisper API
    Automatically handles large files by chunking
    Cost: $0.006 per minute ($0.36 per hour)
    """
    print(f"🎤 Transcribing with OpenAI Whisper API...")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set. Get key at: https://platform.openai.com/api-keys")
    
    try:
        from openai import OpenAI
    except ImportError:
        print("❌ OpenAI library not installed")
        print("Install: pip3 install openai")
        raise
    
    client = OpenAI(api_key=api_key)
    
    # Check file size
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    
    # If file is under 25MB, transcribe directly
    if file_size_mb <= 24:
        print(f"📄 File size: {file_size_mb:.1f}MB (processing as single file)")
        
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        # Convert to dict format
        result = {
            "text": response.text,
            "segments": [],
            "metadata": {
                "model": "whisper-1",
                "service": "openai"
            }
        }
        
        # Add segments if available
        if hasattr(response, 'segments') and response.segments:
            result["segments"] = [
                {
                    "text": seg.text,
                    "start": seg.start,
                    "end": seg.end
                } for seg in response.segments
            ]
        
        print(f"✅ Transcription complete")
        return result
    
    # File is too large, need to chunk
    print(f"📦 File is {file_size_mb:.1f}MB (limit: 25MB), splitting into chunks...")
    
    chunks = chunk_audio_if_needed(audio_path, max_size_mb=20)
    
    all_text = []
    all_segments = []
    offset = 0.0
    
    for i, chunk_path in enumerate(chunks, 1):
        print(f"🎤 Transcribing chunk {i}/{len(chunks)}...")
        
        with open(chunk_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        all_text.append(response.text)
        
        # Adjust segment timestamps with offset
        if hasattr(response, 'segments') and response.segments:
            for seg in response.segments:
                all_segments.append({
                    "text": seg.text,
                    "start": seg.start + offset,
                    "end": seg.end + offset
                })
            
            # Update offset for next chunk
            if response.segments:
                offset = all_segments[-1]["end"]
        
        print(f"✅ Chunk {i}/{len(chunks)} complete")
        
        # Clean up chunk file (keep original)
        if len(chunks) > 1 and chunk_path != audio_path:
            chunk_path.unlink()
    
    # Estimate cost
    duration_minutes = file_size_mb * 0.7  # Rough estimate: 1MB ≈ 0.7 min
    cost = duration_minutes * 0.006
    print(f"💰 Estimated cost: ${cost:.2f} ({duration_minutes:.0f} minutes)")
    print(f"✅ Transcription complete")
    
    return {
        "text": " ".join(all_text),
        "segments": all_segments,
        "metadata": {
            "model": "whisper-1",
            "service": "openai",
            "chunks": len(chunks),
            "estimated_cost": cost
        }
    }


def format_transcript(response: dict) -> str:
    """Convert transcription response to readable transcript"""
    if not response:
        return ""
    
    # Handle Groq/Whisper format (segments with text)
    if "segments" in response and response["segments"]:
        lines = []
        for segment in response["segments"]:
            text = segment.get("text", "").strip()
            if text:
                lines.append(text)
        
        if lines:
            return "\n\n".join(lines)
    
    # Fallback to plain text
    return response.get("text", "")


def save_transcript(video_id: str, metadata: dict, transcript: str, transcription_response: dict):
    """Save transcript and metadata to files"""
    # Clean filename
    safe_title = "".join(c for c in metadata['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
    
    base_filename = f"{video_id}_{safe_title}"
    
    # Save transcript as .txt
    transcript_path = TRANSCRIPTS_DIR / f"{base_filename}.txt"
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(f"Title: {metadata['title']}\n")
        f.write(f"Channel: {metadata['channel']}\n")
        f.write(f"Duration: {metadata['duration']} seconds\n")
        f.write(f"URL: https://www.youtube.com/watch?v={video_id}\n")
        f.write(f"Transcribed: {datetime.now().isoformat()}\n")
        f.write(f"Service: OpenAI Whisper API\n")
        
        # Add cost info if available
        if 'metadata' in transcription_response and 'estimated_cost' in transcription_response['metadata']:
            cost = transcription_response['metadata']['estimated_cost']
            f.write(f"Cost: ${cost:.2f}\n")
        
        f.write("\n" + "="*80 + "\n\n")
        f.write(transcript)
    
    # Save full Whisper response for future reference
    whisper_path = TRANSCRIPTS_DIR / f"{base_filename}_whisper.json"
    with open(whisper_path, 'w', encoding='utf-8') as f:
        json.dump(transcription_response, f, indent=2)
    
    # Save metadata
    metadata_path = TRANSCRIPTS_DIR / f"{base_filename}_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 Saved transcript to: {transcript_path}")
    return transcript_path, base_filename


def run_analysis(transcript_path: Path, base_filename: str):
    """Run the hybrid analyzer on the transcript"""
    print(f"🧠 Running hybrid analyzer...")
    
    try:
        # Check if analyzer exists
        if not Path("analyzer_hybrid.py").exists():
            print("⚠️  analyzer_hybrid.py not found, skipping analysis")
            return False
        
        result = subprocess.run([
            sys.executable,
            'analyzer_hybrid.py',
            str(transcript_path)
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ Analysis complete")
            analysis_file = TRANSCRIPTS_DIR / f"{base_filename}_analysis_hybrid.json"
            if analysis_file.exists():
                print(f"💾 Analysis saved to: {analysis_file}")
                return True
            else:
                print("⚠️  Analysis completed but file not found")
                return False
        else:
            print(f"⚠️  Analysis failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Analysis timed out (>5 minutes)")
        return False
    except Exception as e:
        print(f"⚠️  Error running analysis: {e}")
        return False


def process_youtube_url(youtube_url: str, skip_analysis: bool = False) -> bool:
    """Main pipeline: download → transcribe → analyze"""
    
    print(f"\n{'='*80}")
    print(f"🎬 Processing: {youtube_url}")
    print(f"{'='*80}\n")
    
    try:
        # Step 1: Extract video ID
        video_id = get_youtube_id(youtube_url)
        print(f"📹 Video ID: {video_id}")
        
        # Step 2: Get metadata
        metadata = get_video_metadata(video_id)
        print(f"📝 Title: {metadata['title']}")
        print(f"👤 Channel: {metadata['channel']}")
        print(f"⏱️  Duration: {metadata['duration']/60:.1f} minutes")
        
        # Step 3: Download audio
        audio_path = TEMP_DIR / f"{video_id}.mp3"
        if not download_audio(video_id, audio_path):
            return False
        
        # Step 4: Transcribe
        whisper_response = transcribe_with_whisper_api(audio_path, OPENAI_API_KEY)
        if not whisper_response:
            return False
        
        transcript = format_transcript(whisper_response)
        
        if not transcript:
            print("❌ Failed to extract transcript from Deepgram response")
            return False
        
        print(f"📄 Transcript length: {len(transcript)} characters")
        
        # Step 5: Save transcript
        transcript_path, base_filename = save_transcript(
            video_id, metadata, transcript, whisper_response
        )
        
        # Step 6: Run analysis (optional)
        if not skip_analysis:
            run_analysis(transcript_path, base_filename)
        else:
            print("⏭️  Skipping analysis (use --analyze flag to enable)")
        
        # Cleanup
        if audio_path.exists():
            audio_path.unlink()
            print(f"🗑️  Cleaned up temp audio file")
        
        print(f"\n✅ Successfully processed: {metadata['title']}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error processing video: {e}")
        import traceback
        traceback.print_exc()
        return False


def batch_process(urls_file: Path, skip_analysis: bool = False):
    """Process multiple URLs from a file"""
    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"\n🎯 Processing {len(urls)} videos...\n")
    
    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] {url}")
        success = process_youtube_url(url, skip_analysis)
        results.append({'url': url, 'success': success})
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    print(f"\n{'='*80}")
    print(f"📊 Batch Results: {successful}/{len(urls)} successful")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-transcribe YouTube podcasts')
    parser.add_argument('url', nargs='?', help='YouTube URL to process')
    parser.add_argument('--batch', type=Path, help='Process URLs from file (one per line)')
    parser.add_argument('--analyze', action='store_true', help='Run hybrid analyzer after transcription')
    parser.add_argument('--skip-analysis', action='store_true', help='Skip analysis (transcribe only)')
    
    args = parser.parse_args()
    
    # Check dependencies
    if not OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Get your API key from: https://platform.openai.com/api-keys")
        print("Add credit: https://platform.openai.com/settings/organization/billing")
        sys.exit(1)
    
    if args.batch:
        batch_process(args.batch, skip_analysis=not args.analyze)
    elif args.url:
        process_youtube_url(args.url, skip_analysis=not args.analyze)
    else:
        parser.print_help()
        sys.exit(1)
