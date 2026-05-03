import os
import subprocess

def detect_subtitle_tracks(video_path):
    """
    Check if video has embedded subtitle tracks.
    
    Args:
        video_path (str): Path to video file
        
    Returns:
        bool: True if subtitle tracks found, False otherwise
    """
    try:
        # Use ffprobe to check for subtitle streams
        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 's', 
            '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', 
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # If we get any output, there are subtitle tracks
        return bool(result.stdout.strip())
    except Exception as e:
        print(f"Error detecting subtitle tracks: {e}")
        return False

def extract_embedded_subtitles(video_path, output_srt):
    """
    Extract embedded subtitles to SRT file.
    
    Args:
        video_path (str): Path to video file
        output_srt (str): Path to output SRT file
        
    Returns:
        bool: True if extraction successful, False otherwise
    """
    try:
        cmd = [
            'ffmpeg', '-y', '-i', video_path, 
            '-map', '0:s:0', '-c:s', 'srt', output_srt
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error extracting embedded subtitles: {e}")
        return False
