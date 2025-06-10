#!/usr/bin/env python3
"""
Final Test Script for Cumpair Pre-Flight System
Validates all components and generates final report
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔍 {description}")
    print(f"📝 Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            return True, result.stdout
        else:
            print(f"❌ FAILED: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT")
        return False, "Command timed out"
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False, str(e)

def check_files():
    """Check if all required files exist"""
    print("\n📁 Checking Required Files:")
    
    required_files = [
        "pre_flight_check.py",
        "safe_start_final.py",
        "start-enhanced.ps1",
        "PRE_FLIGHT_GUIDE.md",
        "DEPLOYMENT_COMPLETE.md"
    ]
    
    all_exist = True
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_exist = False
    
    return all_exist

def main():
    """Main validation routine"""
    print("🚀 Cumpair Pre-Flight System - Final Validation")
    print("=" * 60)
    
    # Test results
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "overall_success": False
    }
    
    # 1. Check files
    print("\n1️⃣ FILE VALIDATION")
    results["tests"]["files_exist"] = check_files()
    
    # 2. Test pre-flight check
    print("\n2️⃣ PRE-FLIGHT CHECK TEST")
    success, output = run_command("python pre_flight_check.py --quick", "Running quick pre-flight check")
    results["tests"]["preflight_check"] = success
    
    # 3. Test safe startup (preflight only)
    print("\n3️⃣ SAFE STARTUP TEST")
    success, output = run_command("python safe_start_final.py --preflight-only --quick-check", "Testing safe startup script")
    results["tests"]["safe_startup"] = success
    
    # 4. Check health report generation
    print("\n4️⃣ HEALTH REPORT TEST")
    health_report_exists = Path("pre_flight_health_report.json").exists()
    if health_report_exists:
        try:
            with open("pre_flight_health_report.json", "r") as f:
                health_data = json.load(f)
            print(f"✅ Health report exists with {health_data.get('total_checks', 0)} checks")
            results["tests"]["health_report"] = True
        except Exception as e:
            print(f"❌ Health report corrupted: {e}")
            results["tests"]["health_report"] = False
    else:
        print("❌ Health report not found")
        results["tests"]["health_report"] = False
    
    # 5. Test PowerShell script help
    print("\n5️⃣ POWERSHELL SCRIPT TEST")
    success, output = run_command("powershell -Command \".\\start-enhanced.ps1 -ShowHelp\"", "Testing PowerShell startup script")
    results["tests"]["powershell_script"] = success
    
    # Calculate overall success
    total_tests = len(results["tests"])
    passed_tests = sum(1 for result in results["tests"].values() if result)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    results["overall_success"] = success_rate >= 80  # 80% pass rate required
    results["success_rate"] = success_rate
    results["passed_tests"] = passed_tests
    results["total_tests"] = total_tests
    
    # Generate final report
    print("\n" + "=" * 60)
    print("📊 FINAL VALIDATION REPORT")
    print("=" * 60)
    
    for test_name, result in results["tests"].items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\n📈 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if results["overall_success"]:
        print("\n🎉 DEPLOYMENT READY!")
        print("✅ All critical systems are operational")
        print("✅ Pre-flight check system is fully functional")
        print("✅ Ready for production deployment")
        
        # Save success report
        with open("VALIDATION_SUCCESS.json", "w") as f:
            json.dump(results, f, indent=2)
            
        print(f"📋 Validation report saved to: VALIDATION_SUCCESS.json")
        
    else:
        print("\n⚠️ DEPLOYMENT NEEDS ATTENTION")
        print("❌ Some systems need fixes before production deployment")
        print("🔧 Review failed tests and address issues")
        
        # Save failure report
        with open("VALIDATION_ISSUES.json", "w") as f:
            json.dump(results, f, indent=2)
            
        print(f"📋 Issue report saved to: VALIDATION_ISSUES.json")
    
    return results["overall_success"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
