import os

def mix_audio(original_audio, voice_audio, output):
    """
    Mix original audio with generated voice audio, preserving background.
    
    Args:
        original_audio (str): Path to original audio file
        voice_audio (str): Path to generated voice audio file
        output (str): Path to output mixed audio file
    """
    cmd = f"""
    ffmpeg -y -i {original_audio} -i {voice_audio} \
    -filter_complex "[0:a]volume=0.3[a0];[1:a]volume=1.5[a1];[a0][a1]amix=inputs=2" \
    {output}
    """
    os.system(cmd)
