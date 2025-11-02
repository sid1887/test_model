"""
Final validation before Docker build
Tests all critical imports that were causing startup failures
"""

def test_import(module_path, item_name, description):
    """Test a specific import"""
    try:
        module = __import__(module_path, fromlist=[item_name])
        if hasattr(module, item_name):
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description} - {item_name} not found in {module_path}")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print("=" * 70)
    print("FINAL VALIDATION - Testing All Previously Failing Imports")
    print("=" * 70)
    
    tests = [
        # Issue #1: metrics object
        ("app.core.metrics", "metrics", "metrics object export"),
        ("app.core.metrics", "get_metrics_manager", "get_metrics_manager function"),
        
        # Issue #2: config field
        ("app.core.config", "settings", "settings object"),
        
        # Issue #3: events function
        ("app.core.events", "emit_search_executed", "emit_search_executed function"),
        
        # Issue #4: worker functions
        ("app.api.routes.alerts", "check_and_trigger_alerts", "check_and_trigger_alerts function"),
        ("app.api.routes.smart_lists", "compare_list_prices", "compare_list_prices function"),
        
        # Issue #5: database session
        ("app.core.database", "SessionLocal", "SessionLocal (sync session)"),
        ("app.core.database", "async_session_maker", "async_session_maker"),
        ("app.core.database", "Base", "Base model class"),
        
        # Issue #6: worker modules
        ("app.workers.alert_monitor", "monitor_alerts", "alert_monitor module"),
        ("app.workers.sentiment_worker", "analyze_sentiment", "sentiment_worker module"),
        ("app.workers.forecast_worker", "generate_forecast", "forecast_worker module"),
        ("app.workers.compare_worker", "compare_prices", "compare_worker module"),
        
        # Issue #7: product snapshot model
        ("app.models.product_snapshot", "ProductSnapshot", "ProductSnapshot model"),
        
        # Issue #8: alert model (corrected import path)
        ("app.models.alert", "PriceAlert", "PriceAlert model"),
        ("app.models.alert", "Notification", "Notification model"),
    ]
    
    passed = 0
    failed = 0
    
    for module_path, item_name, description in tests:
        if test_import(module_path, item_name, description):
            passed += 1
        else:
            failed += 1
    
    # Test config field specifically
    print("\n" + "=" * 70)
    print("SPECIFIC FIELD CHECKS")
    print("=" * 70)
    
    try:
        from app.core.config import settings
        if hasattr(settings, 'hf_api_key'):
            print("✅ settings.hf_api_key field exists")
            passed += 1
        else:
            print("❌ settings.hf_api_key field missing")
            failed += 1
    except Exception as e:
        print(f"❌ Could not check settings.hf_api_key - Error: {e}")
        failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL VALIDATIONS PASSED! Ready for Docker build! 🎉")
        return 0
    else:
        print(f"\n⚠️  {failed} validation(s) failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
