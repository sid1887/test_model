#!/usr/bin/env python3
"""
Quick Markdown Linting Fix Script
Fixes common Markdown linting issues automatically
"""

import re
import os
from pathlib import Path

def fix_markdown_file(file_path):
    """Fix common markdown linting issues in a file"""
    print(f"Processing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix MD022: Add blank lines around headings
        # Add blank line before headings (except first line)
        content = re.sub(r'(?<!^)(?<!\n\n)(^#{1,6}\s)', r'\n\1', content, flags=re.MULTILINE)
        
        # Add blank line after headings
        content = re.sub(r'(^#{1,6}\s.*$)(?!\n\n)', r'\1\n', content, flags=re.MULTILINE)
        
        # Fix MD032: Add blank lines around lists
        # Add blank line before lists
        content = re.sub(r'(?<!\n)(\n[-*+]\s)', r'\n\1', content)
        content = re.sub(r'(?<!\n)(\n\d+\.\s)', r'\n\1', content)
        
        # Add blank line after lists (before non-list content)
        content = re.sub(r'(^[-*+]\s.*$)(?=\n[^-*+\s\n])', r'\1\n', content, flags=re.MULTILINE)
        content = re.sub(r'(^\d+\.\s.*$)(?=\n[^\d\s\n])', r'\1\n', content, flags=re.MULTILINE)
        
        # Fix MD031: Add blank lines around fenced code blocks
        content = re.sub(r'(?<!\n\n)(^```)', r'\n\1', content, flags=re.MULTILINE)
        content = re.sub(r'(^```)(?!\n\n)', r'\1\n', content, flags=re.MULTILINE)
        
        # Fix MD026: Remove trailing punctuation from headings
        content = re.sub(r'(^#{1,6}\s.*[.,:;!])$', lambda m: m.group(1)[:-1], content, flags=re.MULTILINE)
        
        # Fix MD009: Remove trailing spaces
        content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
        
        # Fix MD040: Add language to fenced code blocks (where obvious)
        content = re.sub(r'^```$', '```text', content, flags=re.MULTILINE)
        
        # Fix MD036: Bold text shouldn't be used as headings
        content = re.sub(r'^\*\*(.*)\*\*$', r'### \1', content, flags=re.MULTILINE)
        
        # Clean up excessive blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Ensure file ends with single newline
        content = content.rstrip() + '\n'
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Fixed {file_path}")
            return True
        else:
            print(f"  ✨ No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")
        return False

def main():
    """Fix markdown files in the current directory"""
    print("🔧 Fixing Markdown linting issues...")
    
    # Get all markdown files
    md_files = list(Path('.').rglob('*.md'))
    
    fixed_count = 0
    for md_file in md_files:
        # Skip node_modules and other build directories
        if any(part in str(md_file) for part in ['node_modules', '.git', 'dist', 'build']):
            continue
            
        if fix_markdown_file(md_file):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} out of {len(md_files)} markdown files")

if __name__ == "__main__":
    main()
