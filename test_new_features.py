#!/usr/bin/env python3
"""
Quick test script for Price Alerts and Smart Lists API
Tests all major endpoints to verify functionality
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_price_alerts():
    """Test Price Alerts API"""
    print_section("TESTING PRICE ALERTS API")
    
    # 1. Create alert
    print("1. Creating price alert...")
    alert_data = {
        "product_id": 1,
        "target_price": 29.99,
        "operator": "<=",
        "channels": ["email"],
        "frequency": "daily",
        "priority": "normal",
        "notes": "Test alert from API test script"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/alerts",
        headers=HEADERS,
        json=alert_data
    )
    
    if response.status_code == 201:
        alert = response.json()
        alert_id = alert["id"]
        print(f"✅ Alert created: ID={alert_id}")
        print(f"   Status: {alert['status']}")
        print(f"   Target Price: ${alert['target_price']}")
    else:
        print(f"❌ Failed to create alert: {response.status_code}")
        print(f"   {response.text}")
        return
    
    # 2. List alerts
    print("\n2. Listing all alerts...")
    response = requests.get(f"{BASE_URL}/api/alerts")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} alerts")
        for alert in data['alerts'][:3]:
            print(f"   - Alert {alert['id']}: ${alert['target_price']} ({alert['status']})")
    else:
        print(f"❌ Failed to list alerts: {response.status_code}")
    
    # 3. Get alert detail
    print(f"\n3. Getting alert {alert_id} details...")
    response = requests.get(f"{BASE_URL}/api/alerts/{alert_id}")
    
    if response.status_code == 200:
        alert = response.json()
        print(f"✅ Alert details retrieved")
        print(f"   Frequency: {alert['frequency']}")
        print(f"   Channels: {', '.join(alert['channels'])}")
        print(f"   Fire Count: {alert['fire_count']}")
    else:
        print(f"❌ Failed to get alert: {response.status_code}")
    
    # 4. Trigger alert now
    print(f"\n4. Manually triggering alert {alert_id}...")
    response = requests.post(f"{BASE_URL}/api/alerts/{alert_id}/trigger-now")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Alert triggered: {result['status']}")
    else:
        print(f"❌ Failed to trigger alert: {response.status_code}")
    
    # 5. Get alert history
    print(f"\n5. Getting alert history...")
    response = requests.get(f"{BASE_URL}/api/alerts/{alert_id}/history")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total_events']} events")
        for event in data['events'][:3]:
            print(f"   - {event['event_type']} at {event['created_at']}")
    else:
        print(f"❌ Failed to get history: {response.status_code}")
    
    # 6. Pause alert
    print(f"\n6. Pausing alert {alert_id}...")
    response = requests.post(f"{BASE_URL}/api/alerts/{alert_id}/pause")
    
    if response.status_code == 200:
        alert = response.json()
        print(f"✅ Alert paused: Status={alert['status']}")
    else:
        print(f"❌ Failed to pause alert: {response.status_code}")
    
    # 7. Resume alert
    print(f"\n7. Resuming alert {alert_id}...")
    response = requests.post(f"{BASE_URL}/api/alerts/{alert_id}/resume")
    
    if response.status_code == 200:
        alert = response.json()
        print(f"✅ Alert resumed: Status={alert['status']}")
    else:
        print(f"❌ Failed to resume alert: {response.status_code}")
    
    # 8. Get user preferences
    print(f"\n8. Getting user preferences...")
    response = requests.get(f"{BASE_URL}/api/alerts/preferences")
    
    if response.status_code == 200:
        prefs = response.json()
        print(f"✅ Preferences retrieved")
        print(f"   Email enabled: {prefs['email_enabled']}")
        print(f"   Max per hour: {prefs['max_notifications_per_hour']}")
        print(f"   Timezone: {prefs['timezone']}")
    else:
        print(f"❌ Failed to get preferences: {response.status_code}")
    
    # 9. Update alert
    print(f"\n9. Updating alert {alert_id}...")
    update_data = {
        "target_price": 24.99,
        "priority": "urgent"
    }
    response = requests.put(
        f"{BASE_URL}/api/alerts/{alert_id}",
        headers=HEADERS,
        json=update_data
    )
    
    if response.status_code == 200:
        alert = response.json()
        print(f"✅ Alert updated")
        print(f"   New target: ${alert['target_price']}")
        print(f"   Priority: {alert['priority']}")
    else:
        print(f"❌ Failed to update alert: {response.status_code}")
    
    return alert_id


def test_smart_lists():
    """Test Smart Lists API"""
    print_section("TESTING SMART LISTS API")
    
    # 1. Create list
    print("1. Creating smart list...")
    list_data = {
        "name": "Test Shopping List",
        "description": "Created by API test script",
        "tags": ["groceries", "weekly"],
        "auto_monitor": True,
        "auto_monitor_threshold": 5.0,
        "visibility": "private"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/lists",
        headers=HEADERS,
        json=list_data
    )
    
    if response.status_code == 201:
        smart_list = response.json()
        list_id = smart_list["id"]
        print(f"✅ List created: ID={list_id}")
        print(f"   Name: {smart_list['name']}")
        print(f"   Auto-monitor: {smart_list['auto_monitor']}")
    else:
        print(f"❌ Failed to create list: {response.status_code}")
        print(f"   {response.text}")
        return
    
    # 2. Add items to list
    print(f"\n2. Adding items to list {list_id}...")
    items = [
        {"product_id": 1, "desired_price": 29.99, "quantity": 2, "priority": "high"},
        {"product_id": 2, "desired_price": 15.50, "quantity": 1, "priority": "normal"},
        {"product_id": 3, "desired_price": 8.99, "quantity": 3, "priority": "low"},
    ]
    
    item_ids = []
    for item_data in items:
        response = requests.post(
            f"{BASE_URL}/api/lists/{list_id}/items",
            headers=HEADERS,
            json=item_data
        )
        
        if response.status_code == 201:
            item = response.json()
            item_ids.append(item["id"])
            print(f"✅ Item added: Product {item['product_id']} (${item['desired_price']})")
        else:
            print(f"❌ Failed to add item: {response.status_code}")
    
    # 3. Get list detail
    print(f"\n3. Getting list {list_id} details...")
    response = requests.get(f"{BASE_URL}/api/lists/{list_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ List details retrieved")
        print(f"   Total items: {data['total_items']}")
        print(f"   Total value: ${data.get('total_value', 0):.2f}")
        print(f"   Items: {len(data['items'])}")
    else:
        print(f"❌ Failed to get list: {response.status_code}")
    
    # 4. Update item
    if item_ids:
        item_id = item_ids[0]
        print(f"\n4. Updating item {item_id}...")
        update_data = {
            "desired_price": 19.99,
            "priority": "urgent"
        }
        response = requests.put(
            f"{BASE_URL}/api/lists/{list_id}/items/{item_id}",
            headers=HEADERS,
            json=update_data
        )
        
        if response.status_code == 200:
            item = response.json()
            print(f"✅ Item updated")
            print(f"   New price: ${item['desired_price']}")
            print(f"   Priority: {item['priority']}")
        else:
            print(f"❌ Failed to update item: {response.status_code}")
    
    # 5. Start comparison
    print(f"\n5. Starting comparison for list {list_id}...")
    compare_data = {
        "force_rescrape": False
    }
    response = requests.post(
        f"{BASE_URL}/api/lists/{list_id}/compare",
        headers=HEADERS,
        json=compare_data
    )
    
    if response.status_code == 202:
        job = response.json()
        job_id = job["id"]
        print(f"✅ Comparison job started: ID={job_id}")
        print(f"   Status: {job['status']}")
        print(f"   Total items: {job['total_items']}")
    else:
        print(f"❌ Failed to start comparison: {response.status_code}")
        job_id = None
    
    # 6. Get comparison status
    if job_id:
        print(f"\n6. Getting comparison job {job_id} status...")
        response = requests.get(f"{BASE_URL}/api/lists/compare-jobs/{job_id}")
        
        if response.status_code == 200:
            job = response.json()
            print(f"✅ Job status: {job['status']}")
            print(f"   Progress: {job['completed_items']}/{job['total_items']}")
        else:
            print(f"❌ Failed to get job status: {response.status_code}")
    
    # 7. List all lists
    print(f"\n7. Listing all smart lists...")
    response = requests.get(f"{BASE_URL}/api/lists")
    
    if response.status_code == 200:
        lists = response.json()
        print(f"✅ Found {len(lists)} lists")
        for lst in lists[:3]:
            print(f"   - {lst['name']}: {lst['item_count']} items")
    else:
        print(f"❌ Failed to list lists: {response.status_code}")
    
    # 8. Get templates
    print(f"\n8. Getting list templates...")
    response = requests.get(f"{BASE_URL}/api/lists/templates")
    
    if response.status_code == 200:
        templates = response.json()
        print(f"✅ Found {len(templates)} templates")
        for template in templates[:3]:
            print(f"   - {template['name']} ({template['category']})")
    else:
        print(f"❌ Failed to get templates: {response.status_code}")
    
    return list_id


def test_analytics():
    """Test Analytics API"""
    print_section("TESTING ANALYTICS API")
    
    # 1. Get overview
    print("1. Getting analytics overview...")
    response = requests.get(f"{BASE_URL}/api/analytics/overview")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Overview retrieved")
        print(f"   Active alerts: {data['active_alerts']}")
        print(f"   Alerts fired today: {data['alerts_fired_today']}")
        print(f"   Smart lists: {data['smart_lists']}")
        print(f"   Comparisons today: {data['comparisons_today']}")
        print(f"   Forecasts available: {data['forecasts_available']}")
    else:
        print(f"❌ Failed to get overview: {response.status_code}")
    
    # 2. Get product trends
    print(f"\n2. Getting product price trends...")
    response = requests.get(f"{BASE_URL}/api/analytics/product/1/trends?days=30")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Trends retrieved")
        print(f"   Period: {data['period_days']} days")
        print(f"   Current price: ${data['current_price']:.2f}")
        print(f"   Average price: ${data['avg_price']:.2f}")
        print(f"   Trend: {data['trend']['direction']}")
    else:
        print(f"❌ Failed to get trends: {response.status_code}")
    
    # 3. Get forecast (if available)
    print(f"\n3. Getting product forecast...")
    response = requests.get(f"{BASE_URL}/api/analytics/product/1/forecast?horizon_days=30")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Forecast retrieved")
        print(f"   Model: {data['model_type']}")
        print(f"   Predictions: {len(data['predictions'])}")
        if data['best_buy_date']:
            print(f"   Best buy date: {data['best_buy_date']}")
            print(f"   Best buy price: ${data['best_buy_price']:.2f}")
    elif response.status_code == 404:
        print(f"ℹ️  No forecast available (expected for new products)")
    else:
        print(f"❌ Failed to get forecast: {response.status_code}")
    
    # 4. Get sentiment analysis (if available)
    print(f"\n4. Getting sentiment analysis...")
    response = requests.get(f"{BASE_URL}/api/analytics/sentiment/1")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sentiment retrieved")
        print(f"   Score: {data['overall_sentiment']['score']:.2f}")
        print(f"   Label: {data['overall_sentiment']['label']}")
        print(f"   Reviews: {data['total_reviews']}")
    elif response.status_code == 404:
        print(f"ℹ️  No sentiment analysis available (expected for new products)")
    else:
        print(f"❌ Failed to get sentiment: {response.status_code}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  PRICE ALERTS & SMART LISTS API TEST SUITE")
    print("  Base URL:", BASE_URL)
    print("="*60)
    
    try:
        # Test Price Alerts
        alert_id = test_price_alerts()
        
        # Test Smart Lists
        list_id = test_smart_lists()
        
        # Test Analytics
        test_analytics()
        
        print_section("TEST SUMMARY")
        print("✅ All API tests completed!")
        print(f"\n📊 Access API documentation:")
        print(f"   Swagger UI: {BASE_URL}/docs")
        print(f"   ReDoc: {BASE_URL}/redoc")
        
        if alert_id:
            print(f"\n🔔 Created Alert ID: {alert_id}")
        if list_id:
            print(f"📝 Created List ID: {list_id}")
        
        print("\n" + "="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API")
        print(f"   Make sure the server is running at {BASE_URL}")
        print(f"   Try: docker-compose up -d")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    main()
