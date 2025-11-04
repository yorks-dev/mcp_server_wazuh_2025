import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WazuhClient:
    def __init__(self, wazuh_url, username, password, timeout=60):
        self.wazuh_url = wazuh_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.timeout = timeout  # store timeout globally

    def authenticate(self):
        url = f"{self.wazuh_url}/security/user/authenticate"
        payload = {"username": self.username, "password": self.password}
        print(f"[*] Connecting to Wazuh API: {url}")
        try:
            response = requests.post(url, json=payload, verify=False, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            self.token = data.get("data", {}).get("token")
            print("[+] Authentication successful.")
        except requests.exceptions.RequestException as e:
            print(f"[!] Wazuh API connection failed: {e}")
            return

    def get_agents(self):
        if not self.token:
            self.authenticate()
        url = f"{self.wazuh_url}/agents"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=self.timeout)
            response.raise_for_status()
            agents = response.json().get("data", {}).get("affected_items", [])
            return agents
        except requests.exceptions.RequestException as e:
            print(f"[!] Failed to get agents: {e}")
            return []

    def get_alerts(self, limit=5):
        if not self.token:
            self.authenticate()
        url = f"{self.wazuh_url}/alerts?limit={limit}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=self.timeout)
            response.raise_for_status()
            alerts = response.json().get("data", {}).get("affected_items", [])
            return alerts
        except requests.exceptions.RequestException as e:
            print(f"[!] Failed to get alerts: {e}")
            return []


            
