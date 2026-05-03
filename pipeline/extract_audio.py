import os

def extract_audio(video_path, output_audio):
    """
    Extract audio from video file using ffmpeg.
    
    Args:
        video_path (str): Path to input video file
        output_audio (str): Path to output audio file
    """
    os.system(f"ffmpeg -y -i {video_path} -vn -acodec pcm_s16le -ar 44100 -ac 2 {output_audio}")
