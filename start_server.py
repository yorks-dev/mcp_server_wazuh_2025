"""
Start Wazuh MCP Server
Run this script to start the server in the background
"""
import subprocess
import sys
import os

# Change to the repo directory
repo_dir = r"c:\Users\kaust\OneDrive\Desktop\wazuh\mcp_server_wazuh_2025-main"
os.chdir(repo_dir)

print("="*70)
print("Starting Wazuh MCP Server...")
print("="*70)

# Start the server
subprocess.Popen(
    [sys.executable, "-m", "app.main"],
    cwd=repo_dir,
    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
)

print("\n✓ Server started in new window")
print("✓ API will be available at: http://localhost:8000")
print("\nEndpoints:")
print("  GET /          - Server status")
print("  GET /test      - Test Wazuh connection")
print("  GET /agents    - Get all agents")
print("  POST /query_llm/ - Query LLM")
print("\nTo test:")
print('  Invoke-WebRequest -Uri "http://localhost:8000/test" | Select-Object -ExpandProperty Content')
print("\n" + "="*70)
