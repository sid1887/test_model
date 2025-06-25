#!/bin/bash

# Create more direct fixes for specific issues
cat > /tmp/improved_fixes.py << 'EOF'
# Fix the analysis.py file
try:
    with open('/app/app/api/routes/analysis.py', 'r') as f:
        content = f.read()
    
    # Replace problematic imports with try/except blocks
    if 'from app.services.clip_search' in content:
        # Ensure proper indentation and complete the import statement
        content = content.replace(
            'from app.services.clip_search',
            'try:\n    from app.services.clip_search import search_clip_index, rebuild_clip_index\nexcept ImportError:\n    # Define fallback functions\n    def search_clip_index(*args, **kwargs):\n        return {"error": "CLIP module not available"}\n    \n    def rebuild_clip_index(*args, **kwargs):\n        return {"error": "CLIP module not available"}'
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
    
    if 'import torch' in content:
        content = content.replace(
            'import torch',
            'try:\n    import torch\nexcept ImportError:\n    torch = None'
        )
    
    # Replace any function that uses torch with safe versions
    if 'def get_gpu_memory():' in content:
        content = content.replace(
            'def get_gpu_memory():',
            'def get_gpu_memory():\n    if torch is None:\n        return {"error": "PyTorch not available"}\n    try:'
        )
        # Add an except block after the function body
        content = content.replace(
            'return memory_info',
            'return memory_info\n    except Exception:\n        return {"error": "GPU memory check failed"}'
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
    
    # Wrap class methods in try/except blocks
    if 'class AIModels:' in content:
        # Find all method definitions
        lines = content.splitlines()
        in_class = False
        for i, line in enumerate(lines):
            if 'class AIModels:' in line:
                in_class = True
            if in_class and line.strip().startswith('def ') and 'self' in line:
                # Add try/except to method body if not already there
                method_name = line.split('def ')[1].split('(')[0]
                indent = line.split('def')[0]
                # Check if next line already has a try
                if i+1 < len(lines) and 'try:' not in lines[i+1]:
                    lines[i+1] = f"{indent}    try:\n{indent}        {lines[i+1].strip()}"
                    
                    # Find the end of the method to add except block
                    j = i + 2
                    while j < len(lines) and (lines[j].startswith(indent + '    ') or not lines[j].strip()):
                        j += 1
                    
                    # Insert except block before the next method or end of class
                    except_block = f"{indent}    except Exception as e:\n{indent}        logger.error(f\"Error in {method_name}: {{e}}\")\n{indent}        return {{'error': f'AI model error in {method_name}: {{e}}'}}"
                    lines.insert(j, except_block)
        
        content = '\n'.join(lines)
    
    with open('/app/app/services/ai_models.py', 'w') as f:
        f.write(content)
    print("Fixed ai_models.py file")
except Exception as e:
    print(f"Error fixing ai_models.py: {e}")

# Fix clip_search.py if it exists
try:
    if os.path.exists('/app/app/services/clip_search.py'):
        with open('/app/app/services/clip_search.py', 'r') as f:
            content = f.read()
        
        # Add try/except for all imports
        imports_to_fix = {
            'import clip': 'try:\n    import clip\nexcept ImportError:\n    clip = None',
            'import torch': 'try:\n    import torch\nexcept ImportError:\n    torch = None',
            'import numpy as np': 'try:\n    import numpy as np\nexcept ImportError:\n    np = None'
        }
        
        for orig, replacement in imports_to_fix.items():
            if orig in content and 'try:' not in content.split(orig)[0].splitlines()[-1]:
                content = content.replace(orig, replacement)
        
        # Add checks for None at the start of functions
        functions = ['search_clip_index', 'rebuild_clip_index']
        for func in functions:
            if f'def {func}(' in content:
                # Add check for None modules
                func_start = content.find(f'def {func}(')
                func_body_start = content.find(':', func_start) + 1
                indent = '    ' # Assume 4-space indentation
                
                # Determine indentation from first non-empty line after function definition
                for line in content[func_body_start:].splitlines():
                    if line.strip():
                        indent = line[:len(line) - len(line.lstrip())]
                        break
                
                check_code = f"\n{indent}if clip is None or torch is None or np is None:\n{indent}    return {{'error': 'Required AI modules not available'}}\n"
                
                # Insert check after function definition
                content = content[:func_body_start] + check_code + content[func_body_start:]
        
        with open('/app/app/services/clip_search.py', 'w') as f:
            f.write(content)
        print("Fixed clip_search.py file")
except Exception as e:
    print(f"Error fixing clip_search.py: {e}")

# Add missing imports in the script
import os
EOF

# Run the direct fixes
python /tmp/improved_fixes.py

# Install critical packages
pip install asyncpg==0.29.0 aiofiles==23.2.0 python-dotenv==1.0.0

# Clean up
rm /tmp/improved_fixes.py
