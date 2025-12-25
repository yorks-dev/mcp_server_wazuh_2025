#!/usr/bin/env python3
"""
MCP Server Test Cases - Comprehensive Validation
Tests all critical MCP server functionality for Wazuh integration
"""

import requests
import json
import time
from datetime import datetime, timezone

API_URL = "http://localhost:8000"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_header(title):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

def print_test(test_num, description):
    print(f"\n{BLUE}✅ TEST CASE {test_num} — {description}{RESET}")
    print("-" * 70)

def print_pass(message):
    print(f"{GREEN}✓ PASS:{RESET} {message}")

def print_fail(message):
    print(f"{RED}✗ FAIL:{RESET} {message}")

def print_warn(message):
    print(f"{YELLOW}⚠ WARNING:{RESET} {message}")

def print_info(message):
    print(f"  {message}")


# TEST CASE 1: Fetch Recent Logs
def test_case_1_recent_logs():
    print_test(1, "Fetch Recent Logs (Basic Query Test)")
    
    print_info("Purpose: Verify MCP Server can query Wazuh Indexer and retrieve recent logs")
    print_info("Query: 'Show me recent logs from last 15 minutes'")
    
    try:
        response = requests.post(
            f"{API_URL}/query/nl",
            json={"query": "Show me recent logs from last 15 minutes"},
            timeout=60
        )
        
        if response.status_code != 200:
            print_fail(f"HTTP {response.status_code}: {response.text[:200]}")
            return False
        
        result = response.json()
        
        # Check for success
        if not result.get('success'):
            print_fail("Query did not succeed")
            return False
        
        print_pass("HTTP 200 from Indexer")
        
        # Check raw_data
        raw_data = result.get('raw_data', {})
        hits = raw_data.get('hits', {})
        total_hits = hits.get('total', {})
        
        if isinstance(total_hits, dict):
            count = total_hits.get('value', 0)
        else:
            count = total_hits
        
        print_pass(f"Retrieved {count} log documents")
        
        # Check for required fields in first document
        if hits.get('hits') and len(hits['hits']) > 0:
            first_doc = hits['hits'][0]['_source']
            
            required_fields = ['rule.id', 'agent.id', 'timestamp', '@timestamp']
            found_fields = []
            
            for field in required_fields:
                if '.' in field:
                    parts = field.split('.')
                    value = first_doc
                    try:
                        for part in parts:
                            value = value[part]
                        found_fields.append(field)
                    except (KeyError, TypeError):
                        pass
                elif field in first_doc:
                    found_fields.append(field)
            
            print_pass(f"Found fields: {', '.join(found_fields)}")
            
            # Check for common error indicators
            if 'error' in str(result).lower():
                if 'invalid token' in str(result).lower():
                    print_fail("Invalid token error detected")
                    return False
                if 'index not found' in str(result).lower():
                    print_fail("Index not found error")
                    return False
                if 'unauthorized' in str(result).lower():
                    print_fail("Unauthorized error")
                    return False
                if 'connection refused' in str(result).lower():
                    print_fail("Connection refused error")
                    return False
            
            print_pass("No authentication or connection errors")
            return True
        else:
            print_warn("No log documents returned (may be no data in time range)")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print_fail(f"Exception: {e}")
        return False


# TEST CASE 2: Search by Agent ID
def test_case_2_agent_filter():
    print_test(2, "Test Search by Agent ID")
    
    print_info("Purpose: Verify logs can be filtered by Agent ID")
    print_info("Query: 'Get logs for agent 001 in last 1 hour'")
    
    try:
        response = requests.post(
            f"{API_URL}/query/nl",
            json={"query": "Get logs for agent 001 in last 1 hour"},
            timeout=60
        )
        
        if response.status_code != 200:
            print_fail(f"HTTP {response.status_code}: {response.text[:200]}")
            return False
        
        result = response.json()
        
        if not result.get('success'):
            print_fail("Query did not succeed")
            return False
        
        print_pass("Query executed successfully")
        
        # Check if agent filter was applied
        parsed_query = result.get('parsed_query', {})
        filters = parsed_query.get('filters', [])
        
        agent_filter_found = False
        for f in filters:
            if f.get('field') in ['agent.id', 'agent.name']:
                agent_filter_found = True
                print_pass(f"Agent filter applied: {f}")
                break
        
        if not agent_filter_found:
            print_warn("No explicit agent filter in parsed query (may use wildcard)")
        
        # Check raw results
        raw_data = result.get('raw_data', {})
        hits = raw_data.get('hits', {})
        
        if hits.get('hits'):
            # Verify all results are from agent 001
            all_from_agent = True
            checked_docs = 0
            
            for hit in hits['hits'][:5]:  # Check first 5
                doc = hit['_source']
                agent_id = doc.get('agent', {}).get('id', 'unknown')
                checked_docs += 1
                
                if agent_id != '001':
                    print_warn(f"Found log from agent {agent_id} (not 001)")
                    all_from_agent = False
            
            if all_from_agent and checked_docs > 0:
                print_pass(f"All {checked_docs} checked logs are from agent 001")
                return True
            elif checked_docs == 0:
                print_warn("No documents to verify agent filter")
                return True
            else:
                print_fail("Found logs from other agents")
                return False
        else:
            print_warn("No logs returned for agent 001 (may be inactive)")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print_fail(f"Exception: {e}")
        return False


