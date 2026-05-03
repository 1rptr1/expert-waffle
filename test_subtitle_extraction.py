#!/usr/bin/env python3
"""
Test script for subtitle extraction functionality
"""
import os
import sys
from pipeline.subtitle_extractor import extract_subtitles
from pipeline.parse_srt import parse_srt

def main():
    # Configuration
    video_file = "data/input/The.Gangster.the.Cop.the.Devil.2019.KOREAN.1080p.10bit.BluRay.6CH.sample.mkv"
    srt_file = "data/input/extracted_subtitles.srt"
    output_dir = "data/output"
    temp_dir = "data/temp"
    
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    print("🎬 Testing AI Dubber Subtitle Extraction...")
    
    # Test subtitle extraction
    print("🔍 Step 1: Extracting subtitles...")
    if extract_subtitles(video_file, srt_file, temp_dir):
        print("✅ Subtitle extraction successful!")
        
        # Test parsing the generated SRT
        print("📜 Step 2: Parsing extracted subtitles...")
        if os.path.exists(srt_file):
            subs = parse_srt(srt_file)
            print(f"Found {len(subs)} subtitle entries")
            
            # Show first few entries
            for i, sub in enumerate(subs[:5]):
                print(f"Entry {i+1}: [{sub['start']:.2f}s - {sub['end']:.2f}s] {sub['text']}")
            
            if len(subs) > 5:
                print(f"... and {len(subs) - 5} more entries")
        else:
            print("❌ SRT file was not created")
    else:
        print("❌ Subtitle extraction failed")

if __name__ == "__main__":
    main()
