#!/bin/bash

# ProxyManager Complete Fix Script
# This script fixes the ProxyManager instantiation issue

echo "🔧 FIXING PROXYMANAGER INSTANTIATION"
echo "===================================="

# Create a comprehensive fix
cat > /tmp/fix_proxymanager_complete.py << 'EOF'
import re

# Read the file
with open('/app/app/services/scraping.py', 'r') as f:
    content = f.read()

# Fix 1: Replace ProxyManager() with proper instantiation using internal proxy
# Use our internal proxy service at proxy:8001
old_pattern = r'self\.proxy_manager = ProxyManager\(\)'
new_replacement = '''try:
            # Use our internal proxy service
            proxy_url = "http://proxy:8001"
            from urllib3.poolmanager import ProxyManager
            self.proxy_manager = ProxyManager(proxy_url)
            print(f"✅ ProxyManager initialized with internal proxy: {proxy_url}")
        except Exception as e:
            # Fallback to regular PoolManager if proxy fails
            print(f"⚠️ Proxy setup failed, using direct connection: {e}")
            from urllib3.poolmanager import PoolManager
            self.proxy_manager = PoolManager()'''

# Apply the fix
content = re.sub(old_pattern, new_replacement, content)

# Write back to file
with open('/app/app/services/scraping.py', 'w') as f:
    f.write(content)

print("✅ ProxyManager instantiation fixed")
EOF

# Run the fix
python /tmp/fix_proxymanager_complete.py

echo "🔍 Verifying the fix..."
grep -A 10 "proxy_manager =" /app/app/services/scraping.py | head -15

echo "✅ ProxyManager complete fix applied!"
