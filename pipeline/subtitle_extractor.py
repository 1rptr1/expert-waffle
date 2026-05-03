import os
import tempfile
from .subtitle_detector import detect_subtitle_tracks, extract_embedded_subtitles
from .frame_extractor import extract_frames
from .text_merger import process_frames_and_extract_text, merge_consecutive_subtitles
from .srt_generator import generate_srt

def extract_subtitles(video_path, output_srt, temp_dir="data/temp"):
    """
    Extract subtitles from video, handling both embedded and hardcoded subtitles.
    
    Args:
        video_path (str): Path to input video
        output_srt (str): Path to output SRT file
        temp_dir (str): Temporary directory for processing
        
    Returns:
        bool: True if extraction successful, False otherwise
    """
    os.makedirs(temp_dir, exist_ok=True)
    
    print("🔍 Detecting subtitle type...")
    
    # Check for embedded subtitles first
    if detect_subtitle_tracks(video_path):
        print("✅ Found embedded subtitle tracks")
        return extract_embedded_subtitles(video_path, output_srt)
    
    print("🔍 No embedded subtitles found, attempting OCR extraction...")
    
    # Extract frames for OCR
    frames_dir = os.path.join(temp_dir, "frames")
    print("📸 Extracting frames...")
    extract_frames(video_path, frames_dir, fps=2)
    
    # Process frames and extract text
    print("🔤 Processing frames with OCR...")
    subtitle_data = process_frames_and_extract_text(frames_dir)
    
    if not subtitle_data:
        print("❌ No subtitles detected in video")
        return False
    
    # Merge and clean subtitle data
    print("🧹 Merging and cleaning subtitle data...")
    merged_subtitles = merge_consecutive_subtitles(subtitle_data)
    
    # Generate SRT file
    print("📜 Generating SRT file...")
    generate_srt(merged_subtitles, output_srt)
    
    # Clean up temporary frames
    import shutil
    try:
        shutil.rmtree(frames_dir)
    except:
        pass
    
    print(f"✅ Successfully extracted {len(merged_subtitles)} subtitle entries")
    return True
