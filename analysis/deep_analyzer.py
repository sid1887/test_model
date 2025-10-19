import ast
import os
from pathlib import Path
from collections import defaultdict
import re

class DeepPackageAnalyzer(ast.NodeVisitor):
    """Analyze actual package usage, not just imports"""
    
    def __init__(self):
        self.imports = defaultdict(list)  # package -> [file, line, type]
        self.usage = defaultdict(list)     # package -> [file, line, usage]
        self.current_file = None
        self.import_aliases = {}  # alias -> original_name
        
    def visit_Import(self, node):
        for alias in node.names:
            pkg = alias.name.split('.')[0]
            alias_name = alias.asname or alias.name
            self.import_aliases[alias_name] = pkg
            self.imports[pkg].append({
                'file': str(self.current_file),
                'line': node.lineno,
                'type': 'import',
                'statement': f'import {alias.name}'
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            pkg = node.module.split('.')[0]
            for alias in node.names:
                alias_name = alias.asname or alias.name
                self.import_aliases[alias_name] = pkg
            self.imports[pkg].append({
                'file': str(self.current_file),
                'line': node.lineno,
                'type': 'from_import',
                'statement': f'from {node.module} import ...'
            })
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Track function/method calls to see actual usage"""
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in self.import_aliases:
                pkg = self.import_aliases[name]
                self.usage[pkg].append({
                    'file': str(self.current_file),
                    'line': node.lineno,
                    'usage': f'{name}(...)'
                })
        elif isinstance(node.func, ast.Attribute):
            # Handle pkg.function() calls
            if isinstance(node.func.value, ast.Name):
                name = node.func.value.id
                if name in self.import_aliases:
                    pkg = self.import_aliases[name]
                    self.usage[pkg].append({
                        'file': str(self.current_file),
                        'line': node.lineno,
                        'usage': f'{name}.{node.func.attr}(...)'
                    })
        self.generic_visit(node)

def is_third_party(pkg):
    """Enhanced third-party detection"""
    stdlib = {
        'abc', 'asyncio', 'argparse', 'base64', 'collections', 'concurrent',
        'contextlib', 'copy', 'csv', 'dataclasses', 'datetime', 'decimal', 
        'email', 'enum', 'functools', 'gc', 'glob', 'hashlib', 'importlib',
        'io', 'itertools', 'json', 'logging', 'math', 'os', 'pathlib', 
        'pickle', 'platform', 'py_compile', 'random', 're', 'shutil', 
        'sqlite3', 'statistics', 'string', 'subprocess', 'sys', 'tempfile', 
        'threading', 'time', 'traceback', 'typing', 'unittest', 'urllib', 
        'uuid', 'warnings', 'weakref', 'xml'
    }
    local = {'app', 'tests', 'alembic', 'archive', 'scripts', 
             'alembic_database', 'alembic_models_analysis', 
             'alembic_models_price_comparison', 'alembic_models_product',
             'analysis', 'main', 'pre_flight_check', 'price_comparison', 
             'product'}
    return pkg not in stdlib and pkg not in local

# Analyze all files
analyzer = DeepPackageAnalyzer()
project_root = Path('.')

print("="*80)
print("DEEP PACKAGE ANALYSIS - Scanning ALL Python files...")
print("="*80)

file_count = 0
for py_file in project_root.rglob('*.py'):
    if 'venv' in str(py_file) or 'node_modules' in str(py_file):
        continue
    
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(py_file))
            analyzer.current_file = py_file
            analyzer.visit(tree)
            file_count += 1
    except:
        pass

# Filter third-party packages
third_party_imports = {k: v for k, v in analyzer.imports.items() if is_third_party(k)}
third_party_usage = {k: v for k, v in analyzer.usage.items() if is_third_party(k)}

print(f"\nFiles analyzed: {file_count}")
print(f"Third-party packages imported: {len(third_party_imports)}")
print(f"Third-party packages ACTUALLY USED: {len(third_party_usage)}\n")

# Check for imported but never used
print("="*80)
print("PACKAGES IMPORTED BUT NEVER USED (Potentially Optional):")
print("="*80)
unused = []
for pkg in third_party_imports:
    if pkg not in third_party_usage:
        unused.append(pkg)
        files = list(set([imp['file'] for imp in third_party_imports[pkg]]))
        print(f"\n  {pkg}:")
        for f in files[:3]:  # Show first 3 files
            print(f"    - {f}")

if not unused:
    print("   ALL imported packages are actually used!")

# Detailed analysis of key packages
print("\n" + "="*80)
print("DETAILED USAGE ANALYSIS:")
print("="*80)

# Check specific packages
check_packages = ['spacy', 'gensim', 'tensorflow', 'easyocr', 'nltk']

for pkg in check_packages:
    print(f"\n {pkg.upper()}:")
    if pkg in third_party_imports:
        import_count = len(third_party_imports[pkg])
        usage_count = len(third_party_usage.get(pkg, []))
        files_imported = list(set([imp['file'] for imp in third_party_imports[pkg]]))
        
        print(f"   IMPORTED in {len(files_imported)} file(s):")
        for f in files_imported:
            print(f"     - {f}")
        
        if usage_count > 0:
            print(f"   ACTUALLY USED {usage_count} time(s):")
            for usage in third_party_usage[pkg][:5]:  # Show first 5 usages
                print(f"     - {usage['file']}:{usage['line']} -> {usage['usage']}")
        else:
            print(f"    IMPORTED but NO actual usage found!")
            print(f"   This package might be OPTIONAL")
    else:
        print(f"   NOT imported anywhere")
        print(f"   SAFE to comment out in requirements.txt")

print("\n" + "="*80)
