FROM python:3.10

WORKDIR /app

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y ffmpeg tesseract-ocr tesseract-ocr-eng libgl1-mesa-glx

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/input data/output data/temp

CMD ["python", "app.py"]
