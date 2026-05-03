import pysrt

def parse_srt(file_path):
    """
    Parse SRT subtitle file and extract timing and text data.
    
    Args:
        file_path (str): Path to SRT file
        
    Returns:
        list: List of dictionaries containing start, end times and text
    """
    subs = pysrt.open(file_path)
    data = []

    for sub in subs:
        data.append({
            "start": sub.start.ordinal / 1000,
            "end": sub.end.ordinal / 1000,
            "text": sub.text.replace("\n", " ")
        })

    return data
