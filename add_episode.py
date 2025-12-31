#!/usr/bin/env python3
"""
ProductReps Episode Adder - Interactive script to add new podcast episodes

Usage:
    python add_episode.py                    # Interactive mode
    python add_episode.py --batch file.txt  # Batch mode with transcript file
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Category definitions
CATEGORIES = {
    "1": ("learn_from_legends", "🏆 Learn from Legends - Product craft, strategy, career wisdom"),
    "2": ("build_ai_products", "🤖 Build AI Products - Building AI features, AI product management"),
    "3": ("speak_ai_fluently", "🧠 Speak AI Fluently - Understanding AI/ML technology"),
    "4": ("ai_superpowers", "⚡ AI Superpowers - Using AI tools to work better"),
}

# Common podcasts (for quick selection)
PODCASTS = {
    "1": "Lenny's Podcast",
    "2": "Latent Space",
    "3": "My First Million",
    "4": "Acquired",
    "5": "The Knowledge Project",
    "6": "Practical AI",
    "7": "Machine Learning Street Talk",
    "8": "The AI Advantage",
    "9": "How I Built This",
    "0": "Other (enter custom)",
}

TRANSCRIPTS_DIR = Path("transcripts")


def slugify(text: str) -> str:
    """Convert text to a safe filename slug."""
    # Replace spaces and special chars
    slug = text.lower()
    slug = slug.replace("'", "")
    slug = slug.replace("'", "")
    slug = slug.replace('"', "")
    slug = slug.replace(":", "")
    slug = slug.replace(",", "")
    slug = slug.replace(".", "")
    slug = slug.replace("-", "_")
    slug = slug.replace(" ", "_")
    # Remove multiple underscores
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def get_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default."""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def select_category() -> str:
    """Interactive category selection."""
    print("\n📁 Select category:")
    for key, (code, desc) in CATEGORIES.items():
        print(f"   {key}. {desc}")
    
    choice = get_input("\nEnter number", "1")
    if choice in CATEGORIES:
        return CATEGORIES[choice][0]
    return "learn_from_legends"


def select_podcast() -> str:
    """Interactive podcast selection."""
    print("\n🎙️ Select podcast:")
    for key, name in PODCASTS.items():
        print(f"   {key}. {name}")
    
    choice = get_input("\nEnter number", "1")
    if choice == "0":
        return get_input("Enter podcast name")
    if choice in PODCASTS:
        return PODCASTS[choice]
    return PODCASTS["1"]


def create_transcript_file(
    podcast: str,
    episode: str,
    guest: str,
    category: str,
    date: str = None,
    url: str = None,
    transcript_content: str = None
) -> Path:
    """
    Create a new transcript file with metadata header.
    
    Returns:
        Path to the created file
    """
    # Ensure transcripts directory exists
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    
    # Generate filename
    guest_slug = slugify(guest)
    episode_slug = slugify(episode)[:30]  # Limit length
    filename = f"{guest_slug}_{episode_slug}.txt"
    filepath = TRANSCRIPTS_DIR / filename
    
    # Handle duplicate filenames
    counter = 1
    while filepath.exists():
        filename = f"{guest_slug}_{episode_slug}_{counter}.txt"
        filepath = TRANSCRIPTS_DIR / filename
        counter += 1
    
    # Build header
    header_lines = [
        "---",
        f"podcast: {podcast}",
        f"episode: {episode}",
        f"guest: {guest}",
        f"category: {category}",
    ]
    
    if date:
        header_lines.append(f"date: {date}")
    else:
        header_lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
    
    if url:
        header_lines.append(f"url: {url}")
    
    header_lines.append("---")
    header_lines.append("")
    
    if transcript_content:
        header_lines.append(transcript_content)
    else:
        header_lines.append("[PASTE TRANSCRIPT CONTENT BELOW THIS LINE]")
        header_lines.append("")
    
    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(header_lines))
    
    return filepath


