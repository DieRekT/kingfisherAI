from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from pathlib import Path

# Find project root (where .env is located)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    ai_model_chat: str = Field("gpt-5-mini", alias="AI_MODEL_CHAT")
    ai_model_reasoning: str = Field("o3", alias="AI_MODEL_REASONING")
    ai_max_output_tokens: int = Field(1200, alias="AI_MAX_OUTPUT_TOKENS")
    ai_request_timeout_s: int = Field(40, alias="AI_REQUEST_TIMEOUT_S")
    ai_use_json_schema: bool = Field(True, alias="AI_USE_JSON_SCHEMA")
    
    unsplash_key: str = Field("", alias="UNSPLASH_ACCESS_KEY")
    pexels_key: str = Field("", alias="PEXELS_API_KEY")
    image_provider_order: str = Field("unsplash,pexels,generate", alias="IMAGE_PROVIDER_ORDER")
    
    search_provider: str = Field("responses_api", alias="SEARCH_PROVIDER")
    cache_ttl_s: int = Field(1800, alias="CACHE_TTL_S")
    
    app_timezone: str = Field("Australia/Sydney", alias="APP_TIMEZONE")
    app_origin: str = Field("http://localhost:3000", alias="APP_ORIGIN")
    app_name: str = Field("Kingfisher 2465", alias="APP_NAME")
    
    # CI flag for stub responses
    ci: bool = Field(False, alias="CI")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False
    )

settings = Settings()

