import httpx
import json

class WazuhClient:
    def __init__(self, wazuh_url, username, password, timeout=60):
        self.wazuh_url = wazuh_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.timeout = timeout
        self.client = httpx.AsyncClient(verify=False, timeout=timeout)

    async def authenticate(self):
        url = f"{self.wazuh_url}/security/user/authenticate"
        print(f"[*] Connecting to Wazuh API: {url}")
        try:
            response = await self.client.get(
                url, 
                auth=(self.username, self.password)
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get("data", {}).get("token")
            print(f"[+] Authentication successful. Token: {self.token[:20]}...")
        except httpx.HTTPError as e: 
            print(f"[!] Wazuh API connection failed: {e}")
            return

    async def get_agents(self):
        if not self.token:
            await self.authenticate()
        url = f"{self.wazuh_url}/agents"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            agents = response.json().get("data", {}).get("affected_items", [])
            return {"total": len(agents), "agents": agents}
        except httpx.HTTPError as e:
            print(f"[!] Failed to get agents: {e}")
            return {"total": 0, "agents": []}

    async def get_alerts(self, agent_id=None, severity=None, limit=5):
        if not self.token:
            await self.authenticate()
        
        params = {"limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        if severity:
            params["rule.level"] = severity
        
        url = f"{self.wazuh_url}/alerts"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            alerts = response.json().get("data", {}).get("affected_items", [])
            return {"total": len(alerts), "alerts": alerts}
        except httpx.HTTPError as e:
            print(f"[!] Failed to get alerts: {e}")
            return {"total": 0, "alerts": []}

    async def restart_manager(self):
        """Restart the Wazuh manager"""
        if not self.token:
            await self.authenticate()
        url = f"{self.wazuh_url}/manager/restart"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = await self.client.put(url, headers=headers)
            response.raise_for_status()
            print("[+] Manager restart initiated successfully")
            return True
        except httpx.HTTPError as e:
            print(f"[!] Failed to restart manager: {e}")
            return False

    async def check_api(self):
        """Check if Wazuh API is accessible"""
        if not self.token:
            await self.authenticate()
        url = f"{self.wazuh_url}/?pretty=true"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            print(f"[!] API check failed: {e}")
            return False

    async def check_indexer(self):
        """Check if Wazuh Indexer is accessible"""
        # Note: This checks the indexer via the Wazuh API
        # The actual indexer health is checked through OpenSearch client in es_client.py
        try:
            if not self.token:
                await self.authenticate()
            # Check if we can reach any indexer-related endpoint
            url = f"{self.wazuh_url}/manager/info"
            headers = {"Authorization": f"Bearer {self.token}"}
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"[!] Indexer check failed: {e}")
            return False
    
    async def close(self):
        """Close the httpx client"""
        await self.client.aclose()

