import os

def mix_audio(original_audio, voice_audio, output):
    """
    Mix original audio with generated voice audio, preserving background.
    Handles duration mismatch by padding shorter audio.
    
    Args:
        original_audio (str): Path to original audio file
        voice_audio (str): Path to generated voice audio file
        output (str): Path to output mixed audio file
    """
    # Use amix with dropout option to handle duration differences
    cmd = f"""
    ffmpeg -y -i {original_audio} -i {voice_audio} \
    -filter_complex "[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=3" \
    {output}
    """
    os.system(cmd)
