import os
import sys
import time
from typing import Optional

# Add pipeline to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.subtitle_extractor import extract_subtitles
from pipeline.parse_srt import parse_srt
from pipeline.translate import translate_text
from pipeline.llm_refiner import refine_translated_text, get_refiner
from pipeline.ollama_manager import setup_ollama_auto, ensure_model_available, check_ollama_status
from pipeline.real_tts import generate_audio
from pipeline.extract_audio import extract_audio
from pipeline.render import render_video

def main():
    # Configuration
    video_file = "data/input/The.Gangster.the.Cop.the.Devil.2019.KOREAN.1080p.10bit.BluRay.6CH.sample.mkv"
    srt_file = "data/input/extracted_subtitles.srt"
    output_dir = "data/output"
    temp_dir = "data/temp"
    target_language = "hi"
    llm_model = "llama3"
    
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    print("🎬 Starting Auto-Setup AI Dubbing Pipeline...")
    
    # Step 0: Auto-setup Ollama
    print("🔧 Step 0: Auto-setting up Ollama...")
    
    # Check current status
    status = check_ollama_status()
    print(f"📊 System Info:")
    print(f"   Platform: {status['platform']}")
    print(f"   Ollama Installed: {status['ollama_installed']}")
    print(f"   Ollama Running: {status['ollama_running']}")
    print(f"   Available Models: {status['available_models']}")
    
    # Auto-setup Ollama with default models
    if setup_ollama_auto([llm_model]):
        print("✅ Ollama setup completed successfully")
    else:
        print("⚠️ Ollama setup failed, continuing without LLM refinement...")
        llm_model = None
    
    # Step 1: Extract subtitles
    print("🔍 Step 1: Extracting subtitles...")
    if not os.path.exists(srt_file):
        print("No SRT file found, attempting to extract subtitles from video...")
        if not extract_subtitles(video_file, srt_file, temp_dir):
            print("⚠️ Could not extract subtitles. Continuing without translation...")
            return
    
    # Step 2: Parse subtitles
    print("📖 Step 2: Parsing SRT...")
    subtitles = parse_srt(srt_file)
    
    if not subtitles:
        print("⚠️ No subtitles found.")
        return
    
    print(f"✅ Found {len(subtitles)} subtitle lines")
    
    # Step 3: Extract original audio
    print("🎤 Step 3: Extracting original audio...")
    original_audio = os.path.join(temp_dir, "original_audio.wav")
    extract_audio(video_file, original_audio)
    
    # Step 4: Translate and optionally refine with LLM
    print("🌍 Step 4: Translating and refining...")
    voice_files = []
    
    for i, line in enumerate(subtitles):
        print(f"📝 Processing line {i+1}/{len(subtitles)}")
        
        # Translate text
        translated = translate_text(line["text"], target=target_language)
        print(f"   🌐 Translated: {translated[:50]}...")
        
        # Refine with LLM if available
        if llm_model:
            # Calculate duration
            duration = line["end"] - line["start"]
            
            # Ensure model is available
            if ensure_model_available(llm_model):
                refined = refine_translated_text(
                    original=line["text"],
                    translated=translated,
                    duration=duration,
                    model=llm_model
                )
                print(f"   🧠 Refined: {refined[:50]}...")
                final_text = refined
            else:
                print("   ⚠️ Using original translation (model unavailable)")
                final_text = translated
        else:
            final_text = translated
        
        # Generate voice file
        voice_file = os.path.join(temp_dir, f"voice_{i}.wav")
        generate_audio(final_text, voice_file, lang=target_language)
        
        voice_files.append({
            "file": voice_file,
            "start": line["start"],
            "end": line["end"]
        })
    
    # Step 5: Mix audio with background
    print("🎧 Step 5: Mixing audio...")
    
    if voice_files:
        # Create voice list file for concatenation
        voice_list_file = os.path.join(temp_dir, "voice_list.txt")
        with open(voice_list_file, "w") as f:
            for voice_info in voice_files:
                filename = os.path.basename(voice_info['file'])
                f.write(f"file '{filename}'\n")
        
        # Concatenate all voice files
        combined_voice = os.path.join(temp_dir, "combined_voice.wav")
        os.system(f"cd {temp_dir} && ffmpeg -y -f concat -safe 0 -i voice_list.txt -c copy combined_voice.wav")
        
        # Mix with background Korean audio
        mixed_audio = os.path.join(temp_dir, "mixed_audio.wav")
        cmd = f"""
        ffmpeg -y -i {combined_voice} -i {original_audio} \\
        -filter_complex "[0:a]volume=15.0[voice];[1:a]volume=0.1[bg];[voice][bg]amix=inputs=2:duration=longest" \\
        {mixed_audio}
        """
        os.system(cmd)
    else:
        print("⚠️ No voice files generated. Using original audio only.")
        mixed_audio = original_audio
    
    # Step 6: Render final video
    print("🎬 Step 6: Rendering final video...")
    output_video = os.path.join(output_dir, "auto_setup_dubbed_video.mp4")
    render_video(video_file, mixed_audio, output_video)
    
    print(f"✅ Auto-Setup AI Dubbing complete!")
    print(f"📹 Output saved to: {output_video}")
    print(f"🧠 LLM Model: {llm_model if llm_model else 'None'}")
    print(f"🌍 Target language: {target_language}")
    print(f"🎙️ Processed {len(voice_files)} voice segments")
    
    # Final status summary
    final_status = check_ollama_status()
    print(f"\n🎯 Final System Status:")
    print(f"   Ollama Running: {final_status['ollama_running']}")
    print(f"   Available Models: {final_status['available_models']}")

if __name__ == "__main__":
    main()
