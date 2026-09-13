"""
LiveLLM - Telemetry & Streaming Engine
Measures TTFT, ITL (TPOT), and TPS with nanosecond precision.
Applies universal tokenization (o200k_base) to normalize throughput across heterogeneous vendors.
"""

import time
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
from dataclasses import dataclass, field

_TIKTOKEN_AVAILABLE = False
_ENCODER = None

try:
    import tiktoken
    try:
        _ENCODER = tiktoken.get_encoding("o200k_base")
        _TIKTOKEN_AVAILABLE = True
    except Exception:
        try:
            _ENCODER = tiktoken.get_encoding("cl100k_base")
            _TIKTOKEN_AVAILABLE = True
        except Exception:
            _ENCODER = None
            _TIKTOKEN_AVAILABLE = False
except Exception:
    _TIKTOKEN_AVAILABLE = False
    _ENCODER = None


@dataclass
class ChunkEvent:
    timestamp_ns: int
    delta_text: str
    raw_chunk: Optional[Dict[str, Any]] = None


@dataclass
class TelemetryResult:
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    universal_tokens: int  # Standardized token count (o200k_base)
    ttft_ms: float         # Time To First Token in ms
    tpot_ms: float         # Time Per Output Token (Inter-Token Latency) in ms
    tps: float             # Standardized Tokens Per Second during decode
    total_duration_ms: float
    decode_duration_ms: float
    full_text: str
    chunk_count: int
    p95_itl_ms: float = 0.0
    p99_itl_ms: float = 0.0
    jitter_ms: float = 0.0
    error: Optional[str] = None


def count_universal_tokens(text: str) -> int:
    """Calculates standardized token count using o200k_base (OpenAI universal standard)."""
    if not text:
        return 0
    if _TIKTOKEN_AVAILABLE and _ENCODER is not None:
        try:
            return len(_ENCODER.encode(text))
        except Exception:
            pass
    # Fallback heuristic: 1 token ~ 3.8 characters for English/multilingual mix
    return max(1, int(len(text) / 3.8))


class TelemetryCollector:
    """
    Collects SSE chunks with high-precision monotonic timestamps,
    then computes TTFT, TPOT/ITL, TPS, and jitter.
    """

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.t_request_ns: int = 0
        self.events: List[ChunkEvent] = []
        self.error: Optional[str] = None

    def start(self):
        """Mark request departure time."""
        self.t_request_ns = time.perf_counter_ns()
        self.events = []
        self.error = None

    def record_chunk(self, delta_text: str, raw_chunk: Optional[Dict[str, Any]] = None):
        """Record chunk arrival with exact timestamp."""
        now_ns = time.perf_counter_ns()
        self.events.append(ChunkEvent(timestamp_ns=now_ns, delta_text=delta_text, raw_chunk=raw_chunk))

    def record_error(self, err_msg: str):
        self.error = err_msg

    def finish(self, prompt_text: str = "") -> TelemetryResult:
        """Compute statistical and physical metrics."""
        t_finish_ns = time.perf_counter_ns()
        total_duration_ms = (t_finish_ns - self.t_request_ns) / 1_000_000.0

        if not self.events:
            return TelemetryResult(
                model_id=self.model_id,
                prompt_tokens=count_universal_tokens(prompt_text),
                completion_tokens=0,
                universal_tokens=0,
                ttft_ms=total_duration_ms,
                tpot_ms=0.0,
                tps=0.0,
                total_duration_ms=total_duration_ms,
                decode_duration_ms=0.0,
                full_text="",
                chunk_count=0,
                error=self.error or "No chunks received"
            )

        t_first_chunk_ns = self.events[0].timestamp_ns
        t_last_chunk_ns = self.events[-1].timestamp_ns

        # TTFT: From request sent until first chunk arrives
        ttft_ms = (t_first_chunk_ns - self.t_request_ns) / 1_000_000.0
        decode_duration_ms = max(1.0, (t_last_chunk_ns - t_first_chunk_ns) / 1_000_000.0)

        full_text = "".join(e.delta_text for e in self.events)
        universal_tokens = count_universal_tokens(full_text)
        prompt_tokens = count_universal_tokens(prompt_text)

        # Inter-token latencies (ITL) between chunks
        itls_ms: List[float] = []
        for i in range(1, len(self.events)):
            diff_ms = (self.events[i].timestamp_ns - self.events[i - 1].timestamp_ns) / 1_000_000.0
            itls_ms.append(diff_ms)

        # TPOT (Time Per Output Token): decode_duration / (N - 1)
        if universal_tokens > 1:
            tpot_ms = decode_duration_ms / (universal_tokens - 1)
        elif len(self.events) > 1:
            tpot_ms = decode_duration_ms / (len(self.events) - 1)
        else:
            tpot_ms = decode_duration_ms

        # TPS: universal tokens / decode seconds
        decode_sec = decode_duration_ms / 1000.0
        tps = (universal_tokens / decode_sec) if decode_sec > 0 else 0.0

        # Percentiles of chunk intervals (jitter & tail latency)
        if itls_ms:
            sorted_itls = sorted(itls_ms)
            p95_idx = min(len(sorted_itls) - 1, int(len(sorted_itls) * 0.95))
            p99_idx = min(len(sorted_itls) - 1, int(len(sorted_itls) * 0.99))
            p95_itl_ms = sorted_itls[p95_idx]
            p99_itl_ms = sorted_itls[p99_idx]
            avg_itl = sum(itls_ms) / len(itls_ms)
            variance = sum((x - avg_itl) ** 2 for x in itls_ms) / len(itls_ms)
            jitter_ms = variance ** 0.5
        else:
            p95_itl_ms = tpot_ms
            p99_itl_ms = tpot_ms
            jitter_ms = 0.0

        return TelemetryResult(
            model_id=self.model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=len(self.events),
            universal_tokens=universal_tokens,
            ttft_ms=round(ttft_ms, 2),
            tpot_ms=round(tpot_ms, 2),
            tps=round(tps, 2),
            total_duration_ms=round(total_duration_ms, 2),
            decode_duration_ms=round(decode_duration_ms, 2),
            full_text=full_text,
            chunk_count=len(self.events),
            p95_itl_ms=round(p95_itl_ms, 2),
            p99_itl_ms=round(p99_itl_ms, 2),
            jitter_ms=round(jitter_ms, 2),
            error=self.error
        )


async def simulate_streaming_inference(
    model_id: str,
    prompt: str,
    simulated_ttft_ms: float = 240.0,
    simulated_tps: float = 65.0,
    total_tokens: int = 40
) -> AsyncGenerator[str, None]:
    """
    Simulates a realistic provider SSE stream for offline verification and testing.
    Emulates prefill delay (TTFT) followed by steady token streaming.
    """
    await asyncio.sleep(simulated_ttft_ms / 1000.0)

    # Word fragments
    words = [
        "Thinking", " step", " by", " step.", " First,", " we", " parse", " the",
        " problem", " conditions.", " The", " solution", " is", " verified", " through",
        " formal", " deduction.", "\n\n", "Therefore,", " the", " final", " answer", " is",
        " \\boxed{42}."
    ]

    token_delay = 1.0 / max(1.0, simulated_tps)
    for word in words:
        await asyncio.sleep(token_delay)
        yield word
