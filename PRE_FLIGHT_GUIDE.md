# Pre-flight Dependency Check System for Cumpair

This system prevents the frustrating cycle of discovering missing packages after a long Docker build. Instead of having to rebuild your entire container for a single missing package, the pre-flight check identifies and installs missing dependencies before your application starts.

## 🚀 Quick Start

### Option 1: Run Pre-flight Check Separately
```bash
# Basic check and auto-install missing packages
python pre_flight_check.py

# Quick check (critical packages only)
python pre_flight_check.py --quick

# Force reinstall packages
python pre_flight_check.py --force

# Verbose output
python pre_flight_check.py --verbose
```

### Option 2: Use Enhanced Startup Script
```bash
# Start with pre-flight check included
python safe_start.py

# Development mode with auto-reload
python safe_start.py --dev

# Quick check mode
python safe_start.py --quick-check

# Skip pre-flight (not recommended)
python safe_start.py --skip-preflight
```

### Option 3: PowerShell Wrapper (Windows)
```powershell
# Basic check
.\pre-flight-check.ps1

# Docker mode
.\pre-flight-check.ps1 -DockerMode

# Force reinstall with verbose output
.\pre-flight-check.ps1 -Force -Verbose

# Skip optional packages
.\pre-flight-check.ps1 -SkipOptional
```

## 🔧 How It Works

The pre-flight check system:

1. **Identifies Missing Packages**: Safely attempts to import each required package
2. **Auto-Installation**: Uses pip to install missing packages with proper error handling
3. **Special Handling**: Handles complex packages like PyTorch, CLIP, and OpenCV
4. **Graceful Failures**: Distinguishes between critical and optional packages
5. **Emergency Fallback**: Creates an emergency requirements file for manual installation

### Package Categories

#### Critical Packages (Application won't start without these)
- fastapi, uvicorn, pydantic
- sqlalchemy, asyncpg, redis, celery
- numpy, pillow

#### AI/ML Packages (Core AI features)
- torch, torchvision, ultralytics
- transformers, sentence-transformers
- clip-by-openai, faiss-cpu
- opencv-python, scikit-learn

#### Scraping Packages (Web scraping features)
- scrapy, playwright, requests
- aiohttp, beautifulsoup4, selenium

#### Database Packages
- alembic, psycopg2-binary

#### Utility Packages
- python-multipart, aiofiles, httpx
- prometheus-client, structlog

## 🐳 Docker Integration

### Enhanced Dockerfile
Use the enhanced Dockerfile that includes pre-flight checks:

```bash
# Build with enhanced Dockerfile
docker build -f Dockerfile.enhanced -t cumpair:enhanced .

# Run with pre-flight check
docker run -p 8000:8000 cumpair:enhanced
```

### Existing Container
Run pre-flight check in your existing running container:

```bash
# Copy pre-flight script to container
docker cp pre_flight_check.py compair_web:/app/

# Run pre-flight check inside container
docker exec compair_web python pre_flight_check.py --docker

# Or use PowerShell wrapper
.\pre-flight-check.ps1 -DockerMode
```

## 📊 Features

### Smart Package Detection
- **Import Testing**: Actually attempts to import packages to verify they work
- **Special Cases**: Handles packages with different import names (opencv-python → cv2)
- **Version Compatibility**: Works with various package versions

### Robust Installation
- **Timeout Protection**: Prevents hanging on slow installations
- **Error Recovery**: Continues processing other packages if one fails
- **Verification**: Re-tests imports after installation

### Comprehensive Reporting
- **Progress Tracking**: Shows what's being installed in real-time
- **Success Summary**: Lists successfully installed packages
- **Failure Analysis**: Details what failed and why
- **Health Report**: Generates JSON report for analysis

### Emergency Fallback
- **Emergency Requirements**: Creates `emergency_requirements.txt` for manual installation
- **Health Report**: Saves detailed analysis to `pre_flight_health_report.json`
- **Graceful Degradation**: Allows application to start even with non-critical failures

## 🛠️ Advanced Usage

### Custom Package Lists
You can modify the package lists in `pre_flight_check.py`:

```python
# Add your custom packages
CUSTOM_PACKAGES = [
    "your-package-here",
    "another-package"
]

# Add to existing categories
AI_PACKAGES.extend(CUSTOM_PACKAGES)
```

### Environment-Specific Checks
```bash
# Production environment
python pre_flight_check.py --skip-optional

# Development environment  
python pre_flight_check.py --force --verbose

# CI/CD environment
python pre_flight_check.py --quick
```

### Integration with Existing Scripts
```python
from pre_flight_check import PreFlightChecker

def your_startup_function():
    checker = PreFlightChecker()
    if not checker.run_complete_check():
        print("Dependencies missing!")
        return False
    
    # Start your application
    start_application()
```

## 🔍 Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Linux/Mac
sudo python pre_flight_check.py

# Windows (Run as Administrator)
python pre_flight_check.py
```

#### Network Issues
```bash
# Use different index URL
pip install --index-url https://pypi.org/simple/ <package>

# Or use pre-flight with proxy
export https_proxy=your-proxy:port
python pre_flight_check.py
```

#### PyTorch Installation Issues
The script automatically installs CPU version of PyTorch for compatibility. For GPU support:

```bash
# After pre-flight check, manually install GPU version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### CLIP Installation Issues
If CLIP fails to install from GitHub:

```bash
# Manual installation
pip install git+https://github.com/openai/CLIP.git
# or
pip install clip-by-openai
```

### Recovery Procedures

#### If Pre-flight Check Fails
1. Check the `emergency_requirements.txt` file
2. Install packages manually: `pip install -r emergency_requirements.txt`
3. Run the check again with `--force` flag

#### If Application Still Won't Start
1. Run health check: `python pre_flight_check.py --verbose`
2. Check the health report: `pre_flight_health_report.json`
3. Verify critical packages are working:
   ```python
   python -c "import fastapi, torch, clip; print('All critical packages working!')"
   ```

## 📈 Monitoring

### Health Reports
The system generates detailed health reports in JSON format:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "python_version": "3.11.0",
  "installed_packages": ["package1", "package2"],
  "failed_packages": ["package3"],
  "success_rate": 95.5
}
```

### Integration with CI/CD
```yaml
# GitHub Actions example
- name: Pre-flight Check
  run: |
    python pre_flight_check.py --quick
    if [ $? -ne 0 ]; then
      echo "Pre-flight check failed"
      exit 1
    fi
```

## 🎯 Best Practices

1. **Always Run Pre-flight**: Make it part of your startup routine
2. **Use Quick Mode in Production**: `--quick` for faster startup
3. **Regular Health Checks**: Run periodically to catch dependency drift
4. **Version Control**: Keep `emergency_requirements.txt` in your repo
5. **Docker Integration**: Use enhanced Dockerfile for container deployments

## 🤝 Contributing

The pre-flight check system is designed to be easily extensible. To add support for new packages or improve detection logic, modify the `PreFlightChecker` class in `pre_flight_check.py`.

---

**This system eliminates the frustrating cycle of discovering missing packages after long build times. Your application dependencies are checked and resolved before startup, saving you time and ensuring reliable deployments.**
