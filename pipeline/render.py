import os

def render_video(video_path, mixed_audio, output_path):
    """
    Combine original video with mixed audio track.
    
    Args:
        video_path (str): Path to original video file
        mixed_audio (str): Path to mixed audio file
        output_path (str): Path to output video file
    """
    cmd = f"""
    ffmpeg -y -i {video_path} -i {mixed_audio} \
    -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 \
    {output_path}
    """
    os.system(cmd)
