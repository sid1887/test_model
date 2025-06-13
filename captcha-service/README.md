# Self-Hosted Captcha Solving Service

This is a self-hosted captcha solving service that provides a 2captcha-compatible API for solving text-based captchas using multiple OCR engines.

## Features

- **2captcha API Compatible**: Drop-in replacement for 2captcha service

- **Multiple OCR Engines**: Uses Tesseract and EasyOCR with fallback support

- **Enhanced Preprocessing**: Advanced image preprocessing for better accuracy

- **Redis Queue**: Async task processing with Redis backend

- **Health Monitoring**: Built-in health checks and statistics

- **Docker Support**: Complete containerized solution

## Quick Start

### Option 1: Docker Compose (Recommended)

```text
bash
cd captcha-service
docker-compose up -d

```text

This will start:

- Captcha solving service on port 9001

- Redis server on port 6380

### Option 2: Manual Setup

```text
bash
# Install system dependencies (Ubuntu/Debian)

sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Install Python dependencies

pip install -r requirements.txt

# Start Redis (if not running)

redis-server --port 6380

# Start the service

python app.py

```text

## API Endpoints

### Submit Captcha

```text
http
POST /in.php
Content-Type: application/x-www-form-urlencoded

method=base64&body=<base64_encoded_image>

```text

Response:

```text
json
{
  "status": 1,
  "request": "task_id_here"
}

```text

### Get Result

```text
http
GET /res.php?action=get&id=<task_id>

```text

Response (ready):

```text
json
{
  "status": 1,
  "request": "SOLVED_TEXT"
}

```text

Response (processing):

```text
json
{
  "status": 0,
  "request": "CAPCHA_NOT_READY"
}

```text

### Health Check

```text
http
GET /health

```text

### Statistics

```text
http
GET /stats

```text

## Integration with Cumpair

Update your Cumpair configuration:

```text
python
# In app/core/config.py or .env

CAPTCHA_SERVICE_URL=http://localhost:9001

```text

The Cumpair system will automatically use this self-hosted service for captcha solving.

## OCR Engines

### Tesseract

- Always available in Docker container

- Multiple preprocessing techniques

- Various PSM (Page Segmentation Mode) configurations

### EasyOCR

- Neural network-based OCR

- Better accuracy for complex captchas

- GPU support available (disabled by default for stability)

## Performance Tuning

### For better accuracy

1. **Image Quality**: Ensure captcha images are clear and high contrast

2. **Preprocessing**: The service automatically applies multiple preprocessing techniques

3. **Multiple Engines**: Fallback chain ensures best possible results

### For better speed

1. **GPU Support**: Enable GPU for EasyOCR in production

2. **Worker Scaling**: Increase Gunicorn workers in Docker

3. **Redis Optimization**: Tune Redis configuration for your workload

## Monitoring

### Health Endpoint

Monitor service health at `/health`:

```text
bash
curl http://localhost:9001/health

```text

### Statistics

Get service statistics at `/stats`:

```text
bash
curl http://localhost:9001/stats

```text

### Logs

View Docker logs:

```text
bash
docker-compose logs -f captcha-solver

```text

## Error Codes

| Code | Description |
|------|-------------|
| `ERROR_CAPTCHA_UNSOLVABLE` | Could not solve the captcha |
| `ERROR_IMAGE_TYPE` | Invalid image format |
| `ERROR_WRONG_METHOD` | Unsupported solving method |
| `ERROR_INTERNAL` | Internal server error |

## Security Considerations

1. **Network Access**: Restrict access to trusted networks only

2. **Resource Limits**: Monitor CPU/memory usage

3. **Rate Limiting**: Implement rate limiting if needed

4. **Image Cleanup**: Temporary images are automatically cleaned up

## Troubleshooting

### Service won't start

- Check if ports 9001 and 6380 are available

- Verify Docker is running

- Check logs for specific errors

### Poor accuracy

- Verify image quality is good

- Check if all OCR engines are initialized

- Monitor preprocessing steps in logs

### High resource usage

- Reduce number of workers

- Disable GPU if not needed

- Implement request rate limiting

## Development

### Adding new OCR engines

1. Add engine initialization in `init_ocr_engines()`

2. Add solving method in `CaptchaSolver` class

3. Update the methods list

### Custom preprocessing

Modify the preprocessing techniques in `_solve_with_tesseract_enhanced()` for your specific captcha types.

## License

This service is part of the Cumpair project and follows the same license terms.
