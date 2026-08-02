"""Unified LLM interface for MementoBloom.

Supports multiple providers through a single API.
Configuration via environment variables.

Providers:
- deepseek (OpenAI-compatible)
- openai
- google / gemini
- ollama (local)
- auto (fallback chain)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence


def _load_env() -> None:
    """Load .env from workspace root if present."""
    from core.paths import workspace_root

    env_path = workspace_root() / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env()


class LLMProvider:
    name: str = "base"

    def chat(
        self,
        messages: Sequence[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class DeepSeekProvider(LLMProvider):
    name = "deepseek"

    def __init__(self) -> None:
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    def chat(
        self,
        messages: Sequence[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "openai package is required for DeepSeek provider. "
                "Install with: pip install openai"
            ) from exc

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=model or self.model,
            messages=list(messages),
            **kwargs,
        )
        return {
            "provider": self.name,
            "model": response.model,
            "content": response.choices[0].message.content,
            "raw": response,
        }


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def chat(
        self,
        messages: Sequence[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "openai package is required for OpenAI provider."
            ) from exc

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=model or self.model,
            messages=list(messages),
            **kwargs,
        )
        return {
            "provider": self.name,
            "model": response.model,
            "content": response.choices[0].message.content,
            "raw": response,
        }


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self) -> None:
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3")

    def chat(
        self,
        messages: Sequence[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        import urllib.request
        import urllib.error

        url = f"{self.host}/api/chat"
        payload = json.dumps(
            {
                "model": model or self.model,
                "messages": list(messages),
                "stream": False,
                **kwargs,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        return {
            "provider": self.name,
            "model": raw.get("model"),
            "content": raw.get("message", {}).get("content", ""),
            "raw": raw,
        }


class GoogleProvider(LLMProvider):
    name = "google"

    def __init__(self) -> None:
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    def chat(
        self,
        messages: Sequence[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "requests package is required for Google provider. "
                "Install with: pip install requests"
            ) from exc

        model_name = (model or self.model).split("/")[-1]
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model_name}:generateContent?key={self.api_key}"
        )

        system_instruction = None
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            if not isinstance(text, str):
                text = str(text)
            if role == "system":
                system_instruction = {"parts": [{"text": text}]}
            else:
                contents.append({"parts": [{"text": text}]})

        payload: Dict[str, Any] = {"contents": contents, **kwargs}
        if system_instruction:
            payload["system_instruction"] = system_instruction

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            safe_url = url.split("?key=")[0] + "?key=***"
            raise RuntimeError(
                f"Google Gemini request failed: {exc.response.status_code} {safe_url}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Google Gemini request failed: {exc}") from exc
        body = response.json()
        candidates = body.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                text = parts[0].get("text", "")

        return {
            "provider": self.name,
            "model": body.get("modelVersion") or model_name,
            "content": text,
            "raw": body,
        }


class AutoProvider(LLMProvider):
    name = "auto"

    def __init__(self) -> None:
        self.fallback_order = [
            name.strip()
            for name in os.environ.get(
                "LLM_FALLBACK_ORDER",
                "google,deepseek,openai,ollama",
            )
            .split(",")
            if name.strip()
        ]

    def _try_provider(self, name: str, messages, model, kwargs):
        provider_cls = _PROVIDERS.get(name)
        if not provider_cls:
            return None
        try:
            return provider_cls().chat(messages, model=model, **kwargs)
        except Exception as exc:
            return {"error": exc, "provider": name}

    def chat(
        self,
        messages: Sequence[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        last_error = None
        for name in self.fallback_order:
            result = self._try_provider(name, messages, model, kwargs)
            if result is None:
                continue
            if "error" not in result:
                result.setdefault("provider", name)
                result.setdefault("fallback_order", self.fallback_order)
                return result
            last_error = result["error"]

        raise RuntimeError(
            f"AutoProvider fallback failed. Tried: {', '.join(self.fallback_order)}. "
            f"Last error: {last_error}"
        ) from last_error


# Registry of providers
_PROVIDERS = {
    "deepseek": DeepSeekProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
    "google": GoogleProvider,
    "gemini": GoogleProvider,
    "auto": AutoProvider,
}


def get_provider(name: Optional[str] = None) -> LLMProvider:
    provider_name = (name or os.environ.get("LLM_PROVIDER", "auto")).lower()
    provider_cls = _PROVIDERS.get(provider_name)
    if not provider_cls:
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            f"Available: {', '.join(sorted(_PROVIDERS))}"
        )
    return provider_cls()


def chat(
    messages: Sequence[Dict[str, Any]],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Send a chat completion request to the configured LLM provider.

    Environment variables:
        LLM_PROVIDER: provider name (default: auto)
        LLM_FALLBACK_ORDER: comma-separated provider list for auto (default: google,deepseek,openai,ollama)
        DEEPSEEK_API_KEY: API key for DeepSeek
        DEEPSEEK_BASE_URL: base URL (default: https://api.deepseek.com)
        DEEPSEEK_MODEL: model name (default: deepseek-chat)
        OPENAI_API_KEY: API key for OpenAI
        OPENAI_BASE_URL: base URL
        OPENAI_MODEL: model name
        GEMINI_API_KEY: API key for Google Gemini
        GEMINI_MODEL: model name (default: gemini-1.5-flash)
        OLLAMA_HOST: Ollama server URL (default: http://localhost:11434)
        OLLAMA_MODEL: model name (default: llama3)
    """
    client = get_provider(provider)
    return client.chat(messages, model=model, **kwargs)


def ask(text: str, system: Optional[str] = None, **kwargs: Any) -> str:
    """Convenience wrapper for single-turn chat."""
    messages: List[Dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": text})
    result = chat(messages, **kwargs)
    return result.get("content", "")
