# ROBUST CAPTCHA SERVICE DOCKERFILE WITH ERROR HANDLING
FROM python:3.11-slim

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies with error handling
RUN apt-get update && \
    # Essential packages first
    apt-get install -y --no-install-recommends \
        curl wget ca-certificates && \
    # Try to install OCR and graphics packages
    (apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-eng \
        libglib2.0-0 libsm6 libxext6 libxrender-dev \
        libgomp1 libgtk-3-0 libgl1-mesa-glx \
        libglib2.0-dev libgl1-mesa-dev libglu1-mesa-dev \
        libxrandr2 libxss1 libxcursor1 libxcomposite1 \
        libasound2 libxi6 libxtst6 || \
        echo "Some graphics packages failed to install") && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies with error handling
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 3000 --retries 15 --upgrade pip setuptools wheel && \
    # Try to install all packages at once first
    (pip install --no-cache-dir --timeout 3000 --retries 15 \
        --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
        -r requirements.txt || \
    # If bulk install fails, try individual packages
    (echo "Bulk install failed, trying core packages..." && \
     pip install --no-cache-dir --timeout 3000 --retries 15 fastapi uvicorn && \
     pip install --no-cache-dir --timeout 3000 --retries 15 pillow || echo "Pillow failed" && \
     pip install --no-cache-dir --timeout 3000 --retries 15 opencv-python || echo "OpenCV failed" && \
     pip install --no-cache-dir --timeout 3000 --retries 15 pytesseract || echo "PyTesseract failed" && \
     pip install --no-cache-dir --timeout 3000 --retries 15 numpy || echo "NumPy failed"))

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p /app/temp /app/logs && \
    chmod -R 755 /app

# Expose port
EXPOSE 9001

# Robust health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:9001/health || \
        curl -f http://localhost:9001/ || \
        exit 1

# Start with error handling and fallback options
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 9001 || python -m uvicorn main:app --host 0.0.0.0 --port 9001 || gunicorn --bind 0.0.0.0:9001 --workers 2 --timeout 120 app:app"]
