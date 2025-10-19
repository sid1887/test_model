#!/bin/bash

# Fix AI Models Syntax Error
echo "🔧 FIXING AI_MODELS.PY SYNTAX ERROR"
echo "=================================="

# Create the fix
cat > /tmp/fix_ai_models_syntax.py << 'EOF'
# Read the file
with open('/app/app/services/ai_models.py', 'r') as f:
    content = f.read()

# Fix the syntax error - add newline between cv2 = None and YOLO = None
content = content.replace('cv2 = None    YOLO = None', 'cv2 = None\n    YOLO = None')

# Write back to file
with open('/app/app/services/ai_models.py', 'w') as f:
    f.write(content)

print("✅ AI models syntax error fixed")
EOF

# Run the fix
python /tmp/fix_ai_models_syntax.py

echo "🔍 Verifying the fix..."
sed -n '25,35p' /app/app/services/ai_models.py

echo "✅ AI models syntax fix applied!"
