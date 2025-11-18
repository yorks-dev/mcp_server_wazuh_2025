from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    OPENSEARCH_HOST: str = "http://localhost:9200"
    OPENSEARCH_USER: str  = "admin"
    OPENSEARCH_PASS: str  = "admin"
    INDEX_ALLOWLIST: List[str] = ["wazuh-alerts-*"]
    FIELD_ALLOWLIST: List[str] = [
        "rule.id", "rule.level", "agent.name",
        "data.srcip", "@timestamp", "manager.name", "vulnerability.severity"
    ]
    TIME_MAX_DAYS: int = 14
    MAX_LIMIT: int = 200
    DEFAULT_TZ: str = "UTC"

        # Wazuh API (Manager)
    WAZUH_API_HOST: str = "https://10.21.236.157"
    WAZUH_API_PORT: int = 55000
    WAZUH_API_USERNAME: str = "admin"
    WAZUH_API_PASSWORD: str = "NxFdeGIYQMtZ8077IQ?qJRABNpPsPYoa"
    # Wazuh Indexer (Search)
    WAZUH_INDEXER_HOST: str = "https://10.21.236.157"
    WAZUH_INDEXER_PORT: int = 9200
    WAZUH_INDEXER_USERNAME: str = "admin"   # default indexer user
    WAZUH_INDEXER_PASSWORD: str = "admin"   # unless changed manually
    # SSL (self-signed cert)
    WAZUH_VERIFY_SSL: bool = False


    OPENAI_API_KEY: str = "sk-proj-"


    class Config:
        env_file = ".env"

settings = Settings()












