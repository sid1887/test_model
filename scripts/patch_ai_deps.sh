#!/bin/bash

# Create more direct fixes for specific issues
cat > /tmp/direct_fixes.py << 'EOF'
# Fix the analysis.py file
try:
    with open('/app/app/api/routes/analysis.py', 'r') as f:
        content = f.read()
    
    # Replace problematic imports with try/except blocks
    if 'from app.services.clip_search' in content:
        content = content.replace(
            'from app.services.clip_search',
            'try:\n    from app.services.clip_search\nexcept ImportError:\n    pass'
        )
    
    with open('/app/app/api/routes/analysis.py', 'w') as f:
        f.write(content)
    print("Fixed analysis.py file")
except Exception as e:
    print(f"Error fixing analysis.py: {e}")

# Fix other AI imports
try:
    with open('/app/app/core/gpu_memory.py', 'r') as f:
        content = f.read()
    
    if 'import torch' in content and 'try:' not in content.split('import torch')[0].splitlines()[-1]:
        content = content.replace(
            'import torch',
            'try:\n    import torch\nexcept ImportError:\n    torch = None'
        )
    
    with open('/app/app/core/gpu_memory.py', 'w') as f:
        f.write(content)
    print("Fixed gpu_memory.py file")
except Exception as e:
    print(f"Error fixing gpu_memory.py: {e}")

# Fix ai_models.py
try:
    with open('/app/app/services/ai_models.py', 'r') as f:
        content = f.read()
    
    # Add multiple try/except blocks
    imports_to_fix = {
        'import cv2': 'try:\n    import cv2\nexcept ImportError:\n    cv2 = None',
        'from ultralytics import YOLO': 'try:\n    from ultralytics import YOLO\nexcept ImportError:\n    YOLO = None',
        'import clip': 'try:\n    import clip\nexcept ImportError:\n    clip = None',
        'import torch': 'try:\n    import torch\nexcept ImportError:\n    torch = None',
        'import torchvision': 'try:\n    import torchvision\nexcept ImportError:\n    torchvision = None'
    }
    
    for orig, replacement in imports_to_fix.items():
        if orig in content and 'try:' not in content.split(orig)[0].splitlines()[-1]:
            content = content.replace(orig, replacement)
    
    with open('/app/app/services/ai_models.py', 'w') as f:
        f.write(content)
    print("Fixed ai_models.py file")
except Exception as e:
    print(f"Error fixing ai_models.py: {e}")
EOF

# Run the direct fixes
python /tmp/direct_fixes.py

# Install critical packages
pip install asyncpg==0.29.0 aiofiles==23.2.0 python-dotenv==1.0.0

# Clean up
rm /tmp/direct_fixes.py
