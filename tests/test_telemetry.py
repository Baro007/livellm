"""
LiveLLM - Tests for Telemetry, Cache Busting and Tokenization
"""

import time
import pytest
from livellm.core.cache_buster import generate_nonce, inject_cache_buster
from livellm.core.telemetry import TelemetryCollector, count_universal_tokens


def test_cache_buster_nonce():
    nonce = generate_nonce()
    assert len(nonce) > 10

    prompt = "Solve 2 + 2."
    wrapped = inject_cache_buster(prompt, nonce)
    assert f"[Nonce: {nonce}]" in wrapped
    assert prompt in wrapped


def test_universal_token_counting():
    text = "Large language model performance degradation and temporal fluctuations continuous benchmarking."
    tokens = count_universal_tokens(text)
    assert tokens > 5
    assert isinstance(tokens, int)


def test_telemetry_collector_metrics():
    collector = TelemetryCollector(model_id="test-model")
    collector.start()

    # Simulate arrival of first token after 50ms
    time.sleep(0.05)
    collector.record_chunk("Hello")

    # Simulate subsequent tokens
    time.sleep(0.02)
    collector.record_chunk(" world")
    time.sleep(0.02)
    collector.record_chunk(" from LiveLLM")

    res = collector.finish(prompt_text="Say greeting")

    assert res.ttft_ms >= 45.0
    assert res.chunk_count == 3
    assert res.full_text == "Hello world from LiveLLM"
    assert res.universal_tokens >= 3
    assert res.tps > 0.0
