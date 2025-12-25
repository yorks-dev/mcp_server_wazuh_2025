#!/usr/bin/env python3
"""
Interactive test script for Wazuh NL Query System
Tests enhanced GPT context features including agent awareness, time context, rule mapping
"""

import requests
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any

API_URL = "http://localhost:8000"

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def test_query(query: str, expected_pipeline: str = None, verbose: bool = True, timeout: int = 60, retries: int = 2) -> Dict[str, Any]:
    """Test a single query and return results."""
    print(f"\n{BLUE}Testing:{RESET} {query}")
    
    for attempt in range(retries + 1):
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_URL}/query/nl",
                json={"query": query},
                timeout=timeout
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"{GREEN}✓ SUCCESS{RESET} ({elapsed:.2f}s)")
                print(f"  Pipeline: {data['routing']['pipeline']}")
                print(f"  Confidence: {data['routing'].get('confidence', 'N/A')}")
                print(f"  Reasoning: {data['routing'].get('reasoning', 'N/A')}")
                
                if verbose:
                    print(f"\n  Summary:")
                    print(f"  {data.get('summary', 'No summary')[:300]}...")
                    
                    if data.get('parsed_query'):
                        print(f"\n  Parsed Query:")
                        print(f"  {json.dumps(data['parsed_query'], indent=4)[:500]}...")
                
                # Check pipeline expectation
                if expected_pipeline and data['routing']['pipeline'] != expected_pipeline:
                    print(f"{YELLOW}⚠ Expected {expected_pipeline}, got {data['routing']['pipeline']}{RESET}")
                
                return data
                
            else:
                print(f"{RED}✗ FAILED{RESET} (HTTP {response.status_code})")
                print(f"  {response.text[:300]}")
                return None
                
        except requests.Timeout as e:
            if attempt < retries:
                print(f"{YELLOW}⚠ Timeout on attempt {attempt + 1}/{retries + 1}, retrying...{RESET}")
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
                continue
            else:
                print(f"{RED}✗ ERROR{RESET}: {str(e)}")
                return None
        except Exception as e:
            print(f"{RED}✗ ERROR{RESET}: {str(e)}")
            return None


def check_agent_context():
    """Verify agent context is being injected."""
    print(f"\n{BLUE}=== Checking Agent Context ==={RESET}")
    
    # First get agents
    response = requests.get(f"{API_URL}/agents")
    if response.status_code == 200:
        agents = response.json().get('agents', [])
        print(f"{GREEN}✓ Found {len(agents)} agents{RESET}")
        
        if agents:
            print("\nAvailable agents:")
            for agent in agents[:5]:
                print(f"  - {agent['id']}: {agent['name']} ({agent.get('os', {}).get('name', 'Unknown')})")
            
            # Test query with first agent
            if agents:
                first_agent = agents[0]
                query = f"Show me logs from agent {first_agent['name']}"
                print(f"\n{BLUE}Testing agent-specific query...{RESET}")
                result = test_query(query, verbose=False)
                
                if result and result.get('parsed_query'):
                    filters = result['parsed_query'].get('filters', [])
                    has_agent_filter = any(
                        f.get('field') in ['agent.name', 'agent.id'] 
                        for f in filters
                    )
                    if has_agent_filter:
                        print(f"{GREEN}✓ Agent filter correctly applied{RESET}")
                    else:
                        print(f"{YELLOW}⚠ No agent filter found in parsed query{RESET}")
    else:
        print(f"{RED}✗ Could not fetch agents{RESET}")


def check_time_awareness():
    """Verify time context is working."""
    print(f"\n{BLUE}=== Checking Time Awareness ==={RESET}")
    
    current_time = datetime.now(timezone.utc)
    print(f"Current UTC: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test various time queries
    time_queries = [
        ("Show me alerts from today", "now/d"),
        ("Get logs from last hour", "now-1h"),
        ("Recent critical events", "now-"),  # Should have recent time
    ]
    
    for query, expected_time in time_queries:
        result = test_query(query, verbose=False)
        if result and result.get('parsed_query'):
            time_config = result['parsed_query'].get('time', {})
            time_from = time_config.get('from', '')
            
            if expected_time in time_from:
                print(f"{GREEN}✓ Time parsed correctly: {time_from}{RESET}")
            else:
                print(f"{YELLOW}⚠ Time: {time_from} (expected {expected_time}){RESET}")


def check_rule_mapping():
    """Verify rule mappings are working."""
    print(f"\n{BLUE}=== Checking Rule Mappings ==={RESET}")
    
    rule_tests = [
        ("Show me SSH login failures", ["5710", "5551"]),
        ("Windows failed logins", ["4625", "60204"]),
        ("Brute force attempts", ["5720", "87801"]),
    ]
    
    for query, expected_rules in rule_tests:
        result = test_query(query, verbose=False)
        if result and result.get('parsed_query'):
            filters = result['parsed_query'].get('filters', [])
            
            # Check if any expected rule is in filters
            found_rules = []
            for f in filters:
                if f.get('field') == 'rule.id':
                    value = f.get('value')
                    if isinstance(value, list):
                        found_rules.extend(value)
                    else:
                        found_rules.append(value)
            
            if any(rule in str(found_rules) for rule in expected_rules):
                print(f"{GREEN}✓ Rule mapping correct: {found_rules}{RESET}")
            else:
                print(f"{YELLOW}⚠ Rules: {found_rules} (expected {expected_rules}){RESET}")


def check_field_validation():
    """Verify field name corrections are working."""
    print(f"\n{BLUE}=== Checking Field Validation ==={RESET}")
    
    # These queries use common wrong field names that should be corrected
    field_tests = [
        ("Show me high severity alerts", "rule.level"),  # Not "severity"
        ("Get logs from agent WIN-01", "agent.name"),    # Not "agent"
        ("Alerts from source IP 192.168.1.1", "data.srcip"),  # Not "source_ip"
    ]
    
    for query, expected_field in field_tests:
        result = test_query(query, verbose=False)
        if result and result.get('parsed_query'):
            filters = result['parsed_query'].get('filters', [])
            fields = [f.get('field') for f in filters]
            
            if expected_field in fields:
                print(f"{GREEN}✓ Field correct: {expected_field}{RESET}")
            else:
                print(f"{YELLOW}⚠ Fields: {fields} (expected {expected_field}){RESET}")


def manual_test_mode():
    """Interactive testing mode."""
    print(f"\n{BLUE}=== Manual Test Mode ==={RESET}")
    print("Enter queries to test (or 'quit' to exit)\n")
    
    while True:
        try:
            query = input(f"{BLUE}Query:{RESET} ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            test_query(query, verbose=True)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break


def main():
    """Run comprehensive test suite."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Wazuh NL Query System - Comprehensive Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Check server health
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"{GREEN}✓ Server is online{RESET}")
        else:
            print(f"{RED}✗ Server health check failed{RESET}")
            return
    except Exception as e:
        print(f"{RED}✗ Cannot connect to server: {e}{RESET}")
        print(f"Make sure server is running on {API_URL}")
        return
    
    # Run automated tests
    check_agent_context()
    check_time_awareness()
    check_rule_mapping()
    check_field_validation()
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{GREEN}Automated tests complete!{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Offer manual testing
    print("\nOptions:")
    print("  1. Run manual test mode (interactive)")
    print("  2. Exit")
    
    choice = input("\nChoice (1/2): ").strip()
    
    if choice == "1":
        manual_test_mode()
    
    print(f"\n{GREEN}Testing complete!{RESET}\n")


if __name__ == "__main__":
    main()
