from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # OpenSearch / Wazuh Indexer Connection
    OPENSEARCH_HOST: str
    OPENSEARCH_USER: str
    OPENSEARCH_PASS: str
    
    # Allowed indices and fields (configurable but have defaults)
    INDEX_ALLOWLIST: List[str] = ["wazuh-alerts-*", "wazuh-archives-*"]
    FIELD_ALLOWLIST: List[str] = [
        # Rule fields
        "rule.id",
        "rule.level",
        "rule.description",
        "rule.mitre.technique",
        "rule.mitre.tactic",
        # Agent fields
        "agent.name",
        "agent.id",
        "agent.ip",
        "agent.os.platform",
        # Data fields
        "data.srcip",
        "data.dstip",
        "data.srcuser",
        "data.dstuser",
        "data.srcport",
        "data.dstport",
        "data.protocol",
        "data.win.eventdata.targetUserName",
        "data.win.system.eventID",
        "data.win.system.channel",
        # Decoder fields
        "decoder.name",
        "decoder.parent",
        # Other fields
        "@timestamp",
        "timestamp",
        "location",
        "full_log",
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
