import httpx
from app.core.config import settings


class LLMClient:
    def __init__(self) -> None:
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.timeout = settings.LLM_TIMEOUT_SECONDS

    async def completion(
        self, prompt: str, n_predict: int = 600, temperature: float = 0.2
    ) -> str:
        # llama.cpp server: POST /completion
        url = f"{self.base_url}/completion"
        payload = {
            "prompt": prompt,
            "n_predict": n_predict,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            # llama.cpp server returns {"content": "..."} typically
            return data.get("content", "")