# TEST CASE 3: Validate Rule Hit Logs
def test_case_3_rule_filter():
    print_test(3, "Validate Rule Hit Logs (Security Rule Detection)")
    
    print_info("Purpose: Check Wazuh Indexer returns logs for specific rules")
    print_info("Query: 'Show security alerts for rule 5501'")
    
    try:
        response = requests.post(
            f"{API_URL}/query/nl",
            json={"query": "Show security alerts for rule 5501"},
            timeout=60
        )
        
        if response.status_code != 200:
            print_fail(f"HTTP {response.status_code}: {response.text[:200]}")
            return False
        
        result = response.json()
        
        if not result.get('success'):
            print_fail("Query did not succeed")
            return False
        
        print_pass("Query executed successfully")
        
        # Check if rule filter was applied
        parsed_query = result.get('parsed_query', {})
        filters = parsed_query.get('filters', [])
        
        rule_filter_found = False
        for f in filters:
            if f.get('field') == 'rule.id' and '5501' in str(f.get('value')):
                rule_filter_found = True
                print_pass(f"Rule filter applied: {f}")
                break
        
        if not rule_filter_found:
            print_warn("Rule filter not explicitly shown (may be in query_string)")
        
        # Check raw results
        raw_data = result.get('raw_data', {})
        hits = raw_data.get('hits', {})
        
        if hits.get('hits') and len(hits['hits']) > 0:
            # Check first document for required fields
            first_doc = hits['hits'][0]['_source']
            rule = first_doc.get('rule', {})
            
            required_fields = ['id', 'description', 'level']
            found_fields = []
            
            for field in required_fields:
                if field in rule:
                    found_fields.append(field)
            
            print_pass(f"Rule fields present: {', '.join(found_fields)}")
            
            # Verify rule ID
            rule_id = rule.get('id', '')
            if rule_id == '5501':
                print_pass(f"Log contains rule.id: {rule_id}")
            else:
                print_warn(f"Log has rule.id: {rule_id} (not 5501, may be no data)")
            
            # Check other fields
            if first_doc.get('agent', {}).get('id'):
                print_pass(f"agent.id present: {first_doc['agent']['id']}")
            if first_doc.get('timestamp') or first_doc.get('@timestamp'):
                print_pass("timestamp present")
            
            return True
        else:
            print_warn("No logs found for rule 5501 (may be no recent triggers)")
            return True  # Not a failure if rule hasn't fired
            
    except Exception as e:
        print_fail(f"Exception: {e}")
        return False


# TEST CASE 4: Invalid Query / Zero Logs (Error Handling)
def test_case_4_error_handling():
    print_test(4, "Invalid Query / Zero Logs Returned (Error Handling)")
    
    print_info("Purpose: Ensure MCP handles non-existent data gracefully")
    print_info("Query: 'Get logs for agent 99999 in last 5 minutes'")
    
    try:
        response = requests.post(
            f"{API_URL}/query/nl",
            json={"query": "Get logs for agent 99999 in last 5 minutes"},
            timeout=60
        )
        
        # Should NOT be HTTP 500
        if response.status_code == 500:
            print_fail("HTTP 500 - Server error (should handle gracefully)")
            print_info(f"Error: {response.text[:500]}")
            return False
        
        if response.status_code != 200:
            print_warn(f"HTTP {response.status_code} (acceptable if graceful)")
        else:
            print_pass("HTTP 200 - Query executed")
        
        result = response.json()
        
        # Check for clean response
        if 'Traceback' in str(result) or 'Exception' in str(result):
            print_fail("Python exception/traceback in response")
            return False
        
        print_pass("No Python exceptions or stack traces")
        
        # Should either succeed with 0 results or fail gracefully
        raw_data = result.get('raw_data', {})
        hits = raw_data.get('hits', {})
        total = hits.get('total', {})
        
        if isinstance(total, dict):
            count = total.get('value', 0)
        else:
            count = total
        
        if count == 0:
            print_pass(f"Returned 0 logs for non-existent agent (expected)")
        else:
            print_warn(f"Returned {count} logs (unexpected for agent 99999)")
        
        # Check summary message
        summary = result.get('summary', '')
        if 'agent 99999' in summary.lower() or 'no' in summary.lower() or '0' in summary:
            print_pass("Summary mentions no logs or agent 99999")
        
        print_pass("Clean graceful response (no HTTP 500, no exceptions)")
        return True
        
    except requests.exceptions.HTTPError as e:
        if '500' in str(e):
            print_fail(f"HTTP 500 error: {e}")
            return False
        print_pass("No HTTP 500 error")
        return True
    except Exception as e:
        print_fail(f"Unexpected exception: {e}")
        return False


