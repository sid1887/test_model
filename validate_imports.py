#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Import Validator
Checks ALL imports in the codebase for missing definitions
"""

import os
import re
import ast
import sys
from pathlib import Path
from collections import defaultdict

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def extract_imports(file_path):
    """Extract all imports from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('app.'):
                    for alias in node.names:
                        imports.append((node.module, alias.name))
        
        return imports
    except Exception as e:
        print(f"  ERROR parsing {file_path}: {e}")
        return []

def find_definitions(file_path):
    """Find all function/class definitions in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        definitions = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definitions.add(node.name)
            elif isinstance(node, ast.ClassDef):
                definitions.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        definitions.add(target.id)
        
        return definitions
    except Exception as e:
        return set()

def module_to_file(module_name):
    """Convert module name to file path"""
    parts = module_name.split('.')
    # app.core.events -> app/core/events.py
    base_path = Path('d:/dev_packages/test_model')
    file_path = base_path / '/'.join(parts) / '__init__.py'
    if not file_path.exists():
        file_path = base_path / '/'.join(parts[:-1]) / f"{parts[-1]}.py"
    return file_path if file_path.exists() else None

# Scan all Python files
print("🔍 Scanning Python files...")
python_files = list(Path('d:/dev_packages/test_model/app').rglob('*.py'))
print(f"Found {len(python_files)} files\n")

# Build module definitions map
print("📦 Building definitions map...")
module_defs = {}
for py_file in python_files:
    rel_path = py_file.relative_to('d:/dev_packages/test_model')
    module_name = str(rel_path).replace('\\', '.').replace('/', '.').replace('.py', '')
    defs = find_definitions(py_file)
    if defs:
        module_defs[module_name] = defs

# Check all imports
print("\n✅ Checking imports...\n")
missing_imports = defaultdict(list)
checked = 0

for py_file in python_files:
    imports = extract_imports(py_file)
    for module, name in imports:
        checked += 1
        if module in module_defs:
            if name not in module_defs[module] and name != '*':
                missing_imports[module].append((name, str(py_file)))

# Report
print(f"Checked {checked} imports\n")

if missing_imports:
    print(f"❌ Found {len(missing_imports)} modules with missing imports:\n")
    for module, items in sorted(missing_imports.items()):
        print(f"\n📄 {module}:")
        unique_missing = set(item[0] for item in items)
        for missing in sorted(unique_missing):
            files = [item[1] for item in items if item[0] == missing]
            print(f"  ✗ {missing}")
            for f in files[:3]:  # Show first 3 files
                print(f"      used in: {f}")
            if len(files) > 3:
                print(f"      ... and {len(files) - 3} more files")
else:
    print("✅ All imports validated successfully!")
