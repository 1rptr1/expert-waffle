# AI Dubber

An automated video dubbing pipeline that handles **all subtitle types** - embedded, hardcoded, and none - with automatic subtitle extraction, translation, and voice-over generation while preserving background audio.

## 🚀 Major Features

### 📺 **Universal Subtitle Support**
- **🔍 Smart Detection**: Automatically detects embedded subtitle tracks
- **📸 OCR Extraction**: Extracts hardcoded subtitles from video frames
- **📜 SRT Generation**: Creates subtitle files from any source
- **� Fallback Handling**: Gracefully handles videos without subtitles

### 🎬 **Complete Pipeline**
- �🎥 Video audio extraction
- 📜 SRT subtitle parsing (auto-generated if needed)
- 🌍 Text translation
- 🎙️ Text-to-speech generation
- 🎚️ Audio mixing with background preservation
- 🎬 Final video rendering

## Quick Start

### Prerequisites

- Python 3.10+
- FFmpeg
- Tesseract OCR
- CUDA (optional, for faster TTS)

### Installation

```bash
# Clone and navigate to project
cd ai-dubber

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data/input data/output data/temp
```

### Usage

**Simple Mode - Auto-detect subtitles:**
1. Place your video file in `data/input/input_video.mp4`
2. Run the pipeline:

```bash
python app.py
```

The system will:
- 🔍 Check for embedded subtitles
- 📸 Extract hardcoded subtitles via OCR if needed
- 🌍 Translate and generate voice-over
- 🎬 Output to `data/output/dubbed_video.mp4`

**Manual Mode - Use existing SRT:**
1. Place your video file in `data/input/input_video.mp4`
2. Place your subtitle file in `data/input/input.srt`
3. Run the pipeline

### Docker Usage

```bash
# Build the image
docker build -t ai-dubber .

# Run the container
docker run -v $(pwd)/data:/app/data ai-dubber
```

## 🏗️ Enhanced Pipeline Structure

```
ai-dubber/
│
├── app.py                           # Main application with smart subtitle handling
├── pipeline/
│   ├── subtitle_detector.py         # Detect embedded subtitle tracks
│   ├── subtitle_extractor.py        # Main subtitle extraction orchestrator
│   ├── frame_extractor.py           # Extract frames for OCR
│   ├── subtitle_cropper.py           # Crop subtitle regions
│   ├── ocr_extractor.py             # OCR text extraction with cleaning
│   ├── text_merger.py               # Merge and clean OCR results
│   ├── srt_generator.py             # Generate SRT files
│   ├── extract_audio.py             # Extract audio from video
│   ├── parse_srt.py                 # Parse subtitle files
│   ├── translate.py                 # Translate text
│   ├── tts.py                      # Generate speech
│   ├── mixer.py                    # Mix audio tracks
│   └── render.py                   # Render final video
│
├── data/
│   ├── input/                      # Input video files
│   ├── output/                     # Final dubbed videos
│   └── temp/                       # Temporary processing files
│
├── requirements.txt
├── Dockerfile
└── README.md
```

## 🎯 How It Works

### **Smart Subtitle Detection Flow**

1. **🔍 Check Embedded Subtitles**
   - Uses FFprobe to detect subtitle streams
   - Extracts directly if found

2. **📸 OCR Extraction (if no embedded subs)**
   - Extracts frames at 2 FPS
   - Crops bottom 25% of frame
   - Preprocesses with grayscale and thresholding
   - Uses Tesseract OCR with custom configuration
   - Cleans and merges text with similarity detection

3. **🧹 Text Processing**
   - Removes OCR artifacts
   - Merges consecutive similar text
   - Applies timing constraints (1-7 seconds per subtitle)

## 🛠️ Advanced Features

### **OCR Optimization**
- ✅ Grayscale conversion
- ✅ Otsu thresholding
- ✅ Morphological noise removal
- ✅ Custom Tesseract configuration
- ✅ Text similarity detection
- ✅ Artifact cleaning

### **Text Processing**
- ✅ Duplicate removal
- ✅ Flickering text handling
- ✅ Timing-based clustering
- ✅ Duration optimization

## Current Limitations

- ⏱️ No perfect timing synchronization
- 🔄 No chunk buffering system
- 🎧 No voice separation (background vs dialogue)
- 📊 Limited to English TTS model
- 🔤 OCR accuracy varies with subtitle styling

## Phase 2 Upcoming Features

- ⏱️ Precise timing alignment with subtitle timestamps
- 🔄 5-second chunk buffering system
- 🎧 Audio separation using Demucs
- 🌍 Multi-language TTS support
- 🧠 Whisper integration for better OCR correction
- 🎨 Stylized subtitle handling (colors, fonts)
- 🐳 Optimized Docker configuration

## Dependencies

### Python Packages
- `pysrt` - SRT file parsing
- `deep-translator` - Text translation
- `TTS` - Text-to-speech synthesis
- `torch` - Deep learning framework
- `opencv-python` - Image processing
- `pytesseract` - OCR engine
- `Pillow` - Image manipulation

### System Dependencies
- `ffmpeg` - Media processing
- `tesseract-ocr` - OCR engine with English language pack

## 🎉 What Makes This Special

**🏆 Universal Subtitle Support**: Handles embedded, hardcoded, and no subtitles automatically
**🧠 Smart OCR**: Advanced preprocessing and text cleaning for better accuracy
**🔄 Robust Pipeline**: Graceful fallbacks and error handling
**🎯 Production Ready**: Docker support and comprehensive error handling
# expert-waffle
