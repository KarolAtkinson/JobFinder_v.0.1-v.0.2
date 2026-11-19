"""Local-only access to the Ollama HTTP API."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MODEL_ID = "hf.co/Qwen/Qwen3-4B-GGUF:Q4_K_M"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
# Ollama's default 40k context needs ~9 GB for this model; a CV section prompt fits easily in 8k.
CONTEXT_TOKENS = 8192
OUTPUT_LANGUAGES = {"en-GB": "British English (UK spelling)", "pl": "Polish"}
_NUMBER = re.compile(r"(?<!\w)\d+(?:[.,]\d+)*(?:\s*%|[kKmMbB])?(?!\w)")


class LocalModelError(RuntimeError):
    """Raised when the local model runtime or its response is unavailable."""


class ChatClient(Protocol):
    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Return a model-generated response string."""


class OllamaClient:
    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL, model: str = MODEL_ID) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        # Optional callback receiving the number of generated chunks (enables streaming).
        self.on_progress: Callable[[int], None] | None = None

    def _request(
        self,
        endpoint: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout: float = 30,
    ) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"} if data is not None else {},
            method="POST" if data is not None else "GET",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace").strip()
            raise LocalModelError(f"Local model request failed (HTTP {error.code}): {detail}") from error
        except (URLError, TimeoutError) as error:
            raise LocalModelError(
                "Ollama is not responding at "
                f"{self.base_url}. Install/start Ollama and download the configured model."
            ) from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise LocalModelError("Ollama returned an invalid JSON response.") from error
        if not isinstance(result, dict):
            raise LocalModelError("Ollama returned an unexpected response shape.")
        if result.get("error"):
            raise LocalModelError(f"Ollama reported an error: {result['error']}")
        return result

    def is_model_installed(self) -> bool:
        result = self._request("/api/tags")
        models = result.get("models", [])
        if not isinstance(models, list):
            raise LocalModelError("Ollama returned an invalid model list.")
        return any(
            isinstance(item, dict) and item.get("name") == self.model
            for item in models
        )

    def pull_model(self, on_progress: Callable[[str, int | None], None] | None = None) -> None:
        payload = {"model": self.model, "stream": True}
        request = Request(
            f"{self.base_url}/api/pull",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=60) as response:
                for raw_line in response:
                    if not raw_line.strip():
                        continue
                    try:
                        update = json.loads(raw_line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as error:
                        raise LocalModelError("Ollama returned invalid model-download progress.") from error
                    if not isinstance(update, dict):
                        raise LocalModelError("Ollama returned invalid model-download progress.")
                    if update.get("error"):
                        raise LocalModelError(f"Model download failed: {update['error']}")
                    if on_progress is not None:
                        total = update.get("total")
                        completed = update.get("completed")
                        percent = (
                            round(completed / total * 100)
                            if isinstance(total, int) and total > 0 and isinstance(completed, int)
                            else None
                        )
                        on_progress(str(update.get("status", "Downloading model")), percent)
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace").strip()
            raise LocalModelError(f"Model download failed (HTTP {error.code}): {detail}") from error
        except (URLError, TimeoutError) as error:
            raise LocalModelError(
                "Could not reach Ollama. Install/start Ollama before downloading the model."
            ) from error

    def chat(self, system_prompt: str, user_prompt: str, schema: dict[str, Any] | None = None) -> str:
        if self.on_progress is not None:
            return self._chat_streaming(system_prompt, user_prompt, schema)
        result = self._request(
            "/api/chat",
            {
                "model": self.model,
                "stream": False,
                "format": schema,
                "options": {"temperature": 0.1, "num_ctx": CONTEXT_TOKENS},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=600,
        )
        message = result.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise LocalModelError("Ollama returned no generated message.")
        return message["content"]

    def _chat_streaming(self, system_prompt: str, user_prompt: str, schema: dict[str, Any] | None = None) -> str:
        """Stream the reply so the caller can show progress (one chunk is roughly one token)."""
        payload = {
            "model": self.model,
            "stream": True,
            "format": schema,
            "options": {"temperature": 0.1, "num_ctx": CONTEXT_TOKENS},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        parts: list[str] = []
        try:
            with urlopen(request, timeout=600) as response:
                for raw_line in response:
                    if not raw_line.strip():
                        continue
                    try:
                        update = json.loads(raw_line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as error:
                        raise LocalModelError("Ollama returned an invalid streamed response.") from error
                    if not isinstance(update, dict):
                        raise LocalModelError("Ollama returned an unexpected response shape.")
                    if update.get("error"):
                        raise LocalModelError(f"Ollama reported an error: {update['error']}")
                    message = update.get("message")
                    if isinstance(message, dict) and isinstance(message.get("content"), str):
                        parts.append(message["content"])
                        if self.on_progress is not None:
                            self.on_progress(len(parts))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace").strip()
            raise LocalModelError(f"Local model request failed (HTTP {error.code}): {detail}") from error
        except (URLError, TimeoutError) as error:
            raise LocalModelError(
                f"Ollama is not responding at {self.base_url}. Install/start Ollama and download the configured model."
            ) from error
        if not parts:
            raise LocalModelError("Ollama returned no generated message.")
        return "".join(parts)


_POLISH_CHARS = re.compile(r"[ąćęłńśźżĄĆĘŁŃŚŹŻ]")
_POLISH_WORDS = {"oraz", "dla", "się", "przez", "jest", "który", "która", "które", "przy", "na", "do"}
_ENGLISH_WORDS = {"the", "and", "with", "for", "of", "to", "using", "across", "that", "which"}


_QUOTED = re.compile(r"[„“\"«][^„“”\"»]{3,}[”“\"»]|Hack The Box(?: Academy)?|Browser Guard")


def _language_problem(text: str, language: str) -> bool:
    # Quoted titles and product names are proper nouns and may legitimately be in another language.
    words = re.findall(r"[^\W\d_]+", _QUOTED.sub(" ", text).casefold())
    if language == "pl":
        return sum(word in _ENGLISH_WORDS for word in words) >= 3
    polish_markers = sum(bool(_POLISH_CHARS.search(word)) or word in _POLISH_WORDS - {"na", "do"} for word in words)
    return polish_markers >= 3

