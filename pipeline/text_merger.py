import cv2
import os
from .ocr_extractor import extract_text, clean_text, similar_text

def process_frames_and_extract_text(frames_folder, fps=2):
    """
    Process all frames and extract text with timing information.
    
    Args:
        frames_folder (str): Folder containing extracted frames
        fps (int): FPS used for frame extraction
        
    Returns:
        list: List of dictionaries with timing and text data
    """
    subtitle_data = []
    frame_duration = 1.0 / fps
    
    # Get all frame files sorted
    frame_files = sorted([f for f in os.listdir(frames_folder) if f.endswith('.png')])
    
    current_text = ""
    start_time = 0
    last_change_time = 0
    
    for i, frame_file in enumerate(frame_files):
        frame_path = os.path.join(frames_folder, frame_file)
        current_time = i * frame_duration
        
        # Read and process frame
        from .subtitle_cropper import crop_subtitle_area, preprocess_for_ocr
        
        try:
            # Crop subtitle area
            cropped = crop_subtitle_area(frame_path)
            
            # Preprocess for OCR
            processed = preprocess_for_ocr(cropped)
            
            # Extract text
            raw_text = extract_text(processed)
            cleaned_text = clean_text(raw_text)
            
            # Check if text changed significantly
            if cleaned_text and not similar_text(current_text, cleaned_text):
                # Save previous subtitle if exists
                if current_text:
                    subtitle_data.append({
                        "start": start_time,
                        "end": current_time,
                        "text": current_text
                    })
                
                # Start new subtitle
                current_text = cleaned_text
                start_time = current_time
                last_change_time = current_time
                
            elif not cleaned_text and current_text:
                # Text ended
                subtitle_data.append({
                    "start": start_time,
                    "end": current_time,
                    "text": current_text
                })
                current_text = ""
                
        except Exception as e:
            print(f"Error processing frame {frame_file}: {e}")
            continue
    
    # Add final subtitle if exists
    if current_text:
        subtitle_data.append({
            "start": start_time,
            "end": current_time + frame_duration,
            "text": current_text
        })
    
    return subtitle_data

def merge_consecutive_subtitles(subtitle_data, min_duration=1.0, max_duration=7.0):
    """
    Merge consecutive subtitles with similar text and adjust timing.
    
    Args:
        subtitle_data (list): List of subtitle data
        min_duration (float): Minimum subtitle duration in seconds
        max_duration (float): Maximum subtitle duration in seconds
        
    Returns:
        list: Merged subtitle data
    """
    if not subtitle_data:
        return []
    
    merged = []
    current_subtitle = subtitle_data[0].copy()
    
    for next_subtitle in subtitle_data[1:]:
        # Check if subtitles should be merged
        time_gap = next_subtitle["start"] - current_subtitle["end"]
        
        # Merge if very close in time or similar content
        if time_gap < 0.5 or (
            time_gap < 2.0 and 
            len(current_subtitle["text"]) < 50 and 
            len(next_subtitle["text"]) < 50
        ):
            # Merge text
            current_subtitle["text"] += " " + next_subtitle["text"]
            current_subtitle["end"] = next_subtitle["end"]
        else:
            # Add current and start new
            merged.append(current_subtitle)
            current_subtitle = next_subtitle.copy()
    
    merged.append(current_subtitle)
    
    # Adjust durations to be within bounds
    for subtitle in merged:
        duration = subtitle["end"] - subtitle["start"]
        if duration < min_duration:
            subtitle["end"] = subtitle["start"] + min_duration
        elif duration > max_duration:
            subtitle["end"] = subtitle["start"] + max_duration
    
    return merged
