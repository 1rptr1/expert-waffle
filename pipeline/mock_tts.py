import os
import time

def generate_audio(text, output_file):
    """
    Mock TTS function that creates a silent audio file with the expected duration.
    This simulates TTS output without requiring the heavy TTS dependencies.
    
    Args:
        text (str): Text to convert to speech
        output_file (str): Path to output audio file
    """
    # Estimate duration based on text length (rough approximation: 0.5 seconds per word)
    word_count = len(text.split())
    duration = max(1.0, word_count * 0.5)  # Minimum 1 second
    
    # Create a silent audio file using ffmpeg
    cmd = f"ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t {duration} -acodec pcm_s16le -ar 44100 -ac 1 {output_file}"
    os.system(cmd)
    
    print(f"Generated mock audio for: '{text[:30]}...' ({duration:.1f}s)")
