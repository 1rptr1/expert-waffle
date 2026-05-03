import os
import sys
from pipeline.subtitle_extractor import extract_subtitles
from pipeline.parse_srt import parse_srt
from pipeline.translate import translate_text
from pipeline.real_tts import generate_audio
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
    
    print("🎬 Starting AI Dubbing Pipeline...")
    
    # Step 0: Extract subtitles (handles embedded, hardcoded, or no subtitles)
    print("🔍 Step 0: Extracting subtitles...")
    if not os.path.exists(srt_file):
        print("No SRT file found, attempting to extract subtitles from video...")
        if not extract_subtitles(video_file, srt_file, temp_dir):
            print("⚠️ Could not extract subtitles. Continuing without translation...")
            subs = []
        else:
            print("✅ Subtitles extracted successfully")
    else:
        print("✅ Using existing SRT file")
    
    # Step 1: Extract audio from video
    print("⚙️ Step 1: Extracting audio...")
    original_audio = os.path.join(temp_dir, "original_audio.wav")
    extract_audio(video_file, original_audio)
    
    # Step 2: Parse subtitles
    print("📜 Step 2: Parsing subtitles...")
    if os.path.exists(srt_file):
        subs = parse_srt(srt_file)
        print(f"Found {len(subs)} subtitle entries")
    else:
        subs = []
        print("No subtitles available for translation")
    
    # Step 3 & 4: Translate and generate voice for each subtitle
    print("🌍🎙️ Steps 3 & 4: Translating and generating voice...")
    voice_files = []
    
    if subs:
        for i, line in enumerate(subs):
            print(f"Processing line {i+1}/{len(subs)}: {line['text'][:50]}...")
            
            # Translate text to Hindi
            translated = translate_text(line["text"], target="hi")
            
            # Generate Hindi voice audio
            voice_file = os.path.join(temp_dir, f"voice_{i}.wav")
            generate_audio(translated, voice_file, lang="hi")
            voice_files.append({
                "file": voice_file,
                "start": line["start"],
                "end": line["end"]
            })
    else:
        print("⚠️ No subtitles to process. Skipping translation and TTS.")
    
    # Step 5: Create combined voice track (simplified version)
    print("🎚️ Step 5: Mixing audio...")
    if voice_files:
        # For now, we'll concatenate all voice files
        # In Phase 2, we'll add proper timing alignment
        combined_voice = os.path.join(temp_dir, "combined_voice.wav")
        
        # Create simple audio mix with background and Hindi voice
        if voice_files:
            mixed_audio = os.path.join(temp_dir, "mixed_audio.wav")
            
            # Mix Hindi voice with background Korean audio
            cmd = f"""
            ffmpeg -y -i {temp_dir}/temp_combined.wav -i {original_audio} \\
            -filter_complex "[0:a]volume=15.0[voice];[1:a]volume=0.1[bg];[voice][bg]amix=inputs=2:duration=longest" \\
            {mixed_audio}
            """
            os.system(cmd)
        else:
            print("⚠️ No voice files generated. Using original audio only.")
            mixed_audio = original_audio
    else:
        print("⚠️ No voice files generated. Using original audio only.")
        mixed_audio = original_audio
    
    # Step 6: Render final video
    print("🎬 Step 6: Rendering final video...")
    output_video = os.path.join(output_dir, "dubbed_video.mp4")
    render_video(video_file, mixed_audio, output_video)
    
    print(f"✅ Dubbing complete! Output saved to: {output_video}")

if __name__ == "__main__":
    main()
