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
    use_llm_refinement = True  # Enable LLM enhancement
    llm_model = "llama3"  # Can be "llama3", "mistral", etc.
    
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    print("🎬 Starting Enhanced AI Dubbing Pipeline with LLM Refinement...")
    
    # Step 0: Extract subtitles
    print("🔍 Step 0: Extracting subtitles...")
    if not os.path.exists(srt_file):
        print("No SRT file found, attempting to extract subtitles from video...")
        if not extract_subtitles(video_file, srt_file, temp_dir):
            print("⚠️ Could not extract subtitles. Continuing without translation...")
            return
    
    # Step 1: Parse subtitles
    print("📖 Step 1: Parsing SRT...")
    subtitles = parse_srt(srt_file)
    
    if not subtitles:
        print("⚠️ No subtitles found.")
        return
    
    print(f"✅ Found {len(subtitles)} subtitle lines")
    
    # Step 2: Extract original audio
    print("🎤 Step 2: Extracting original audio...")
    original_audio = os.path.join(temp_dir, "original_audio.wav")
    extract_audio(video_file, original_audio)
    
    # Step 3: Translate and refine with LLM
    print("🌍 Step 3: Translating and refining with LLM...")
    voice_files = []
    
    # Prepare data for batch processing
    translation_data = []
    for i, line in enumerate(subtitles):
        # Translate text
        translated = translate_text(line["text"], target=target_language)
        
        # Calculate duration
        duration = line["end"] - line["start"]
        
        # Detect emotion (simple heuristic)
        emotion = get_refiner(llm_model).detect_emotion(line["text"])
        
        translation_data.append({
            'original': line["text"],
            'translated': translated,
            'duration': duration,
            'emotion': emotion,
            'index': i
        })
    
    # Batch refine with LLM
    if use_llm_refinement:
        print(f"🧠 Refining {len(translation_data)} lines with {llm_model}...")
        refined_texts = get_refiner(llm_model).batch_refine(translation_data, batch_size=3)
    else:
        refined_texts = [item['translated'] for item in translation_data]
    
    # Step 4: Generate voice audio
    print("🗣️ Step 4: Generating refined voice audio...")
    
    for i, (line_data, refined_text) in enumerate(zip(subtitles, refined_texts)):
        print(f"🎙️ Processing line {i+1}/{len(subtitles)}: '{refined_text[:50]}...'")
        
        # Generate voice file
        voice_file = os.path.join(temp_dir, f"voice_{i}.wav")
        generate_audio(refined_text, voice_file, lang=target_language)
        
        voice_files.append({
            "file": voice_file,
            "start": line["start"],
            "end": line["end"]
        })
    
    # Step 5: Mix audio with background
    print("🎧 Step 5: Mixing refined audio with background...")
    
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
    print("🎬 Step 6: Rendering final enhanced video...")
    output_video = os.path.join(output_dir, "enhanced_dubbed_video.mp4")
    render_video(video_file, mixed_audio, output_video)
    
    print(f"✅ Enhanced AI Dubbing complete! Output saved to: {output_video}")
    print(f"🧠 Used {llm_model} for text refinement")
    print(f"🌍 Target language: {target_language}")
    print(f"🎙️ Processed {len(voice_files)} voice segments")

def detect_emotion_heuristic(text: str) -> str:
    """
    Simple emotion detection based on text patterns
    """
    text_lower = text.lower()
    
    # Emotion indicators
    if '!' in text or any(word in text_lower for word in ['amazing', 'wonderful', 'great']):
        return 'happy'
    elif '...' in text or any(word in text_lower for word in ['sad', 'sorry', 'goodbye']):
        return 'sad'
    elif any(word in text_lower for word in ['what', 'how', 'why', 'really']):
        return 'surprised'
    elif any(word in text_lower for word in ['help', 'scared', 'danger']):
        return 'fear'
    elif any(word in text_lower for word in ['damn', 'hell', 'get out']):
        return 'angry'
    
    return 'neutral'

if __name__ == "__main__":
    main()
