# 🚀 Comprehensive AI Integration Activation Guide

## 📋 Overview

This guide provides step-by-step instructions to activate all AI services in the Cumpair platform:
- HuggingFace API (text generation, sentiment, embeddings, captioning)
- Voice STT (Speech-to-Text via Whisper)
- CLIP (image-text matching)
- YOLO (object detection)
- Barcode/QR detection
- OCR (text extraction)
- CAPTCHA solving

---

## 🔑 Prerequisites Checklist

### Environment Variables
Ensure the following are set in `.env`:

```bash
# HuggingFace (REQUIRED)
HF_API_KEY=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

# Database
DATABASE_URL=postgresql://compair:compair123@postgres:5432/compair
REDIS_URL=redis://redis:6379

# Services
CAPTCHA_SERVICE_URL=http://captcha:9001
VOICE_STT_PROVIDER=local  # or 'hf'
WHISPER_MODEL_SIZE=base

# Uploads
UPLOAD_DIR=uploads
```

### Dependencies Installed
All Python packages from `requirements.txt` including:
- `aiohttp` (HTTP client)
- `faster-whisper` (Speech-to-Text)
- `pyzbar` (Barcode detection)
- `easyocr` or `pytesseract` (OCR)
- `transformers`, `sentence-transformers` (HF models)
- `huggingface-hub` (HF API client)

---

## 📝 Step-by-Step Activation Order

### Step 0: Verify Infrastructure

```powershell
# Check Redis
docker exec test_model-redis-1 redis-cli ping
# Expected: PONG

# Check PostgreSQL
docker exec test_model-postgres-1 pg_isready
# Expected: accepting connections

# Check disk space (models need ~2GB)
Get-PSDrive C
```

---

### Step 1: Start CAPTCHA Service

```powershell
# Check CAPTCHA health
curl http://localhost:9001/health | ConvertFrom-Json

# Expected output:
# {
#   "status": "healthy",
#   "ocr_engines": {"tesseract": true, "easyocr": true},
#   "redis": "connected"
# }

# Smoke test with sample CAPTCHA
$base64img = [Convert]::ToBase64String([IO.File]::ReadAllBytes("test_captcha.png"))
$body = @{method='base64'; body=$base64img} | ConvertTo-Json
curl -Method POST -Uri "http://localhost:9001/in.php" -Body $body -ContentType "application/json"
```

---

### Step 2: Start Main FastAPI Application

```powershell
# Build Docker image (if needed)
docker-compose build web

# Start service
docker-compose up -d web

# Check logs
docker logs test_model-web-1 --tail 50

# Look for:
# ✅ AI models initialized successfully!
# ✅ CLIP service ready
# 🤗 HuggingFace connector initialized (configured: True)
# 🎤 Voice STT service initialized (provider: local)
# 🖼️  Image Processor initialized
```

---

### Step 3: Health Check All Services

```powershell
# Comprehensive health check
curl http://localhost:8000/health/services | ConvertFrom-Json

# Expected: All services show "healthy": true
# {
#   "status": "healthy",
#   "services": {
#     "clip": {"status": "healthy", "healthy": true},
#     "huggingface": {"status": "healthy", "healthy": true},
#     "voice_stt": {"status": "healthy", "healthy": true},
#     "image_processor": {"status": "healthy", "healthy": true},
#     "captcha": {"status": "healthy", "healthy": true},
#     "redis": {"status": "healthy", "healthy": true},
#     "database": {"status": "healthy", "healthy": true}
#   }
# }
```

---

## 🧪 Manual Test Commands

### 1. Image Upload

```powershell
# Upload image via camera/file
curl -Method POST `
  -Uri "http://localhost:8000/api/images/upload" `
  -Form @{file=Get-Item "test_product.jpg"; source="upload"}

# Expected:
# {
#   "status": "ok",
#   "image_id": "uuid-here",
#   "url": "/uploads/uuid-here.jpg",
#   "size": 12345
# }
```

### 2. Image Analysis (All Tasks)

```powershell
$body = @{
  image_id = "uuid-from-upload"
  tasks = @("clip", "barcode", "ocr", "caption", "objects")
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/api/images/analyze" `
  -Body $body `
  -ContentType "application/json"

# Expected:
# {
#   "status": "ok",
#   "results": {
#     "clip": {"matches": [...], "count": 5},
#     "barcode": [{"type": "qrcode", "data": "..."}],
#     "ocr": "Extracted text here...",
#     "caption": "A product on a shelf",
#     "objects": [{"class": "bottle", "confidence": 0.95}]
#   },
#   "processing_time": 2.34
# }
```

### 3. CLIP Similarity Search

