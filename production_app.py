from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json
import uuid
import threading
import hashlib
from datetime import datetime
import sys
from typing import Optional

# Add pipeline to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.subtitle_extractor import extract_subtitles
from pipeline.parse_srt import parse_srt
from pipeline.translate import translate_text
from pipeline.llm_refiner import refine_translated_text, get_refiner
from pipeline.ollama_manager import setup_ollama_auto, ensure_model_available
from pipeline.real_tts import generate_audio
from pipeline.extract_audio import extract_audio
from pipeline.render import render_video

app = FastAPI(title="AI Dubber - One-Click Video Dubbing", version="2.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global status tracking
PROCESSING_STATUS = {}
CACHE = {}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure directories exist
os.makedirs("data/input", exist_ok=True)
os.makedirs("data/output", exist_ok=True)
os.makedirs("data/temp", exist_ok=True)
os.makedirs("data/cache", exist_ok=True)
os.makedirs("static", exist_ok=True)

def get_file_hash(file_path: str) -> str:
    """Generate SHA-256 hash of file for caching"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def update_status(job_id: str, stage: str, percent: int, message: str = "", mode: str = "fast"):
    """Update processing status for a job"""
    PROCESSING_STATUS[job_id] = {
        "stage": stage,
        "percent": percent,
        "message": message,
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "done": percent >= 100
    }
    
    # Save to file for persistence
    with open(f"data/temp/{job_id}_status.json", "w") as f:
        json.dump(PROCESSING_STATUS[job_id], f)

def run_fast_pipeline(job_id: str, video_path: str, srt_path: Optional[str], target_language: str):
    """Fast Mode: Subtitle-based dubbing"""
    try:
        temp_dir = f"data/temp/{job_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        update_status(job_id, "Setting up", 10, "Initializing Fast Mode...", "fast")
        
        # Step 1: Handle subtitles
        if srt_path and os.path.exists(srt_path):
            update_status(job_id, "Loading subtitles", 20, "Using provided SRT file...", "fast")
            final_srt = srt_path
        else:
            update_status(job_id, "Extracting subtitles", 20, "Extracting subtitles from video...", "fast")
            final_srt = os.path.join(temp_dir, "extracted_subtitles.srt")
            if not extract_subtitles(video_path, final_srt, temp_dir):
                raise Exception("Could not extract subtitles")
        
        # Step 2: Parse subtitles
        update_status(job_id, "Parsing subtitles", 30, "Parsing subtitle timing...", "fast")
        subtitles = parse_srt(final_srt)
        
        if not subtitles:
            raise Exception("No subtitles found")
        
        # Step 3: Extract audio
        update_status(job_id, "Extracting audio", 40, "Extracting original audio...", "fast")
        original_audio = os.path.join(temp_dir, "original_audio.wav")
        extract_audio(video_path, original_audio)
        
        # Step 4: Translate and generate voice (fast processing)
        update_status(job_id, "Translating", 50, "Translating subtitles...", "fast")
        voice_files = []
        
        for i, line in enumerate(subtitles):
            progress = 50 + int((i / len(subtitles)) * 30)
            update_status(job_id, "Generating voice", progress, f"Processing line {i+1}/{len(subtitles)}", "fast")
            
            # Fast translation (no LLM refinement)
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
        update_status(job_id, "Mixing audio", 85, "Mixing audio tracks...", "fast")
        mixed_audio = os.path.join(temp_dir, "mixed_audio.wav")
        
        if voice_files:
            # Quick concatenation
            voice_list_file = os.path.join(temp_dir, "voice_list.txt")
            with open(voice_list_file, "w") as f:
                for voice_info in voice_files:
                    filename = os.path.basename(voice_info['file'])
                    f.write(f"file '{filename}'\n")
            
            combined_voice = os.path.join(temp_dir, "combined_voice.wav")
            os.system(f"cd {temp_dir} && ffmpeg -y -f concat -safe 0 -i voice_list.txt -c copy combined_voice.wav")
            
            # Quick mix - preserve background audio
            os.system(f"""
            ffmpeg -y -i {original_audio} -i {combined_voice} \\
            -filter_complex "[0:a]volume=0.3[bg];[1:a]volume=5.0[voice];[bg][voice]amix=inputs=2:duration=longest:weights=1 3" \\
            {mixed_audio}
            """)
        else:
            mixed_audio = original_audio
        
        # Step 6: Render
        update_status(job_id, "Rendering", 95, "Rendering final video...", "fast")
        output_video = os.path.join("data/output", f"{job_id}_fast_dubbed.mp4")
        render_video(video_path, mixed_audio, output_video)
        
        # Cache result
        video_hash = get_file_hash(video_path)
        CACHE[video_hash] = {
            "output_path": output_video,
            "mode": "fast",
            "language": target_language,
            "timestamp": datetime.now().isoformat()
        }
        
        update_status(job_id, "Completed", 100, f"Fast Mode complete! Output: {job_id}_fast_dubbed.mp4", "fast")
        
    except Exception as e:
        update_status(job_id, "Error", 0, f"Fast Mode failed: {str(e)}", "fast")

def run_ai_pipeline(job_id: str, video_path: str, target_language: str):
    """AI Mode: Enhanced dubbing with LLM refinement and parallel processing"""
    try:
        temp_dir = f"data/temp/{job_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        update_status(job_id, "Setting up AI", 5, "Initializing AI Mode...", "ai")
        
        # Setup Ollama if needed
        update_status(job_id, "AI Setup", 10, "Setting up AI models...", "ai")
        setup_ollama_auto(["llama3"])
        ensure_model_available("llama3")
        
        # Extract subtitles
        update_status(job_id, "Extracting subtitles", 15, "Extracting subtitles...", "ai")
        srt_file = os.path.join(temp_dir, "extracted_subtitles.srt")
        if not extract_subtitles(video_path, srt_file, temp_dir):
            raise Exception("Could not extract subtitles")
        
        # Parse subtitles
        update_status(job_id, "Parsing subtitles", 20, "Parsing subtitle timing...", "ai")
        subtitles = parse_srt(srt_file)
        
        if not subtitles:
            raise Exception("No subtitles found")
        
        # Extract audio
        update_status(job_id, "Extracting audio", 25, "Extracting original audio...", "ai")
        original_audio = os.path.join(temp_dir, "original_audio.wav")
        extract_audio(video_path, original_audio)
        
        # AI-enhanced translation with LLM refinement
        update_status(job_id, "AI Translation", 30, "AI-powered translation...", "ai")
        voice_files = []
        
        for i, line in enumerate(subtitles):
            progress = 30 + int((i / len(subtitles)) * 40)
            update_status(job_id, "AI Processing", progress, f"AI refining line {i+1}/{len(subtitles)}", "ai")
            
            # Translate
            translated = translate_text(line["text"], target=target_language)
            
            # AI refinement
            duration = line["end"] - line["start"]
            refined = refine_translated_text(
                original=line["text"],
                translated=translated,
                duration=duration,
                model="llama3"
            )
            
            # Generate voice
            voice_file = os.path.join(temp_dir, f"voice_{i}.wav")
            generate_audio(refined, voice_file, lang=target_language)
            
            voice_files.append({
                "file": voice_file,
                "start": line["start"],
                "end": line["end"]
            })
        
        # Advanced audio mixing
        update_status(job_id, "AI Mixing", 75, "AI audio processing...", "ai")
        mixed_audio = os.path.join(temp_dir, "mixed_audio.wav")
        
        if voice_files:
            voice_list_file = os.path.join(temp_dir, "voice_list.txt")
            with open(voice_list_file, "w") as f:
                for voice_info in voice_files:
                    filename = os.path.basename(voice_info['file'])
                    f.write(f"file '{filename}'\n")
            
            combined_voice = os.path.join(temp_dir, "combined_voice.wav")
            os.system(f"cd {temp_dir} && ffmpeg -y -f concat -safe 0 -i voice_list.txt -c copy combined_voice.wav")
            
            # Enhanced mixing - preserve background audio
            os.system(f"""
            ffmpeg -y -i {original_audio} -i {combined_voice} \\
            -filter_complex "[0:a]volume=0.3[bg];[1:a]volume=5.0[voice];[bg][voice]amix=inputs=2:duration=longest:weights=1 3" \\
            {mixed_audio}
            """)
        else:
            mixed_audio = original_audio
        
        # Final rendering
        update_status(job_id, "AI Rendering", 90, "AI-enhanced rendering...", "ai")
        output_video = os.path.join("data/output", f"{job_id}_ai_dubbed.mp4")
        render_video(video_path, mixed_audio, output_video)
        
        # Cache result
        video_hash = get_file_hash(video_path)
        CACHE[video_hash] = {
            "output_path": output_video,
            "mode": "ai",
            "language": target_language,
            "timestamp": datetime.now().isoformat()
        }
        
        update_status(job_id, "AI Complete", 100, f"AI Mode complete! Output: {job_id}_ai_dubbed.mp4", "ai")
        
    except Exception as e:
        update_status(job_id, "AI Error", 0, f"AI Mode failed: {str(e)}", "ai")

def process_video_async(job_id: str, video_path: str, srt_path: Optional[str], mode: str, target_language: str):
    """Process video in background thread"""
    try:
        # Check cache first
        video_hash = get_file_hash(video_path)
        cache_key = f"{video_hash}_{mode}_{target_language}"
        
        if cache_key in CACHE:
            cached_result = CACHE[cache_key]
            if os.path.exists(cached_result["output_path"]):
                update_status(job_id, "Cached", 100, f"Using cached result: {os.path.basename(cached_result['output_path'])}", mode)
                return
        
        # Run appropriate pipeline
        if mode == "fast":
            run_fast_pipeline(job_id, video_path, srt_path, target_language)
        elif mode == "ai":
            run_ai_pipeline(job_id, video_path, target_language)
        else:
            raise Exception(f"Unknown mode: {mode}")
            
    except Exception as e:
        update_status(job_id, "Error", 0, f"Processing failed: {str(e)}", mode)

@app.get("/")
async def root():
    """Serve the main web interface"""
    return FileResponse("static/production.html")

@app.post("/process")
async def process_video(
    video: UploadFile = File(...),
    srt: Optional[UploadFile] = File(None),
    mode: str = Form(...),
    language: str = Form("hi")
):
    """Main processing endpoint with mode support"""
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Save video file
    video_path = f"data/input/{job_id}_{video.filename}"
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    
    # Save SRT file if provided
    srt_path = None
    if srt:
        srt_path = f"data/input/{job_id}_{srt.filename}"
        with open(srt_path, "wb") as buffer:
            shutil.copyfileobj(srt.file, buffer)
    
    # Initialize status
    update_status(job_id, "Uploaded", 5, f"Video uploaded, starting {mode} mode...", mode)
    
    # Start processing in background
    thread = threading.Thread(
        target=process_video_async,
        args=(job_id, video_path, srt_path, mode, language)
    )
    thread.start()
    
    return {"job_id": job_id, "status": "processing_started", "mode": mode}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get processing status for a job"""
    
    # Try to load from file if not in memory
    if job_id not in PROCESSING_STATUS:
        status_file = f"data/temp/{job_id}_status.json"
        if os.path.exists(status_file):
            with open(status_file, "r") as f:
                PROCESSING_STATUS[job_id] = json.load(f)
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    
    return PROCESSING_STATUS[job_id]

@app.get("/video/{job_id}")
async def get_video(job_id: str):
    """Get processed video"""
    # Check both fast and ai outputs
    for suffix in ["_fast_dubbed.mp4", "_ai_dubbed.mp4"]:
        video_path = f"data/output/{job_id}{suffix}"
        if os.path.exists(video_path):
            return FileResponse(video_path, media_type="video/mp4")
    
    raise HTTPException(status_code=404, detail="Video not ready")

@app.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download processed video"""
    # Check both fast and ai outputs
    for suffix in ["_fast_dubbed.mp4", "_ai_dubbed.mp4"]:
        video_path = f"data/output/{job_id}{suffix}"
        if os.path.exists(video_path):
            filename = f"dubbed_{job_id}{suffix}"
            return FileResponse(video_path, filename=filename)
    
    raise HTTPException(status_code=404, detail="Video not ready")

@app.get("/jobs")
async def list_jobs():
    """List recent jobs"""
    jobs = []
    
    # Check output directory for completed jobs
    output_dir = "data/output"
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            if filename.endswith("_dubbed.mp4"):
                job_id = filename.replace("_fast_dubbed.mp4", "").replace("_ai_dubbed.mp4", "")
                mode = "fast" if "_fast_" in filename else "ai"
                jobs.append({
                    "job_id": job_id,
                    "mode": mode,
                    "status": "completed",
                    "video_url": f"/video/{job_id}",
                    "download_url": f"/download/{job_id}"
                })
    
    return {"jobs": jobs}

@app.get("/cache")
async def get_cache_info():
    """Get cache information"""
    return {"cache_size": len(CACHE), "cached_items": list(CACHE.keys())}

@app.delete("/cache")
async def clear_cache():
    """Clear cache"""
    global CACHE
    CACHE = {}
    return {"status": "cache_cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
