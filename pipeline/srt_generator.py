import datetime

def format_time(seconds):
    """
    Convert seconds to SRT time format (HH:MM:SS,mmm).
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def generate_srt(subtitle_data, output_file):
    """
    Generate SRT file from subtitle data.
    
    Args:
        subtitle_data (list): List of subtitle dictionaries
        output_file (str): Path to output SRT file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, subtitle in enumerate(subtitle_data):
            f.write(f"{i + 1}\n")
            f.write(f"{format_time(subtitle['start'])} --> {format_time(subtitle['end'])}\n")
            f.write(f"{subtitle['text']}\n\n")
