"""
LiveLLM - Real Multi-Provider Streaming Client
Connects to actual live APIs (OpenAI, Anthropic, Google Gemini, Groq, DeepSeek, OpenRouter)
via HTTP SSE streaming and measures real-time physical telemetry.
"""

import json
import time
import httpx
from typing import AsyncGenerator, Dict, Any, Optional
from livellm.core.telemetry import TelemetryCollector, TelemetryResult


PROVIDER_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o"
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-3-5-sonnet-20241022"
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_model": "gemini-1.5-pro"
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile"
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat"
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openai/gpt-4o"
    }
}


def detect_provider(model_id: str, custom_base_url: Optional[str] = None) -> str:
    if custom_base_url:
        if "groq.com" in custom_base_url:
            return "groq"
        if "deepseek.com" in custom_base_url:
            return "deepseek"
        if "openrouter.ai" in custom_base_url:
            return "openrouter"
        if "anthropic.com" in custom_base_url:
            return "anthropic"
        if "googleapis.com" in custom_base_url:
            return "gemini"
        return "openai"

    if model_id.startswith(("gemini-", "models/gemini", "gemma-")):
        return "gemini"
    if model_id.startswith("groq/") or model_id in (
        "qwen/qwen3.8-27b", "qwen/qwen3.6-27b", "allam-2-7b", 
        "llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b"
    ):
        return "groq"
    if ":free" in model_id or "/" in model_id:
        return "openrouter"
    if model_id.startswith(("claude-", "anthropic/")):
        return "anthropic"
    if model_id.startswith("deepseek-"):
        return "deepseek"
    return "openai"


async def stream_openai_compatible(
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    collector: TelemetryCollector,
    temperature: float = 0.0
) -> AsyncGenerator[str, None]:
    """Streams from OpenAI, Groq, DeepSeek, OpenRouter, vLLM or Ollama."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Handling reasoning models that forbid temperature=0 (e.g. o1, o3, deepseek-reasoner)
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }
    if not any(x in model.lower() for x in ["o1", "o3", "deepseek-reasoner", "r1"]):
        payload["temperature"] = temperature
        payload["seed"] = 42

    url = f"{base_url.rstrip('/')}/chat/completions"
    
    async with client.stream("POST", url, headers=headers, json=payload, timeout=60.0) as resp:
        if resp.status_code != 200:
            err_body = await resp.aread()
            raise RuntimeError(f"API Error ({resp.status_code}): {err_body.decode(errors='replace')}")

        buffer = ""
        async for chunk_bytes in resp.aiter_bytes():
            buffer += chunk_bytes.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content") or delta.get("reasoning_content") or ""
                            if content:
                                collector.record_chunk(content, raw_chunk=data)
                                yield content
                    except json.JSONDecodeError:
                        continue


async def stream_anthropic(
    client: httpx.AsyncClient,
    api_key: str,
    model: str,
    prompt: str,
    collector: TelemetryCollector
) -> AsyncGenerator[str, None]:
    """Streams from Anthropic Messages API."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "temperature": 0.0
    }
    url = "https://api.anthropic.com/v1/messages"

    async with client.stream("POST", url, headers=headers, json=payload, timeout=60.0) as resp:
        if resp.status_code != 200:
            err_body = await resp.aread()
            raise RuntimeError(f"Anthropic API Error ({resp.status_code}): {err_body.decode(errors='replace')}")

        buffer = ""
        async for chunk_bytes in resp.aiter_bytes():
            buffer += chunk_bytes.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    try:
                        data = json.loads(data_str)
                        if data.get("type") == "content_block_delta":
                            text = data.get("delta", {}).get("text", "")
                            if text:
                                collector.record_chunk(text, raw_chunk=data)
                                yield text
                    except json.JSONDecodeError:
                        continue


async def stream_gemini(
    client: httpx.AsyncClient,
    api_key: str,
    model: str,
    prompt: str,
    collector: TelemetryCollector
) -> AsyncGenerator[str, None]:
    """Streams from Google Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0}
    }
    headers = {"Content-Type": "application/json"}

    async with client.stream("POST", url, headers=headers, json=payload, timeout=60.0) as resp:
        if resp.status_code != 200:
            err_body = await resp.aread()
            raise RuntimeError(f"Gemini API Error ({resp.status_code}): {err_body.decode(errors='replace')}")

        buffer = ""
        async for chunk_bytes in resp.aiter_bytes():
            buffer += chunk_bytes.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    try:
                        data = json.loads(data_str)
                        cands = data.get("candidates", [])
                        if cands:
                            parts = cands[0].get("content", {}).get("parts", [])
                            for p in parts:
                                text = p.get("text", "")
                                if text:
                                    collector.record_chunk(text, raw_chunk=data)
                                    yield text
                    except json.JSONDecodeError:
                        continue


async def stream_real_llm_inference(
    model_id: str,
    prompt: str,
    collector: TelemetryCollector,
    api_key: Optional[str] = None,
    custom_base_url: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Dispatcher for live streaming inference across any supported LLM provider.
    """
    provider = detect_provider(model_id, custom_base_url)

    async with httpx.AsyncClient() as client:
        if provider == "anthropic":
            async for chunk in stream_anthropic(client, api_key or "", model_id, prompt, collector):
                yield chunk
        elif provider == "gemini":
            async for chunk in stream_gemini(client, api_key or "", model_id, prompt, collector):
                yield chunk
        else:
            # OpenAI / Groq / DeepSeek / OpenRouter
            base_url = custom_base_url or PROVIDER_CONFIGS.get(provider, {}).get("base_url", "https://api.openai.com/v1")
            async for chunk in stream_openai_compatible(client, base_url, api_key or "", model_id, prompt, collector):
                yield chunk
