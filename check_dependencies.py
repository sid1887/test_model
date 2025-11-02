#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check for circular imports and missing dependencies
"""
import os
import re
import sys
from pathlib import Path
from collections import defaultdict, deque

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def get_imports(file_path):
    """Extract imports from a Python file"""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Match: from app.xxx import yyy
        from_imports = re.findall(r'from\s+(app\.[^\s]+)\s+import', content)
        imports.extend(from_imports)
        
        # Match: import app.xxx
        direct_imports = re.findall(r'(?:^|\n)import\s+(app\.[^\s,]+)', content)
        imports.extend(direct_imports)
        
    except Exception as e:
        pass
    
    return imports

def build_dependency_graph():
    """Build dependency graph of all Python modules"""
    root = Path('d:/dev_packages/test_model')
    graph = defaultdict(set)
    module_files = {}
    
    for py_file in root.rglob('*.py'):
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        # Convert file path to module name
        rel_path = py_file.relative_to(root)
        module = str(rel_path.with_suffix('')).replace(os.sep, '.')
        
        if module.startswith('app.'):
            module_files[module] = py_file
            imports = get_imports(py_file)
            
            for imp in imports:
                # Normalize import (remove .router, etc)
                imp_module = imp.split('.router')[0].split('.py')[0]
                graph[module].add(imp_module)
    
    return graph, module_files

def find_circular_dependencies(graph):
    """Find circular dependencies using DFS"""
    circles = []
    
    def dfs(node, path, visited):
        if node in path:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            circles.append(cycle)
            return
        
        if node in visited:
            return
        
        visited.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            dfs(neighbor, path[:], visited)
    
    visited = set()
    for node in graph:
        if node not in visited:
            dfs(node, [], visited)
    
    return circles

def check_missing_modules(graph, module_files):
    """Check for imports that don't exist"""
    missing = []
    
    for module, imports in graph.items():
        for imp in imports:
            # Check if imported module exists
            if imp.startswith('app.') and imp not in module_files:
                # Check if it's a package (has __init__.py)
                package_path = Path('d:/dev_packages/test_model') / imp.replace('.', os.sep)
                init_file = package_path / '__init__.py'
                
                if not init_file.exists() and not (package_path.parent / f"{package_path.name}.py").exists():
                    missing.append((module, imp))
    
    return missing

print("[CHECK] Building dependency graph...")
graph, module_files = build_dependency_graph()
print(f"Found {len(module_files)} Python modules")

print("\n[CHECK] Looking for circular dependencies...")
circles = find_circular_dependencies(graph)

if circles:
    print(f"\n[ERROR] Found {len(circles)} circular dependency chains:\n")
    for i, circle in enumerate(circles[:5], 1):  # Show first 5
        print(f"  {i}. {' -> '.join(circle)}")
    if len(circles) > 5:
        print(f"  ... and {len(circles) - 5} more")
else:
    print("[OK] No circular dependencies found!")

print("\n[CHECK] Looking for missing module imports...")
missing = check_missing_modules(graph, module_files)

if missing:
    print(f"\n[ERROR] Found {len(missing)} missing module imports:\n")
    seen = set()
    for module, imp in missing[:10]:  # Show first 10
        if imp not in seen:
            seen.add(imp)
            print(f"  - {imp}")
            print(f"      imported by: {module}")
    if len(missing) > 10:
        print(f"  ... and {len(missing) - 10} more")
else:
    print("[OK] All imported modules exist!")

# Check for common import issues
print("\n[CHECK] Checking for common issues...")
issues = []

# Check if main.py imports all route modules
main_file = Path('d:/dev_packages/test_model/main.py')
if main_file.exists():
    with open(main_file, 'r') as f:
        main_content = f.read()
    
    route_modules = [m for m in module_files if m.startswith('app.api.routes.') and not m.endswith('.__init__')]
    for route_mod in route_modules:
        route_name = route_mod.split('.')[-1]
        if route_name not in main_content and route_name not in ['__init__', 'metrics']:
            issues.append(f"Route module '{route_name}' might not be imported in main.py")

if issues:
    print(f"\n[WARN] Found {len(issues)} potential issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("[OK] No common issues found!")

print("\n" + "="*60)
if not circles and not missing:
    print("[SUCCESS] All dependency checks passed!")
    sys.exit(0)
else:
    print("[FAILED] Some checks failed - review above")
    sys.exit(1)
