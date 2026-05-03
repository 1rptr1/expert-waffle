#!/usr/bin/env python3
"""
Complete AI Dubber pipeline demo using mock TTS
"""
import os
import sys
from pipeline.subtitle_extractor import extract_subtitles
from pipeline.parse_srt import parse_srt
from pipeline.translate import translate_text
from pipeline.mock_tts import generate_audio
from pipeline.extract_audio import extract_audio
from pipeline.mixer import mix_audio
from pipeline.render import render_video

def main():
    # Configuration
    video_file = "data/input/The.Gangster.the.Cop.the.Devil.2019.KOREAN.1080p.10bit.BluRay.6CH.sample.mkv"
    srt_file = "data/input/extracted_subtitles.srt"
    output_dir = "data/output"
    temp_dir = "data/temp"
    
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    print("🎬 Starting Complete AI Dubbing Pipeline Demo...")
    
    # Step 0: Extract subtitles (already done, but include for completeness)
    if not os.path.exists(srt_file):
        print("🔍 Step 0: Extracting subtitles...")
        if not extract_subtitles(video_file, srt_file, temp_dir):
            print("❌ Could not extract subtitles")
            return
    else:
        print("✅ Using existing extracted subtitles")
    
    # Step 1: Extract audio from video
    print("⚙️ Step 1: Extracting audio...")
    original_audio = os.path.join(temp_dir, "original_audio.wav")
    extract_audio(video_file, original_audio)
    print(f"✅ Audio extracted to: {original_audio}")
    
    # Step 2: Parse subtitles
    print("📜 Step 2: Parsing subtitles...")
    subs = parse_srt(srt_file)
    print(f"Found {len(subs)} subtitle entries")
    
    # Step 3 & 4: Translate and generate voice for each subtitle
    print("🌍🎙️ Steps 3 & 4: Translating and generating voice...")
    voice_files = []
    
    for i, line in enumerate(subs):
        print(f"Processing line {i+1}/{len(subs)}: {line['text'][:50]}...")
        
        # Translate text (keeping as English for demo since already in English)
        translated = translate_text(line["text"], target="en")
        
        # Generate voice audio (using mock TTS)
        voice_file = os.path.join(temp_dir, f"voice_{i}.wav")
        generate_audio(translated, voice_file)
        voice_files.append({
            "file": voice_file,
            "start": line["start"],
            "end": line["end"]
        })
    
    # Step 5: Create combined voice track
    print("🎚️ Step 5: Mixing audio...")
    if voice_files:
        # Create a simple concatenation of all voice files
        combined_voice = os.path.join(temp_dir, "combined_voice.wav")
        voice_list_file = os.path.join(temp_dir, "voice_list.txt")
        
        with open(voice_list_file, "w") as f:
            for voice_info in voice_files:
                f.write(f"file '{voice_info['file']}'\n")
        
        # Concatenate all voice files
        os.system(f"ffmpeg -y -f concat -safe 0 -i {voice_list_file} -c copy {combined_voice}")
        
        # Mix with original audio
        mixed_audio = os.path.join(temp_dir, "mixed_audio.wav")
        mix_audio(original_audio, combined_voice, mixed_audio)
        print(f"✅ Audio mixed to: {mixed_audio}")
    else:
        print("⚠️ No voice files generated. Using original audio only.")
        mixed_audio = original_audio
    
    # Step 6: Render final video
    print("🎬 Step 6: Rendering final video...")
    output_video = os.path.join(output_dir, "dubbed_video_demo.mp4")
    render_video(video_file, mixed_audio, output_video)
    
    print(f"🎉 Complete! Demo dubbed video saved to: {output_video}")
    
    # Show file sizes
    if os.path.exists(output_video):
        size_mb = os.path.getsize(output_video) / (1024 * 1024)
        print(f"📊 Output video size: {size_mb:.2f} MB")

if __name__ == "__main__":
    main()