def interactive_add():
    """Interactive mode to add a new episode."""
    print("\n" + "="*50)
    print("📝 ADD NEW PODCAST EPISODE")
    print("="*50)
    
    # Collect metadata
    podcast = select_podcast()
    guest = get_input("\n👤 Guest name")
    episode = get_input("📺 Episode title", f"Interview with {guest}")
    category = select_category()
    date = get_input("\n📅 Episode date (YYYY-MM-DD)", datetime.now().strftime('%Y-%m-%d'))
    url = get_input("🔗 Episode URL (optional)", "")
    
    # Create file
    filepath = create_transcript_file(
        podcast=podcast,
        episode=episode,
        guest=guest,
        category=category,
        date=date,
        url=url if url else None
    )
    
    print("\n" + "="*50)
    print(f"✅ Created: {filepath}")
    print("="*50)
    print("\n📋 NEXT STEPS:")
    print(f"   1. Open {filepath}")
    print("   2. Paste the transcript content")
    print("   3. Run: python analyzer_hybrid.py " + str(filepath))
    print("   4. Review the generated analysis JSON")
    print("   5. Run: python generate_productreps_data.py")
    print("\n")
    
    return filepath


def batch_add(transcript_file: str):
    """Add episode from a file with metadata prompts."""
    print(f"\n📄 Reading transcript from: {transcript_file}")
    
    with open(transcript_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already has header
    if content.strip().startswith('---'):
        print("   ✓ File already has metadata header")
        # Just copy to transcripts folder
        filename = os.path.basename(transcript_file)
        dest = TRANSCRIPTS_DIR / filename
        
        if not dest.exists():
            TRANSCRIPTS_DIR.mkdir(exist_ok=True)
            with open(dest, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✓ Copied to: {dest}")
        else:
            print(f"   ⚠️  File already exists: {dest}")
        
        return dest
    
    # Need to add header - collect metadata interactively
    print("   ⚠️  No metadata header found. Please provide episode details:\n")
    
    podcast = select_podcast()
    guest = get_input("\n👤 Guest name")
    episode = get_input("📺 Episode title", f"Interview with {guest}")
    category = select_category()
    
    # Create file with content
    filepath = create_transcript_file(
        podcast=podcast,
        episode=episode,
        guest=guest,
        category=category,
        transcript_content=content
    )
    
    print(f"\n✅ Created: {filepath}")
    print(f"\n🚀 Run: python analyzer_hybrid.py {filepath}")
    
    return filepath


def show_status():
    """Show current transcripts and their analysis status."""
    print("\n📊 TRANSCRIPT STATUS")
    print("="*60)
    
    if not TRANSCRIPTS_DIR.exists():
        print("   No transcripts directory found.")
        return
    
    txt_files = list(TRANSCRIPTS_DIR.glob("*.txt"))
    json_files = {f.stem.replace('_analysis_hybrid', '') for f in TRANSCRIPTS_DIR.glob("*_analysis_hybrid.json")}
    
    analyzed = []
    pending = []
    
    for txt in txt_files:
        stem = txt.stem
        if stem in json_files:
            analyzed.append(txt.name)
        else:
            pending.append(txt.name)
    
    print(f"\n✅ ANALYZED ({len(analyzed)}):")
    for name in sorted(analyzed)[:10]:
        print(f"   • {name}")
    if len(analyzed) > 10:
        print(f"   ... and {len(analyzed) - 10} more")
    
    print(f"\n⏳ PENDING ({len(pending)}):")
    for name in sorted(pending):
        print(f"   • {name}")
    
    if pending:
        print(f"\n💡 To analyze pending files:")
        print(f"   python analyzer_hybrid.py transcripts/{pending[0]}")
    
    print()


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            show_status()
        elif sys.argv[1] == "--batch" and len(sys.argv) > 2:
            batch_add(sys.argv[2])
        elif os.path.isfile(sys.argv[1]):
            batch_add(sys.argv[1])
        else:
            print(f"Unknown option or file not found: {sys.argv[1]}")
            print("\nUsage:")
            print("  python add_episode.py            # Interactive mode")
            print("  python add_episode.py file.txt   # Add from file")
            print("  python add_episode.py --status   # Show status")
    else:
        interactive_add()


if __name__ == "__main__":
    main()

