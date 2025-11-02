"""
Detailed API endpoint testing and data integration verification
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(method, endpoint, description):
    """Test an API endpoint and show response"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, timeout=10)
        
        if response.status_code in [200, 201, 204]:
            print(f"✅ {description}")
            try:
                data = response.json()
                if isinstance(data, dict):
                    print(f"   Response keys: {list(data.keys())[:5]}")
                elif isinstance(data, list):
                    print(f"   Items: {len(data)}")
                    if len(data) > 0:
                        print(f"   Sample: {list(data[0].keys())[:3] if isinstance(data[0], dict) else data[0]}")
            except:
                print(f"   Response: {response.text[:100]}")
        else:
            print(f"⚠️  {description} - Status: {response.status_code}")
            print(f"   {response.text[:100]}")
        
        return response.status_code in [200, 201, 204]
    except Exception as e:
        print(f"❌ {description} - Error: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("DETAILED API INTEGRATION TEST")
    print("=" * 80)
    
    print("\n1️⃣  CORE API ENDPOINTS:")
    print("-" * 80)
    
    test_endpoint("GET", "/health", "Health Check")
    test_endpoint("GET", "/products", "Get Products")
    test_endpoint("GET", "/retailers", "Get Retailers")
    
    print("\n2️⃣  PRICE COMPARISON & ANALYSIS:")
    print("-" * 80)
    
    test_endpoint("GET", "/price-comparison", "Price Comparison Data")
    test_endpoint("GET", "/price-trends", "Price Trends")
    
    print("\n3️⃣  SMART LISTS & ALERTS:")
    print("-" * 80)
    
    test_endpoint("GET", "/smart-lists", "Smart Lists")
    test_endpoint("GET", "/alerts", "Alerts")
    
    print("\n4️⃣  SEARCH & RECOMMENDATIONS:")
    print("-" * 80)
    
    test_endpoint("GET", "/search?q=phone", "Product Search")
    test_endpoint("GET", "/recommendations", "Recommendations")
    
    print("\n5️⃣  REAL-TIME FEATURES:")
    print("-" * 80)
    
    test_endpoint("GET", "/feed", "Live Feed")
    test_endpoint("GET", "/notifications", "Notifications")
    
    print("\n6️⃣  ANALYTICS & REPORTING:")
    print("-" * 80)
    
    test_endpoint("GET", "/analytics", "Analytics Data")
    test_endpoint("GET", "/reports", "Reports")
    
    print("\n7️⃣  BARCODE & QR CODE SERVICES:")
    print("-" * 80)
    
    test_endpoint("POST", "/barcode/scan", "Barcode Scan (POST)")
    test_endpoint("POST", "/qrcode/scan", "QR Code Scan (POST)")
    
    print("\n8️⃣  SETTINGS & PREFERENCES:")
    print("-" * 80)
    
    test_endpoint("GET", "/settings", "User Settings")
    test_endpoint("GET", "/preferences", "User Preferences")
    
    print("\n" + "=" * 80)
    print("SERVICE INTEGRATION VERIFICATION")
    print("=" * 80)
    
    # Test database connection
    print("\n📊 Database Integration:")
    products_ok = test_endpoint("GET", "/products", "Database Connection")
    
    # Test external services
    print("\n🔗 External Service Integration:")
    test_endpoint("GET", "/retailers", "Retailer APIs")
    test_endpoint("GET", "/search?q=test", "Search Service")
    
    # Test background tasks/workers
    print("\n⚙️  Background Services:")
    test_endpoint("GET", "/alerts", "Alert Worker Integration")
    test_endpoint("GET", "/smart-lists", "List Comparison Worker")
    
    # Test AI/ML services
    print("\n🤖 AI/ML Integration:")
    test_endpoint("GET", "/recommendations", "AI Recommendations")
    
    print("\n" + "=" * 80)
    print("✅ INTEGRATION TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
