import os
from gtts import gTTS

def generate_audio(text, output_file, lang="hi"):
    """
    Generate speech audio from text using Google TTS (gTTS).
    
    Args:
        text (str): Text to convert to speech
        output_file (str): Path to output audio file
        lang (str): Language code (default: "hi" for Hindi)
    """
    try:
        # Create gTTS object
        tts = gTTS(text=text, lang=lang, slow=False)
        
        # Generate speech and save as mp3
        temp_mp3 = output_file.replace('.wav', '.mp3')
        tts.save(temp_mp3)
        
        # Convert mp3 to wav using ffmpeg with volume boost
        cmd = f"ffmpeg -y -i {temp_mp3} -af 'volume=10dB' -acodec pcm_s16le -ar 44100 -ac 1 {output_file}"
        os.system(cmd)
        
        # Clean up temporary mp3
        os.remove(temp_mp3)
        
        print(f"Generated Hindi audio for: '{text[:30]}...'")
        
    except Exception as e:
        print(f"Error generating TTS: {e}")
        # Fallback to silent audio
        word_count = len(text.split())
        duration = max(1.0, word_count * 0.5)
        cmd = f"ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t {duration} -acodec pcm_s16le -ar 44100 -ac 1 {output_file}"
        os.system(cmd)
