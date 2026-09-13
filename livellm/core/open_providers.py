"""
LiveLLM - Zero-Cost Open API Providers ("Amme Hizmeti" Engine)
Integrates zero-cost public gateways and free-tier APIs to run continuous benchmarking
with $0.00 infrastructure and token cost.
"""

from typing import Dict, Any, List

OPEN_FREE_GATEWAYS = {
    "pollinations": {
        "name": "Pollinations.ai Açık Ağ Geçidi (Anahtarsız Sıfır Maliyet)",
        "base_url": "https://text.pollinations.ai/openai",
        "requires_key": False,
        "default_models": ["openai", "qwen-coder", "mistral", "llama"],
        "description": "Herhangi bir API anahtarı veya kredi kartı gerektirmeden 100% açık kamu hizmeti çıkarımı."
    },
    "openrouter_free": {
        "name": "OpenRouter Açık Ücretsiz Havuz (:free)",
        "base_url": "https://openrouter.ai/api/v1",
        "requires_key": True,  # Key can be a free account key with 0 credits
        "filter_tag": ":free",
        "description": "OpenRouter üzerindeki 19+ adet sıfır kredili açık model havuzu."
    },
    "github_models": {
        "name": "GitHub Models (Azure AI)",
        "base_url": "https://models.inference.ai.azure.com",
        "requires_key": True,  # Uses free GITHUB_TOKEN (Personal Access Token)
        "default_models": ["gpt-4o", "gpt-4o-mini", "Phi-4", "Mistral-large-2411"],
        "description": "Tüm GitHub kullanıcılarına ücretsiz sunulan günlük 50-150 sorguluk model erişimi."
    },
    "google_ai_studio": {
        "name": "Google AI Studio Ücretsiz Katmanı",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "requires_key": True,
        "rate_limit": "15 RPM / 1500 RPD",
        "default_models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        "description": "Kredi kartsız dakikada 15 istek, günde 1.500 istek ücretsiz."
    },
    "groq_free": {
        "name": "Groq LPU Ücretsiz Çıkarım",
        "base_url": "https://api.groq.com/openai/v1",
        "requires_key": True,
        "rate_limit": "30 RPM / 14,400 RPD",
        "default_models": ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b"],
        "description": "Ultra yüksek TPS (300+ TPS) ile günde 14.400 istek ücretsiz."
    }
}


def get_zero_cost_providers_summary() -> List[Dict[str, Any]]:
    summary = []
    for k, v in OPEN_FREE_GATEWAYS.items():
        summary.append({
            "key": k,
            "name": v["name"],
            "base_url": v["base_url"],
            "requires_key": v["requires_key"],
            "description": v["description"]
        })
    return summary