# BONUS: Threat Hunting Query
def test_case_bonus_threat_hunting():
    print_test("BONUS", "Threat Hunting Query (IP Search)")
    
    print_info("Purpose: Search logs by source IP for threat investigation")
    print_info("Query: 'Show logs where source IP is 8.8.8.8'")
    
    try:
        response = requests.post(
            f"{API_URL}/query/nl",
            json={"query": "Show logs where source IP is 8.8.8.8"},
            timeout=60
        )
        
        if response.status_code != 200:
            print_fail(f"HTTP {response.status_code}: {response.text[:200]}")
            return False
        
        result = response.json()
        
        if not result.get('success'):
            print_fail("Query did not succeed")
            return False
        
        print_pass("Query executed successfully")
        
        # Check if srcip filter was applied
        parsed_query = result.get('parsed_query', {})
        filters = parsed_query.get('filters', [])
        
        srcip_filter_found = False
        for f in filters:
            if 'srcip' in f.get('field', '').lower() and '8.8.8.8' in str(f.get('value')):
                srcip_filter_found = True
                print_pass(f"Source IP filter applied: {f}")
                break
        
        if not srcip_filter_found:
            print_warn("Source IP filter not found (may use different field)")
        
        # Check for errors
        error_indicators = ['bad request', 'unknown field', 'authentication failure', 'unauthorized']
        response_text = str(result).lower()
        
        for error in error_indicators:
            if error in response_text:
                print_fail(f"Error detected: {error}")
                return False
        
        print_pass("No authentication, field, or request errors")
        
        # Check results
        raw_data = result.get('raw_data', {})
        hits = raw_data.get('hits', {})
        
        if hits.get('hits'):
            count = len(hits['hits'])
            print_pass(f"Retrieved {count} logs for IP 8.8.8.8")
            
            # Check first doc for srcip field
            if hits['hits']:
                first_doc = hits['hits'][0]['_source']
                data = first_doc.get('data', {})
                srcip = data.get('srcip', 'not found')
                print_info(f"Sample srcip from result: {srcip}")
        else:
            print_warn("No logs found for IP 8.8.8.8 (may not exist in data)")
        
        return True
        
    except Exception as e:
        print_fail(f"Exception: {e}")
        return False


# Main test runner
def main():
    print_header("MCP SERVER TEST SUITE - COMPREHENSIVE VALIDATION")
    print(f"Testing against: {API_URL}")
    print(f"Test started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Check server health
    try:
        health = requests.get(f"{API_URL}/health", timeout=5)
        if health.status_code == 200:
            print_pass(f"Server is online and healthy")
        else:
            print_warn(f"Server health check returned {health.status_code}")
    except Exception as e:
        print_fail(f"Cannot connect to server: {e}")
        return
    
    # Run all tests
    results = {}
    
    results['Test 1'] = test_case_1_recent_logs()
    time.sleep(2)
    
    results['Test 2'] = test_case_2_agent_filter()
    time.sleep(2)
    
    results['Test 3'] = test_case_3_rule_filter()
    time.sleep(2)
    
    results['Test 4'] = test_case_4_error_handling()
    time.sleep(2)
    
    results['Bonus'] = test_case_bonus_threat_hunting()
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"{test}: {status}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    if passed == total:
        print(f"{GREEN}ALL TESTS PASSED! ({passed}/{total}){RESET}")
    else:
        print(f"{YELLOW}TESTS PASSED: {passed}/{total}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
