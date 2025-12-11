from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # OpenSearch / Wazuh Indexer Connection
    OPENSEARCH_HOST: str
    OPENSEARCH_USER: str
    OPENSEARCH_PASS: str
    
    # Allowed indices and fields (configurable but have defaults)
    INDEX_ALLOWLIST: List[str] = ["wazuh-alerts-*"]
    FIELD_ALLOWLIST: List[str] = [
        "rule.id",
        "rule.level",
        "agent.name",
        "data.srcip",
        "@timestamp",
        "manager.name",
        "vulnerability.severity",
    ]
    TIME_MAX_DAYS: int = 14
    MAX_LIMIT: int = 200
    DEFAULT_TZ: str = "UTC"

    # Wazuh API (Manager) - Required from environment
    WAZUH_API_HOST: str
    WAZUH_API_PORT: int
    WAZUH_API_USERNAME: str
    WAZUH_API_PASSWORD: str
    
    # Wazuh Indexer (Search) - Required from environment
    WAZUH_INDEXER_HOST: str
    WAZUH_INDEXER_PORT: int
    WAZUH_INDEXER_USERNAME: str
    WAZUH_INDEXER_PASSWORD: str
    
    # SSL verification (self-signed cert handling)
    WAZUH_VERIFY_SSL: bool = False

    # OpenAI API Key - Required from environment
    OPENAI_API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
