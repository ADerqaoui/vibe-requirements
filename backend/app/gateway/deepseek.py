"""Deepseek cloud adapter."""
import httpx

from app.gateway._cloud_http import require_api_key, require_api_model_id
from app.gateway._openai_compatible import OpenAICompatibleGateway

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


class DeepseekGateway(OpenAICompatibleGateway):
    """Gateway adapter for Deepseek's OpenAI-compatible chat completions API."""

    def __init__(
        self,
        api_key: str,
        api_model_id: str | None,
        client: httpx.AsyncClient | None = None,
    ):
        super().__init__(
            provider="deepseek",
            base_url=DEEPSEEK_BASE_URL,
            api_key=require_api_key(api_key, "deepseek"),
            api_model_id=require_api_model_id(api_model_id, "deepseek"),
            client=client,
        )
