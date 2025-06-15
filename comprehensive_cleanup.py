#!/usr/bin/env python3
"""
Comprehensive Project Repository Cleanup Script
Based on the detailed analysis of file redundancy and organizational issues.
This script will clean up the repository while preserving essential files.
"""

import os
import shutil
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class RepositoryCleanup:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.cleanup_report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "actions": [],
            "preserved_files": [],
            "statistics": {}
        }
        
        # Create archive directories
        self.archive_dir = Path("archive")
        self.archive_dirs = {
            "docker": self.archive_dir / "docker-configs",
            "scripts": self.archive_dir / "scripts-obsolete", 
            "tests": self.archive_dir / "test-artifacts",
            "docs": self.archive_dir / "completion-docs",
            "assets": self.archive_dir / "test-assets",
            "backups": self.archive_dir / "backup-files"
        }
        
    def create_archive_structure(self):
        """Create archive directory structure"""
        for dir_path in self.archive_dirs.values():
            if not self.dry_run:
                dir_path.mkdir(parents=True, exist_ok=True)
            self.log_action("create_directory", str(dir_path))
    
    def log_action(self, action_type: str, file_path: str, reason: str = ""):
        """Log cleanup action"""
        self.cleanup_report["actions"].append({
            "type": action_type,
            "file": file_path,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        action_symbol = {
            "move": "📦",
            "delete": "🗑️", 
            "preserve": "✅",
            "create_directory": "📁",
            "consolidate": "🔄"
        }.get(action_type, "ℹ️")
        
        print(f"{action_symbol} {action_type.upper()}: {file_path}")
        if reason:
            print(f"   Reason: {reason}")
    
    def move_to_archive(self, file_path: Path, archive_subdir: str, reason: str):
        """Move file to archive directory"""
        if not file_path.exists():
            return
            
        target_dir = self.archive_dirs[archive_subdir]
        target_path = target_dir / file_path.name
        
        # Handle name conflicts
        counter = 1
        while target_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            target_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        if not self.dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), str(target_path))
        
        self.log_action("move", str(file_path), reason)
    
    def cleanup_docker_configs(self):
        """Phase 1: Docker Configuration Consolidation"""
        print("\n🐳 PHASE 1: Docker Configuration Cleanup")
        
        # Keep only essential Docker files
        essential_docker_files = {
            "docker-compose.complete.yml": "Primary comprehensive configuration",
            "docker-compose.yml": "Standard development configuration", 
            "Dockerfile": "Main application Dockerfile",
            "Dockerfile.production": "Production-optimized Dockerfile"
        }
        
        # Archive redundant Docker files
        redundant_patterns = [
            "docker-compose*.backup*",
            "docker-compose*-fixed*", 
            "docker-compose*.enhanced*",
            "docker-compose*.secure*",
            "Dockerfile.enhanced"
        ]
        
        for pattern in redundant_patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.name not in essential_docker_files:
                    self.move_to_archive(file_path, "docker", "Redundant Docker configuration")
        
        # Log preserved files
        for file_name, reason in essential_docker_files.items():
            if Path(file_name).exists():
                self.cleanup_report["preserved_files"].append({
                    "file": file_name,
                    "reason": reason
                })
                self.log_action("preserve", file_name, reason)
    
    def cleanup_scripts(self):
        """Phase 2: Script Rationalization"""
        print("\n📜 PHASE 2: Script Cleanup")
        
        # Essential scripts to keep
        essential_scripts = {
            "docker-start-secure-fixed.ps1": "Primary secure startup script",
            "docker-start.ps1": "Standard startup script",
            "pre_flight_check.py": "Essential validation script",
            "validate_fixes.py": "Optimization validation script"
        }
        
        # Archive redundant scripts
        redundant_script_patterns = [
            "*-new.ps1",
            "*-fixed.ps1", 
            "*-enhanced.ps1",
            "*-simple.ps1",
            "start-all*.ps1",
            "setup*.ps1",
            "enhanced-start*.ps1"
        ]
        
        for pattern in redundant_script_patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.name not in essential_scripts:
                    self.move_to_archive(file_path, "scripts", "Redundant or obsolete script")
        
        # Log preserved scripts
        for file_name, reason in essential_scripts.items():
            if Path(file_name).exists():
                self.cleanup_report["preserved_files"].append({
                    "file": file_name, 
                    "reason": reason
                })
                self.log_action("preserve", file_name, reason)
    
    def cleanup_test_files(self):
        """Phase 3: Test Infrastructure Cleanup"""
        print("\n🧪 PHASE 3: Test File Cleanup")
        
        # Essential test files to keep
        essential_tests = {
            "final_validation.py": "Primary validation script",
            "integration_test.py": "Core integration tests",
            "product_testing_suite.py": "Main product test suite"
        }
        
        # Archive redundant test files
        test_patterns = [
            "comprehensive_*test*.py",
            "*test*clean*.py", 
            "*test*fixed*.py",
            "simple_*test*.py",
            "quick_*test*.py",
            "real_data_test.py",
            "analytics_*test*.py"
        ]
        
        for pattern in test_patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.name not in essential_tests:
                    self.move_to_archive(file_path, "tests", "Redundant test file")
        
        # Clean up test result files
        result_patterns = [
            "*.json", 
            "*.csv",
            "*test_results*",
            "*validation_*.json"
        ]
        
        for pattern in result_patterns:
            for file_path in Path(".").glob(pattern):
                if any(keyword in file_path.name.lower() for keyword in ["test", "result", "validation", "summary"]):
                    if not file_path.name.startswith("requirements"):
                        self.move_to_archive(file_path, "tests", "Test result artifact")
    
    def cleanup_completion_docs(self):
        """Archive completion milestone documents"""
        print("\n📄 PHASE 4: Documentation Cleanup")
        
        completion_patterns = [
            "*COMPLETE*.md",
            "*ACCOMPLISHED*.md", 
            "STEP*_*.md",
            "*SUMMARY*.md"
        ]
        
        # Keep only the final remediation document
        essential_docs = {
            "REMEDIATION_COMPLETE.md": "Final comprehensive status",
            "README.md": "Main project documentation"
        }
        
        for pattern in completion_patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.name not in essential_docs:
                    self.move_to_archive(file_path, "docs", "Completion milestone document")
    
    def cleanup_backup_files(self):
        """Archive backup and variant files"""
        print("\n💾 PHASE 5: Backup File Cleanup")
        
        backup_patterns = [
            "*.backup*",
            "*_backup.*",
            "*_fixed.*",
            "*_updated.*",
            "Makefile.*"
        ]
        
        for pattern in backup_patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.name != "Makefile":  # Keep main Makefile
                    self.move_to_archive(file_path, "backups", "Backup or variant file")
    
    def cleanup_requirements_files(self):
        """Consolidate requirements files"""
        print("\n📦 PHASE 6: Requirements Cleanup")
        
        # Keep only essential requirements
        essential_reqs = {
            "requirements.txt": "Standard dependencies",
            "requirements_complete.txt": "Comprehensive dependencies"
        }
        
        req_patterns = ["requirements_*.txt", "emergency_requirements.txt"]
        
        for pattern in req_patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.name not in essential_reqs:
                    self.move_to_archive(file_path, "backups", "Redundant requirements file")
    
    def cleanup_test_assets(self):
        """Move test assets to proper location"""
        print("\n🖼️ PHASE 7: Test Assets Cleanup")
        
        test_image_patterns = ["test_*.jpg", "test_*.png", "*.debug.png"]
        
        for pattern in test_image_patterns:
            for file_path in Path(".").glob(pattern):
                self.move_to_archive(file_path, "assets", "Test asset file")
    
    def generate_cleanup_script(self):
        """Generate automated cleanup script"""
        print("\n🤖 PHASE 8: Generate Cleanup Automation")
        
        script_content = '''#!/usr/bin/env python3
"""
Automated Repository Cleanup - Generated Script
Run this to execute the planned cleanup actions.
"""

import shutil
from pathlib import Path

def execute_cleanup():
    """Execute the planned cleanup actions"""
    actions = ''' + json.dumps(self.cleanup_report["actions"], indent=2) + '''
    
    for action in actions:
        if action["type"] == "move":
            # Implementation would go here
            print(f"Would move: {action['file']}")
    
if __name__ == "__main__":
    execute_cleanup()
'''
        
        if not self.dry_run:
            with open("execute_cleanup.py", "w") as f:
                f.write(script_content)
        
        self.log_action("create", "execute_cleanup.py", "Automated cleanup script")
    
    def run_cleanup(self):
        """Execute the complete cleanup process"""
        print("🧹 STARTING COMPREHENSIVE REPOSITORY CLEANUP")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        print("=" * 60)
        
        self.create_archive_structure()
        self.cleanup_docker_configs()
        self.cleanup_scripts() 
        self.cleanup_test_files()
        self.cleanup_completion_docs()
        self.cleanup_backup_files()
        self.cleanup_requirements_files()
        self.cleanup_test_assets()
        self.generate_cleanup_script()
        
        # Generate statistics
        action_counts = {}
        for action in self.cleanup_report["actions"]:
            action_type = action["type"]
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        self.cleanup_report["statistics"] = action_counts
        
        print("\n📊 CLEANUP SUMMARY")
        print("=" * 40)
        for action_type, count in action_counts.items():
            print(f"{action_type.upper()}: {count} files")
        
        print(f"\nPreserved essential files: {len(self.cleanup_report['preserved_files'])}")
        
        # Save report
        report_file = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        if not self.dry_run:
            with open(report_file, "w") as f:
                json.dump(self.cleanup_report, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_file}")
        
        if self.dry_run:
            print("\n⚠️  This was a DRY RUN - no files were moved!")
            print("   Run with dry_run=False to execute cleanup")

def main():
    """Main cleanup execution"""
    import sys
    
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("🔍 Running cleanup analysis (DRY RUN)")
        print("   Add --execute flag to perform actual cleanup")
    else:
        print("⚠️  EXECUTING LIVE CLEANUP!")
        confirm = input("Are you sure? Type 'YES' to continue: ")
        if confirm != "YES":
            print("Cleanup cancelled")
            return
    
    cleanup = RepositoryCleanup(dry_run=dry_run)
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()
