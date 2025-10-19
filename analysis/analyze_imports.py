import ast
import os
import sys
from pathlib import Path
from collections import defaultdict

def extract_imports(file_path):
    """Extract all imports from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
        return imports
    except Exception as e:
        return []

def is_third_party(module_name):
    """Check if module is third-party (not stdlib or local)"""
    stdlib_modules = {
        'abc', 'asyncio', 'argparse', 'base64', 'collections', 'contextlib', 
        'copy', 'csv', 'dataclasses', 'datetime', 'decimal', 'email', 'enum',
        'functools', 'gc', 'glob', 'hashlib', 'io', 'itertools', 'json', 
        'logging', 'math', 'os', 'pathlib', 'pickle', 'platform', 're', 
        'shutil', 'sqlite3', 'statistics', 'string', 'subprocess', 'sys', 
        'tempfile', 'threading', 'time', 'typing', 'unittest', 'urllib', 
        'uuid', 'warnings', 'weakref', 'xml'
    }
    
    local_modules = {'app', 'tests', 'alembic', 'archive', 'scripts'}
    
    return module_name not in stdlib_modules and module_name not in local_modules

# Scan all Python files
project_root = Path('.')
all_imports = defaultdict(list)

for py_file in project_root.rglob('*.py'):
    if 'venv' in str(py_file) or 'node_modules' in str(py_file):
        continue
    
    imports = extract_imports(py_file)
    for imp in imports:
        if is_third_party(imp):
            all_imports[imp].append(str(py_file))

# Print results
print("\n" + "="*80)
print("THIRD-PARTY PACKAGES USED IN PROJECT")
print("="*80 + "\n")

# Common package name mappings
package_mappings = {
    'bs4': 'beautifulsoup4',
    'sklearn': 'scikit-learn',
    'cv2': 'opencv-python',
    'PIL': 'pillow',
    'yaml': 'pyyaml',
    'dotenv': 'python-dotenv',
    'psycopg2': 'psycopg2-binary',
}

packages = sorted(all_imports.keys())
print(f"Total unique third-party packages: {len(packages)}\n")

for pkg in packages:
    actual_pkg = package_mappings.get(pkg, pkg)
    file_count = len(set(all_imports[pkg]))
    print(f"  {pkg:30s} -> {actual_pkg:30s} (used in {file_count} files)")

print("\n" + "="*80)
print("COPY THIS LIST TO requirements.txt:")
print("="*80 + "\n")

for pkg in packages:
    actual_pkg = package_mappings.get(pkg, pkg)
    print(f"{actual_pkg}")

