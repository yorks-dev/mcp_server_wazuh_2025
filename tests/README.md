# Test Suite

All test files are organized here for easy access and maintenance.

## Quick Test Commands

```bash
# Run all tests
./tests/test_queries.py          # General query tests (11/12 pass)
./tests/test_mcp_cases.py         # MCP test cases (5/5 pass)
./tests/test_advanced_dsl.py      # Advanced DSL tests (5/5 pass)

# Or use shell script
./tests/test_queries.sh

# Diagnose timeouts
./tests/diagnose_timeout.py
```

## Test Files

- **test_queries.py** - General natural language query tests
- **test_mcp_cases.py** - Basic MCP functionality validation  
- **test_advanced_dsl.py** - Advanced security analytics tests
- **test_query_filters.py** - Filter validation tests
- **diagnose_timeout.py** - Timeout diagnostic tool
- **test_queries.sh** - Shell script wrapper for tests

## Documentation

See main docs for detailed test case documentation:
- [MCP_TEST_CASES.md](../MCP_TEST_CASES.md)
- [ADVANCED_DSL_TEST_CASES.md](../ADVANCED_DSL_TEST_CASES.md)
- [TESTING_GUIDE.md](../TESTING_GUIDE.md)