```powershell
$body = @{
  image = "https://example.com/product.jpg"
  top_k = 5
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/api/clip/compare" `
  -Body $body `
  -ContentType "application/json"

# Expected:
# {
#   "status": "ok",
#   "matches": [
#     {"product_id": "123", "score": 0.95, "title": "Product Name", "price": 29.99},
#     ...
#   ],
#   "count": 5
# }
```

### 4. Barcode Decode

```powershell
$body = @{image_id = "uuid-here"} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/api/barcode/decode" `
  -Body $body `
  -ContentType "application/json"

# Expected:
# {
#   "status": "ok",
#   "barcodes": [
#     {"type": "EAN13", "data": "1234567890123", "rect": {...}}
#   ],
#   "count": 1
# }
```

### 5. OCR Receipt

```powershell
$body = @{image_id = "uuid-here"} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/api/ocr/receipt" `
  -Body $body `
  -ContentType "application/json"

# Expected:
# {
#   "status": "ok",
#   "text": "STORE NAME\nItem 1 ... $10.99\nItem 2 ... $5.49",
#   "items": [
#     {"name": "Item 1", "price": 10.99, "qty": 1, "confidence": 0.7},
#     ...
#   ]
# }
```

### 6. Text Generation (HuggingFace)

```powershell
$body = @{
  prompt = "Summarize: I bought a smartphone for $599"
  max_tokens = 50
  temperature = 0.7
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/api/text/generate" `
  -Body $body `
  -ContentType "application/json"

# Expected:
# {
#   "status": "ok",
#   "text": "A smartphone purchase for $599 represents..."
# }
```

### 7. Sentiment Analysis

```powershell
$body = @{
  text = "This product is absolutely amazing! Best purchase ever."
  task = "sentiment"
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/api/text/analyze" `
  -Body $body `
  -ContentType "application/json"

# Expected:
# {
#   "status": "ok",
#   "task": "sentiment",
#   "result": {
#     "label": "POSITIVE",
#     "score": 0.9998,
#     "all_predictions": [...]
#   }
# }
```

### 8. Named Entity Recognition (NER)

```powershell
$body = @{
  text = "I bought an iPhone 15 from Amazon in New York"
  task = "ner"
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/api/text/analyze" `
  -Body $body `
  -ContentType "application/json"

# Expected:
# {
#   "status": "ok",
#   "task": "ner",
#   "result": [
#     {"entity": "ORG", "word": "Amazon", "score": 0.99},
#     {"entity": "LOC", "word": "New York", "score": 0.98}
#   ]
# }
```

### 9. Text Summarization

```powershell
$body = @{
  text = "Long product description here... [500+ words]"
  task = "summarize"
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/api/text/analyze" `
  -Body $body `
  -ContentType "application/json"

# Expected:
# {
#   "status": "ok",
#   "task": "summarize",
#   "result": {"summary": "Brief summary of the text..."}
# }
```

### 10. Text Embeddings

```powershell
$body = @{
  texts = @(
    "smartphone with great camera",
    "laptop for programming"
  )
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/api/embeddings" `
  -Body $body `
  -ContentType "application/json"

# Expected:
# {
#   "status": "ok",
#   "embeddings": [
#     [0.123, -0.456, ...],  # 384-dimensional vector
#     [0.789, -0.012, ...]
#   ],
#   "count": 2
# }
```

### 11. Voice Transcription

```powershell
curl -Method POST `
  -Uri "http://localhost:8000/api/voice/transcribe" `
  -Form @{file=Get-Item "hello.wav"; language="en"}

# Expected:
# {
#   "status": "ok",
#   "transcript": "Hello, I'm looking for a new phone",
#   "language": "en",
#   "processing_time": 1.23
# }
```

### 12. CAPTCHA Solve

```powershell
$base64img = [Convert]::ToBase64String([IO.File]::ReadAllBytes("captcha.png"))
$body = @{
  site = "https://example.com"
  image_base64 = "data:image/png;base64,$base64img"
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/api/captcha/solve" `
  -Body $body `
  -ContentType "application/json"

# Expected:
# {
#   "status": "ok",
#   "solution": "ABC123"
# }
```

---

## 📊 Service Statistics

```powershell
# Get performance metrics
curl http://localhost:8000/health/stats | ConvertFrom-Json

# Expected:
# {
#   "status": "ok",
#   "stats": {
#     "huggingface": {
#       "configured": true,
#       "requests_total": 42,
#       "errors_total": 0,
#       "avg_latency_seconds": 1.234
#     },
#     "voice_stt": {
#       "provider": "local",
#       "transcriptions_total": 10,
#       "avg_processing_time": 2.1
#     },
#     "image_processor": {
#       "images_processed": 100,
#       "avg_processing_time": 3.5
#     }
#   }
# }
```

---

## 🔧 Debugging & Troubleshooting

