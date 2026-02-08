import json
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
            return data.get("content", "")

    async def completion_stream(
        self, prompt: str, n_predict: int = 600, temperature: float = 0.2
    ):
        """Async generator: yields content chunks (str) as they arrive from llama.cpp SSE."""
        url = f"{self.base_url}/completion"
        payload = {
            "prompt": prompt,
            "n_predict": n_predict,
            "temperature": temperature,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload) as r:
                r.raise_for_status()
                buffer = ""
                async for chunk in r.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, _, buffer = buffer.partition("\n")
                        line = line.strip()
                        if not line:
                            continue
                        # SSE: "data: {...}" oder NDJSON: "{...}"
                        data_str = line[5:].strip() if line.startswith("data:") else line
                        if data_str == "[DONE]":
                            return
                        try:
                            data = json.loads(data_str)
                            content = data.get("content") if isinstance(data, dict) else None
                            if content:
                                yield content
                            if isinstance(data, dict) and data.get("stop") is True:
                                return
                        except json.JSONDecodeError:
                            continue
