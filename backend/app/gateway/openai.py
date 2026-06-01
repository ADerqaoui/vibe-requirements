"""OpenAI cloud adapter."""
import httpx

from app.gateway._cloud_http import require_api_key, require_api_model_id
from app.gateway._openai_compatible import OpenAICompatibleGateway

OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAIGateway(OpenAICompatibleGateway):
    """Gateway adapter for OpenAI chat completions."""

    def __init__(
        self,
        api_key: str,
        api_model_id: str | None,
        client: httpx.AsyncClient | None = None,
    ):
        super().__init__(
            provider="openai",
            base_url=OPENAI_BASE_URL,
            api_key=require_api_key(api_key, "openai"),
            api_model_id=require_api_model_id(api_model_id, "openai"),
            client=client,
        )
