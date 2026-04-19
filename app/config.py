"""应用配置"""
import os
from pydantic import BaseModel


class Settings(BaseModel):
    """全局配置"""
    # 大模型 API 配置
    llm_api_url: str = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    # 服务配置
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8100"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()