### HuggingFace API Issues

**Problem**: "HuggingFace API not configured"
```powershell
# Check API key
docker exec test_model-web-1 printenv HF_API_KEY
# Should output: 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

# Test HF connection
docker exec test_model-web-1 python -c "from app.services.huggingface_connector import get_hf_connector; import asyncio; print(asyncio.run(get_hf_connector().health_check()))"
```

**Problem**: Rate limits (HTTP 429)
- HF implements automatic retry with exponential backoff
- Check logs for retry attempts
- Consider upgrading HF account or using cached responses

### Voice STT Issues

**Problem**: "Whisper model not loaded"
```powershell
# Check provider
docker exec test_model-web-1 printenv VOICE_STT_PROVIDER
# Should be: local or hf

# Test Whisper
docker exec test_model-web-1 python -c "from faster_whisper import WhisperModel; m = WhisperModel('base'); print('OK')"
```

**Problem**: Slow transcription
- Use smaller model: `WHISPER_MODEL_SIZE=tiny` or `base`
- Enable int8 quantization: `WHISPER_COMPUTE_TYPE=int8`

### CLIP/Image Processing Issues

**Problem**: "CLIP service not available"
```powershell
# Check CLIP initialization
docker logs test_model-web-1 | Select-String "CLIP"
# Look for: ✅ CLIP service ready

# Verify CLIP model files
docker exec test_model-web-1 ls -la models/
```

**Problem**: Out of memory
- Reduce batch sizes in image processing
- Use CPU instead of GPU if memory constrained
- Process images sequentially instead of parallel

### CAPTCHA Service Issues

**Problem**: "CAPTCHA service unreachable"
```powershell
# Check CAPTCHA container
docker ps | Select-String "captcha"

# Check CAPTCHA logs
docker logs test_model-captcha-1 --tail 50

# Test direct connection
curl http://localhost:9001/health
```

---

## 🎯 Success Criteria

✅ **All systems operational when:**

1. `/health/services` returns HTTP 200 with all services `"healthy": true`
2. Image upload + analysis completes in < 10 seconds
3. CLIP search returns relevant matches with scores > 0.5
4. Text generation produces coherent responses
5. Voice transcription accuracy > 90% on clear audio
6. Barcode detection works on standard retail products
7. OCR extracts text from receipts with reasonable accuracy
8. CAPTCHA solver achieves > 70% success rate

---

## 📈 Performance Benchmarks

| Operation | Target Time | Acceptable Range |
|-----------|-------------|------------------|
| Image Upload | < 500ms | 100ms - 1s |
| CLIP Search | < 2s | 1s - 5s |
| Barcode Decode | < 1s | 500ms - 3s |
| OCR Extract | < 3s | 1s - 5s |
| Text Generation | < 5s | 2s - 10s |
| Sentiment Analysis | < 1s | 500ms - 3s |
| Voice Transcription (30s audio) | < 10s | 5s - 20s |
| CAPTCHA Solve | < 30s | 10s - 60s |

---

## 🔄 Fallback Options

### If HuggingFace API Fails:
- Text generation: Use local GPT-2 or smaller models
- Sentiment: Fallback to VADER (already implemented)
- Embeddings: Use local sentence-transformers models

### If Voice STT Fails:
- Switch from `local` to `hf` provider (or vice versa)
- Use smaller Whisper models (tiny, base instead of large)
- Implement queue system for async processing

### If CLIP Fails:
- Use YOLO object detection + text matching as fallback
- Implement simple feature matching with ORB/SIFT

### If OCR Fails:
- Try both EasyOCR and Tesseract
- Apply different preprocessing techniques
- Request manual review for critical receipts

---

## 📝 Monitoring Dashboard

Access Prometheus metrics at `http://localhost:9090`

Key metrics to monitor:
- `hf_inference_seconds` - HF API latency
- `clip_search_seconds` - CLIP search time
- `yolo_detection_seconds` - Object detection time
- `stt_transcription_seconds` - Voice transcription time
- `barcode_decode_seconds` - Barcode detection time

---

## 🚀 Next Steps

1. **Frontend Integration**
   - Wire camera upload UI to `/api/images/upload`
   - Display CLIP matches in product grid
   - Show voice transcription in search bar

2. **Performance Optimization**
   - Implement Redis caching for HF responses
   - Batch similar requests to HF API
   - Use FAISS for faster vector search

3. **Production Deployment**
   - Configure HF API rate limiting
   - Set up model caching/CDN
   - Enable GPU acceleration if available
   - Implement health check auto-restart

---

## 📞 Support

For issues:
1. Check logs: `docker logs test_model-web-1 --tail 100`
2. Verify environment variables
3. Test individual components with health checks
4. Review this guide's debugging section

Last Updated: 2025-10-22
