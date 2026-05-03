from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json
import uuid
import threading
from datetime import datetime
import sys

# Add pipeline to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.subtitle_extractor import extract_subtitles
from pipeline.parse_srt import parse_srt
from pipeline.translate import translate_text
from pipeline.real_tts import generate_audio
from pipeline.extract_audio import extract_audio
from pipeline.render import render_video

app = FastAPI(title="AI Dubber - Video Dubbing API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global status tracking
processing_status = {}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure directories exist
os.makedirs("data/input", exist_ok=True)
os.makedirs("data/output", exist_ok=True)
os.makedirs("data/temp", exist_ok=True)
os.makedirs("static", exist_ok=True)

def update_status(job_id: str, stage: str, percent: int, message: str = ""):
    """Update processing status for a job"""
    processing_status[job_id] = {
        "stage": stage,
        "percent": percent,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save to file for persistence
    with open(f"data/temp/{job_id}_status.json", "w") as f:
        json.dump(processing_status[job_id], f)

def process_video_async(job_id: str, video_path: str, target_language: str, mode: str = "fast"):
    """Process video in background thread"""
    try:
        update_status(job_id, "starting", 5, "Initializing pipeline...")
        
        # Generate unique filenames for this job
        temp_dir = f"data/temp/{job_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        srt_file = os.path.join(temp_dir, "extracted_subtitles.srt")
        original_audio = os.path.join(temp_dir, "original_audio.wav")
        output_video = os.path.join("data/output", f"{job_id}_dubbed.mp4")
        
        # Step 1: Extract subtitles
        update_status(job_id, "extracting_subtitles", 15, "Extracting subtitles from video...")
        if not extract_subtitles(video_path, srt_file, temp_dir):
            update_status(job_id, "error", 0, "Could not extract subtitles")
            return
        
        # Step 2: Parse subtitles
        update_status(job_id, "parsing_subtitles", 25, "Parsing subtitle timing...")
        subtitles = parse_srt(srt_file)
        
        if not subtitles:
            update_status(job_id, "error", 0, "No subtitles found")
            return
        
        # Step 3: Extract audio
        update_status(job_id, "extracting_audio", 35, "Extracting original audio...")
        extract_audio(video_path, original_audio)
        
        # Step 4: Translate and generate voice
        update_status(job_id, "translating", 45, "Translating subtitles...")
        voice_files = []
        
        for i, line in enumerate(subtitles):
            progress = 45 + int((i / len(subtitles)) * 30)
            update_status(job_id, "generating_voice", progress, f"Processing line {i+1}/{len(subtitles)}")
            
            # Translate text
            translated = translate_text(line["text"], target=target_language)
            
            # Generate voice
            voice_file = os.path.join(temp_dir, f"voice_{i}.wav")
            generate_audio(translated, voice_file, lang=target_language)
            
            voice_files.append({
                "file": voice_file,
                "start": line["start"],
                "end": line["end"]
            })
        
        # Step 5: Mix audio
        update_status(job_id, "mixing_audio", 80, "Mixing audio tracks...")
        
        if voice_files:
            # Create voice list file
            voice_list_file = os.path.join(temp_dir, "voice_list.txt")
            with open(voice_list_file, "w") as f:
                for voice_info in voice_files:
                    filename = os.path.basename(voice_info['file'])
                    f.write(f"file '{filename}'\n")
            
            # Concatenate voice files
            combined_voice = os.path.join(temp_dir, "combined_voice.wav")
            os.system(f"cd {temp_dir} && ffmpeg -y -f concat -safe 0 -i voice_list.txt -c copy combined_voice.wav")
            
            # Mix with background
            mixed_audio = os.path.join(temp_dir, "mixed_audio.wav")
            os.system(f"""
            ffmpeg -y -i {combined_voice} -i {original_audio} \\
            -filter_complex "[0:a]volume=15.0[voice];[1:a]volume=0.1[bg];[voice][bg]amix=inputs=2:duration=longest" \\
            {mixed_audio}
            """)
        else:
            mixed_audio = original_audio
        
        # Step 6: Render final video
        update_status(job_id, "rendering", 90, "Rendering final video...")
        render_video(video_path, mixed_audio, output_video)
        
        # Clean up temp files
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        update_status(job_id, "completed", 100, f"Video successfully dubbed! Output: {job_id}_dubbed.mp4")
        
    except Exception as e:
        update_status(job_id, "error", 0, f"Processing failed: {str(e)}")

@app.get("/")
async def root():
    """Serve the main web interface"""
    return FileResponse("static/index.html")

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...), language: str = "hi", mode: str = "fast"):
    """Upload and start processing video"""
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Save uploaded file
    input_path = f"data/input/{job_id}_{file.filename}"
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Initialize status
    update_status(job_id, "uploaded", 10, "Video uploaded, starting processing...")
    
    # Start processing in background
    thread = threading.Thread(
        target=process_video_async,
        args=(job_id, input_path, language, mode)
    )
    thread.start()
    
    return {"job_id": job_id, "status": "processing_started"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get processing status for a job"""
    
    # Try to load from file if not in memory
    if job_id not in processing_status:
        status_file = f"data/temp/{job_id}_status.json"
        if os.path.exists(status_file):
            with open(status_file, "r") as f:
                processing_status[job_id] = json.load(f)
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    
    return processing_status[job_id]

@app.get("/video/{job_id}")
async def get_video(job_id: str):
    """Get processed video"""
    video_path = f"data/output/{job_id}_dubbed.mp4"
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not ready")
    
    return FileResponse(video_path, media_type="video/mp4")

@app.get("/jobs")
async def list_jobs():
    """List all recent jobs"""
    jobs = []
    
    # Check output directory for completed jobs
    output_dir = "data/output"
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            if filename.endswith("_dubbed.mp4"):
                job_id = filename.replace("_dubbed.mp4", "")
                jobs.append({
                    "job_id": job_id,
                    "status": "completed",
                    "video_url": f"/video/{job_id}"
                })
    
    return {"jobs": jobs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
