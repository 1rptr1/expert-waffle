import os

def extract_frames(video_path, output_folder, fps=2):
    """
    Extract frames from video at specified FPS.
    
    Args:
        video_path (str): Path to input video
        output_folder (str): Folder to save frames
        fps (int): Frames per second to extract (default: 2)
    """
    os.makedirs(output_folder, exist_ok=True)
    
    # Use ffmpeg to extract frames at specified FPS
    cmd = f"ffmpeg -y -i {video_path} -vf fps={fps} {output_folder}/frame_%04d.png"
    os.system(cmd)
    
    return output_folder
