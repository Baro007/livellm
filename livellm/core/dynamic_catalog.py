"""
LiveLLM - Dynamic Model Catalog & Zero-Cost Open Registry
Dynamically pulls the latest 2026 frontier models (GPT-6 Astra, Gemini 3.8 Flash,
Claude Fable 5.1, DeepSeek V4.1) and all zero-cost free-tier models (:free) from open registries.
"""

import os
import json
import time
import httpx
from typing import List, Dict, Any, Optional

CATALOG_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "catalog_cache.json")

# Fallback models if offline
DEFAULT_FRONTIER_MODELS = [
    {
        "id": "openai/gpt-6-astra",
        "name": "OpenAI GPT-6 Astra (Frontier)",
        "provider": "OpenAI",
        "tier": "Astra Frontier",
        "is_free": False,
        "baseline_tps": 110.0,
        "baseline_ttft_ms": 290.0,
        "base_accuracy": 0.98
    },
    {
        "id": "~openai/gpt-astra-latest",
        "name": "OpenAI GPT-Astra Latest",
        "provider": "OpenAI",
        "tier": "Astra Flagship",
        "is_free": False,
        "baseline_tps": 125.0,
        "baseline_ttft_ms": 250.0,
        "base_accuracy": 0.97
    },
    {
        "id": "google/gemini-3.8-flash",
        "name": "Google Gemini 3.8 Flash",
        "provider": "Google",
        "tier": "Multimodal Flash",
        "is_free": False,
        "baseline_tps": 195.0,
        "baseline_ttft_ms": 190.0,
        "base_accuracy": 0.95
    },
    {
        "id": "anthropic/claude-fable-5.1",
        "name": "Anthropic Claude Fable 5.1",
        "provider": "Anthropic",
        "tier": "Next-Gen Reasoning",
        "is_free": False,
        "baseline_tps": 85.0,
        "baseline_ttft_ms": 350.0,
        "base_accuracy": 0.98
    },
    {
        "id": "deepseek/deepseek-v4.1-flash",
        "name": "DeepSeek V4.1 Flash",
        "provider": "DeepSeek",
        "tier": "Frontier MoE",
        "is_free": False,
        "baseline_tps": 90.0,
        "baseline_ttft_ms": 320.0,
        "base_accuracy": 0.94
    },
    {
        "id": "qwen/qwen3.8-max-0902",
        "name": "Qwen 3.8 Max",
        "provider": "Alibaba",
        "tier": "Flagship Dense",
        "is_free": False,
        "baseline_tps": 75.0,
        "baseline_ttft_ms": 390.0,
        "base_accuracy": 0.93
    },
    # ZERO COST FREE TIER OPEN MODELS
    {
        "id": "nex-agi/nex-n2.5-pro:free",
        "name": "Nex N2.5 Pro (Açık Havuz)",
        "provider": "OpenRouter Free",
        "tier": "Sıfır Maliyetli Açık Havuz",
        "is_free": True,
        "baseline_tps": 80.0,
        "baseline_ttft_ms": 350.0,
        "base_accuracy": 0.88
    },
    {
        "id": "inclusionai/ling-3.0-flash-vl:free",
        "name": "Ling 3.0 Flash VL (Açık Havuz)",
        "provider": "OpenRouter Free",
        "tier": "Sıfır Maliyetli Açık Havuz",
        "is_free": True,
        "baseline_tps": 120.0,
        "baseline_ttft_ms": 280.0,
        "base_accuracy": 0.87
    },
    {
        "id": "liquid/lfm-2.5-2.6b:free",
        "name": "Liquid LFM 2.5 2.6B (Açık Havuz)",
        "provider": "OpenRouter Free",
        "tier": "Sıfır Maliyetli Açık Havuz",
        "is_free": True,
        "baseline_tps": 160.0,
        "baseline_ttft_ms": 210.0,
        "base_accuracy": 0.84
    },
    {
        "id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B (Groq Ücretsiz)",
        "provider": "Groq Cloud (Free Tier)",
        "tier": "Sıfır Maliyetli (30 RPM)",
        "is_free": True,
        "baseline_tps": 290.0,
        "baseline_ttft_ms": 170.0,
        "base_accuracy": 0.91
    },
    {
        "id": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash (AI Studio Ücretsiz)",
        "provider": "Google AI Studio",
        "tier": "Sıfır Maliyetli (15 RPM)",
        "is_free": True,
        "baseline_tps": 175.0,
        "baseline_ttft_ms": 220.0,
        "base_accuracy": 0.93
    }
]


async def fetch_openrouter_catalog() -> List[Dict[str, Any]]:
    """
    Queries OpenRouter's live API to discover all current models,
    including new 2026 releases (GPT-6 Astra, Gemini 3.8, Claude Fable, DeepSeek V4)
    and zero-cost models with :free tag.
    """
    url = "https://openrouter.ai/api/v1/models"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers={"User-Agent": "LiveLLM/1.0"})
            if resp.status_code != 200:
                return load_cached_catalog()

            data = resp.json().get("data", [])
            parsed_models = []

            for m in data:
                m_id = m.get("id", "")
                m_name = m.get("name", m_id)
                pricing = m.get("pricing", {})
                is_free = ":free" in m_id or (pricing.get("prompt") == "0" and pricing.get("completion") == "0")

                # Detect provider
                provider = m_id.split("/")[0].title() if "/" in m_id else "AI"

                # Detect tier
                tier = "Sıfır Maliyetli Açık Havuz" if is_free else "Frontier"
                if "astra" in m_id.lower():
                    tier = "Astra Frontier"
                elif "flash" in m_id.lower():
                    tier = "Flash Speed"
                elif "reason" in m_id.lower() or "r1" in m_id.lower():
                    tier = "CoT Reasoning"

                parsed_models.append({
                    "id": m_id,
                    "name": m_name,
                    "provider": provider,
                    "tier": tier,
                    "is_free": is_free,
                    "context_length": m.get("context_length", 32768),
                    "baseline_tps": 140.0 if is_free else 95.0,
                    "baseline_ttft_ms": 260.0,
                    "base_accuracy": 0.88 if is_free else 0.96
                })

            # Save to cache
            save_cached_catalog(parsed_models)
            return parsed_models

    except Exception as e:
        print(f"[Catalog] Error fetching live catalog: {e}, falling back to cache.")
        return load_cached_catalog()


def save_cached_catalog(models: List[Dict[str, Any]]):
    try:
        os.makedirs(os.path.dirname(CATALOG_CACHE_FILE), exist_ok=True)
        with open(CATALOG_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(models, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Catalog] Failed to write cache: {e}")


def load_cached_catalog() -> List[Dict[str, Any]]:
    if os.path.exists(CATALOG_CACHE_FILE):
        try:
            with open(CATALOG_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_FRONTIER_MODELS
