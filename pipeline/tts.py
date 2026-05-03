from TTS.api import TTS

# Initialize TTS model
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

def generate_audio(text, output_file):
    """
    Generate speech audio from text using TTS.
    
    Args:
        text (str): Text to convert to speech
        output_file (str): Path to output audio file
    """
    tts.tts_to_file(text=text, file_path=output_file)
