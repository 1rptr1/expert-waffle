import pytesseract
import re
from difflib import SequenceMatcher

def extract_text(image):
    """
    Extract text from image using Tesseract OCR.
    
    Args:
        image (numpy.ndarray): Preprocessed image
        
    Returns:
        str: Extracted text
    """
    # Configure Tesseract for better subtitle recognition
    custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
    text = pytesseract.image_to_string(image, config=custom_config)
    
    return text.strip()

def clean_text(text):
    """
    Clean OCR text by removing common artifacts.
    
    Args:
        text (str): Raw OCR text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove common OCR artifacts
    text = re.sub(r'[|lI]', 'l', text)  # Common character confusion
    text = re.sub(r'[0O]', 'O', text)   # Number/letter confusion
    text = re.sub(r'[1!]', 'l', text)   # Number/exclamation confusion
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove non-printable characters except basic punctuation
    text = re.sub(r'[^\w\s\-.,!?;:\'"()]', '', text)
    
    return text.strip()

def similar_text(text1, text2, threshold=0.8):
    """
    Check if two text strings are similar.
    
    Args:
        text1 (str): First text
        text2 (str): Second text
        threshold (float): Similarity threshold (default: 0.8)
        
    Returns:
        bool: True if texts are similar
    """
    if not text1 or not text2:
        return False
    
    similarity = SequenceMatcher(None, text1, text2).ratio()
    return similarity >= threshold
