#!/bin/bash

# ProxyManager Fix Script
# This script fixes the missing ProxyManager import in scraping.py

echo "🔧 FIXING PROXYMANAGER IMPORT ISSUE"
echo "===================================="

# Backup original file
cp /app/app/services/scraping.py /app/app/services/scraping.py.backup

# Add the missing import at the top of the file
echo "📝 Adding ProxyManager import..."

# Create a temporary file with the fix
cat > /tmp/fix_proxymanager.py << 'EOF'
import sys

# Read the original file
with open('/app/app/services/scraping.py', 'r') as f:
    content = f.read()

# Check if ProxyManager is already imported
if 'from urllib3.poolmanager import ProxyManager' not in content:
    # Find the import section and add the missing import
    lines = content.split('\n')
    
    # Find where to insert the import (after other urllib3 imports or with other imports)
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_index = i + 1
        elif line.strip() == '' and insert_index > 0:
            break
    
    # Insert the import
    lines.insert(insert_index, 'from urllib3.poolmanager import ProxyManager')
    
    # Write back to file
    with open('/app/app/services/scraping.py', 'w') as f:
        f.write('\n'.join(lines))
    
    print("✅ ProxyManager import added successfully")
else:
    print("✅ ProxyManager import already exists")
EOF

# Run the fix
python /tmp/fix_proxymanager.py

echo "🔍 Verifying the fix..."
grep -n "from urllib3.poolmanager import ProxyManager" /app/app/services/scraping.py

echo "✅ ProxyManager fix completed!"
