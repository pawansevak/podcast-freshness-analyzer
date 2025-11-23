#!/usr/bin/env python3
"""
Batch analyze existing transcript files that don't have analysis yet
Useful after you've transcribed many episodes and want to analyze them all
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

TRANSCRIPTS_DIR = Path("transcripts")


def find_unanalyzed_transcripts():
    """Find .txt transcripts that don't have corresponding *_analysis_hybrid.json"""
    txt_files = list(TRANSCRIPTS_DIR.glob("*.txt"))
    unanalyzed = []
    
    for txt_file in txt_files:
        # Check various analysis file patterns
        base_name = txt_file.stem
        
        possible_analysis_files = [
            TRANSCRIPTS_DIR / f"{base_name}_analysis_hybrid.json",
            TRANSCRIPTS_DIR / f"{base_name}_analysis_v2.json",
            TRANSCRIPTS_DIR / f"{base_name}_analysis_critical.json",
        ]
        
        # If none exist, this transcript needs analysis
        if not any(f.exists() for f in possible_analysis_files):
            unanalyzed.append(txt_file)
    
    return unanalyzed


def analyze_transcript(txt_file: Path) -> bool:
    """Run analyzer on a single transcript"""
    print(f"\n{'='*80}")
    print(f"🧠 Analyzing: {txt_file.name}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, 'analyzer_hybrid.py', str(txt_file)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ Analysis complete")
            return True
        else:
            print(f"❌ Analysis failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  Analysis timed out (>5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    # Check if analyzer exists
    if not Path("analyzer_hybrid.py").exists():
        print("❌ Error: analyzer_hybrid.py not found")
        print("Make sure you're running this from the project root")
        sys.exit(1)
    
    # Find unanalyzed transcripts
    unanalyzed = find_unanalyzed_transcripts()
    
    if not unanalyzed:
        print("✅ All transcripts already analyzed!")
        return
    
    print(f"\n📋 Found {len(unanalyzed)} transcripts to analyze\n")
    
    # Ask for confirmation
    print("Transcripts to analyze:")
    for i, txt_file in enumerate(unanalyzed, 1):
        print(f"  {i}. {txt_file.name}")
    
    response = input(f"\nAnalyze all {len(unanalyzed)} transcripts? (y/n): ")
    if response.lower() not in ['y', 'yes']:
        print("Cancelled")
        return
    
    # Process each transcript
    results = []
    start_time = datetime.now()
    
    for i, txt_file in enumerate(unanalyzed, 1):
        print(f"\n[{i}/{len(unanalyzed)}]")
        success = analyze_transcript(txt_file)
        results.append({'file': txt_file.name, 'success': success})
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    successful = sum(1 for r in results if r['success'])
    
    print(f"\n{'='*80}")
    print(f"📊 Batch Analysis Complete")
    print(f"{'='*80}")
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {len(results) - successful}/{len(results)}")
    print(f"⏱️  Total time: {duration/60:.1f} minutes")
    print(f"⏱️  Average per episode: {duration/len(results):.1f} seconds")
    
    # Show failed ones
    failed = [r for r in results if not r['success']]
    if failed:
        print(f"\n❌ Failed transcripts:")
        for r in failed:
            print(f"  - {r['file']}")
    
    print()


if __name__ == "__main__":
    main()
