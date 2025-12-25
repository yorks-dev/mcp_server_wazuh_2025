#!/usr/bin/env python3
"""
Diagnostic script to identify where timeouts occur in the query pipeline.
"""

import requests
import time
import json

API_URL = "http://localhost:8000"

def test_with_timing(query: str):
    """Test a query and show timing breakdown."""
    print(f"\n{'='*60}")
    print(f"Testing: {query}")
    print(f"{'='*60}")
    
    overall_start = time.time()
    
    try:
        response = requests.post(
            f"{API_URL}/query/nl",
            json={"query": query},
            timeout=120,
            stream=False
        )
        
        overall_time = time.time() - overall_start
        
        print(f"\n✓ Query completed in {overall_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nPipeline: {data['routing']['pipeline']}")
            print(f"Confidence: {data['routing']['confidence']}")
            
            if 'parsed_query' in data and data['parsed_query']:
                pq = data['parsed_query']
                print(f"\nParsed Query:")
                print(f"  Filters: {len(pq.get('filters', []))}")
                print(f"  Time: {pq.get('time', {}).get('from', 'N/A')} to {pq.get('time', {}).get('to', 'N/A')}")
                print(f"  Limit: {pq.get('limit', 'N/A')}")
            
            if 'raw_data' in data and isinstance(data['raw_data'], dict):
                if 'hits' in data['raw_data']:
                    total = data['raw_data']['hits'].get('total', 0)
                    if isinstance(total, dict):
                        total = total.get('value', 0)
                    print(f"\nResults: {total} hits")
        else:
            print(f"\n✗ HTTP {response.status_code}")
            print(response.text[:500])
            
    except requests.Timeout:
        overall_time = time.time() - overall_start
        print(f"\n✗ TIMEOUT after {overall_time:.2f}s")
        print("\nPossible causes:")
        print("  1. GPT API slow/hanging")
        print("  2. Wazuh Indexer query timeout")
        print("  3. Large result set processing")
        print("  4. Network issues")
        
    except Exception as e:
        overall_time = time.time() - overall_start
        print(f"\n✗ ERROR after {overall_time:.2f}s: {e}")


if __name__ == "__main__":
    # Test queries that might timeout
    queries = [
        "Get logs from last hour",
        "Show me alerts from today",
        "Recent critical events",
        "Show me all alerts from last 24 hours",
    ]
    
    print("Timeout Diagnostic Tool")
    print("="*60)
    
    for query in queries:
        test_with_timing(query)
        time.sleep(2)  # Brief pause between queries
    
    print(f"\n{'='*60}")
    print("Diagnosis complete!")
    print("\nCheck server logs for detailed timing:")
    print("  grep 'took.*s' /var/log/your-app.log")
    print("\nOr check uvicorn output for timing info")
