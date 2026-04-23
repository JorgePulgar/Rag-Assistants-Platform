from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_llm_deployment: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    # Azure AI Search
    azure_search_endpoint: str
    azure_search_api_key: str

    # Database
    database_url: str = "sqlite:///./app.db"

    # RAG parameters
    chunk_size: int = 800
    chunk_overlap: int = 150
    retrieval_top_k: int = 5
    retrieval_score_threshold: float = 1.5
    history_max_messages: int = 10
    query_rewriting_enabled: bool = True
    query_rewriting_history_n: int = 4

    # Logging
    log_level: str = "INFO"


settings = Settings()
