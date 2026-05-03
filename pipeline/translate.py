from deep_translator import GoogleTranslator

def translate_text(text, target="hi"):
    """
    Translate text to target language using Google Translator.
    
    Args:
        text (str): Text to translate
        target (str): Target language code (default: "en")
        
    Returns:
        str: Translated text
    
    Common language codes:
        "en" - English
        "es" - Spanish
        "fr" - French
        "de" - German
        "it" - Italian
        "pt" - Portuguese
        "ru" - Russian
        "ja" - Japanese
        "ko" - Korean
        "zh" - Chinese
        "hi" - Hindi
        "ar" - Arabic
        "bn" - Bengali
        "ta" - Tamil
        "te" - Telugu
        "mr" - Marathi
        "gu" - Gujarati
        "pa" - Punjabi
        "ur" - Urdu
    """
    return GoogleTranslator(source='auto', target=target).translate(text)
