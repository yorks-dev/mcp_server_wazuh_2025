#!/usr/bin/env python3
"""
Test script to verify that time-based queries without severity filters work correctly.
Tests: "get logs from last 15 minutes" should return ALL logs, not just critical ones.
"""
import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_query(query_text, pipeline="advanced"):
    """Execute a query and display results"""
    print(f"\n{'='*80}")
    print(f"Testing Query: {query_text}")
    print(f"Pipeline: {pipeline}")
    print(f"{'='*80}\n")
    
    if pipeline == "advanced":
        endpoint = f"{API_BASE_URL}/query/"
    elif pipeline == "simple":
        endpoint = f"{API_BASE_URL}/query/simple"
    else:
        endpoint = f"{API_BASE_URL}/mcp/wazuh.search"
    
    try:
        response = requests.post(
            endpoint,
            json={"query": query_text},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Display natural language response
            if "response" in result:
                print(f"\n📝 Natural Language Summary:")
                print(f"   {result['response']}")
            
            # Display parsed plan (if available)
            if "parsed_plan" in result:
                print(f"\n🔍 Parsed Plan:")
                print(f"   Time: {result['parsed_plan'].get('time')}")
                print(f"   Filters: {result['parsed_plan'].get('filters')}")
                print(f"   Limit: {result['parsed_plan'].get('limit')}")
            
            # Display DSL (if available)
            if "dsl" in result:
                print(f"\n⚙️  Generated DSL:")
                print(json.dumps(result['dsl'], indent=2))
            
            # Display result count
            if "raw_data" in result and "hits" in result["raw_data"]:
                hits = result["raw_data"]["hits"]
                total = hits.get("total", {})
                if isinstance(total, dict):
                    count = total.get("value", 0)
                else:
                    count = total
                
                print(f"\n📊 Results: {count} total hits")
                
                # Show sample of results
                if hits.get("hits"):
                    print(f"\n📋 Sample Results (first 3):")
                    for i, hit in enumerate(hits["hits"][:3], 1):
                        source = hit.get("_source", {})
                        rule = source.get("rule", {})
                        print(f"\n   {i}. {rule.get('description', 'N/A')}")
                        print(f"      Level: {rule.get('level', 'N/A')}")
                        print(f"      Agent: {source.get('agent', {}).get('name', 'N/A')}")
                        print(f"      Time: {source.get('@timestamp', 'N/A')}")
            
            print(f"\n✅ Query executed successfully!")
            return True
        else:
            print(f"\n❌ Query failed!")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  Wazuh MCP Server - Query Filter Test                       ║
║  Testing: ALL logs retrieval without severity filtering     ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Check server health
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            print(f"✅ Server is healthy")
            print(json.dumps(health.json(), indent=2))
        else:
            print(f"⚠️  Server health check returned: {health.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach server: {e}")
        return
    
    # Test cases
    test_cases = [
        {
            "name": "Time-based only (no severity)",
            "query": "get logs from last 15 minutes",
            "pipeline": "advanced",
            "expected": "Should return ALL logs from last 15min, no severity filter"
        },
        {
            "name": "Recent logs (no severity)",
            "query": "show me recent logs",
            "pipeline": "advanced",
            "expected": "Should return ALL logs from recent time, no severity filter"
        },
        {
            "name": "Logs from last hour",
            "query": "logs from last hour",
            "pipeline": "advanced",
            "expected": "Should return ALL logs from last hour, no severity filter"
        },
        {
            "name": "Critical logs (with severity)",
            "query": "show me critical alerts from last 24 hours",
            "pipeline": "advanced",
            "expected": "Should return ONLY critical (level >= 12) alerts"
        },
        {
            "name": "Simple query",
            "query": "show me recent alerts",
            "pipeline": "simple",
            "expected": "Should return alerts via Wazuh API"
        }
    ]
    
    results = []
    for test in test_cases:
        print(f"\n\n{'#'*80}")
        print(f"# Test Case: {test['name']}")
        print(f"# Expected: {test['expected']}")
        print(f"{'#'*80}")
        
        success = test_query(test['query'], test['pipeline'])
        results.append({
            "test": test['name'],
            "query": test['query'],
            "success": success
        })
        
        input("\nPress Enter to continue to next test...")
    
    # Summary
    print(f"\n\n{'='*80}")
    print(f"TEST SUMMARY")
    print(f"{'='*80}\n")
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} - {result['test']}")
        print(f"         Query: {result['query']}\n")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()
