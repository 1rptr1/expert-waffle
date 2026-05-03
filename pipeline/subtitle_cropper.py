import cv2
import numpy as np

def crop_subtitle_area(image_path, bottom_ratio=0.25):
    """
    Crop the bottom region of frame where subtitles typically appear.
    
    Args:
        image_path (str): Path to image file
        bottom_ratio (float): Fraction of bottom area to crop (default: 0.25)
        
    Returns:
        numpy.ndarray: Cropped image
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    h, w, _ = img.shape
    
    # Crop bottom portion
    crop_start = int(h * (1 - bottom_ratio))
    cropped = img[crop_start:h, 0:w]
    
    return cropped

def preprocess_for_ocr(image):
    """
    Preprocess image for better OCR accuracy.
    
    Args:
        image (numpy.ndarray): Input image
        
    Returns:
        numpy.ndarray: Preprocessed image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Apply morphological operations to remove noise
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
    
    return processed
