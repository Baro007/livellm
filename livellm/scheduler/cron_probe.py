"""
LiveLLM - Automated Continuous Prober (Cron / GitHub Actions)
Runs periodic Tier 1 and Tier 2 probes at $0.00 cost using GitHub Actions and free endpoints.
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime, timezone

from livellm.storage.database import init_db, save_probe_run, DB_PATH
from livellm.benchmarks.datasets import TIER_1_PULSE_TASKS, TIER_2_REASONING_TASKS
from livellm.core.cache_buster import generate_nonce, inject_cache_buster
from livellm.core.telemetry import TelemetryCollector
from livellm.core.provider_client import stream_real_llm_inference
from livellm.core.dynamic_catalog import load_cached_catalog
from livellm.evaluators.math_eval import verify_math_answer
from livellm.evaluators.code_eval import execute_sandboxed_code, extract_python_code
from livellm.evaluators.format_eval import extract_and_validate_json


async def run_cron_cycle(free_only: bool = True):
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting LiveLLM Continuous Probe Cycle...")
    init_db(DB_PATH)

    catalog = load_cached_catalog()
    target_models = [m for m in catalog if m.get("is_free", False)] if free_only else catalog

    print(f"Targeting {len(target_models)} models for this cycle.")

    # Rotate through Tier 1 and Tier 2 tasks
    all_tasks = TIER_1_PULSE_TASKS + TIER_2_REASONING_TASKS

    for m in target_models[:4]:  # Probe up to 4 models per cron tick to stay within free limits
        model_id = m["id"]
        task = all_tasks[hash(model_id) % len(all_tasks)]
        nonce = generate_nonce()
        prompt = inject_cache_buster(task["prompt"], nonce)

        collector = TelemetryCollector(model_id=model_id)
        collector.start()

        print(f"Probing {model_id} on task {task['id']}...")

        # Detect any available key (Pollinations, Groq, OpenRouter, etc.)
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")
        base_url = None

        try:
            async for chunk in stream_real_llm_inference(
                model_id=model_id,
                prompt=prompt,
                collector=collector,
                api_key=api_key,
                custom_base_url=base_url
            ):
                pass
        except Exception as e:
            collector.record_error(str(e))
            print(f"Warning: Probe for {model_id} returned: {e}")

        telemetry = collector.finish(prompt_text=prompt)

        # Verification
        is_corr = False
        score = 0.0
        if task.get("task_type") == "math":
            is_corr, _, _ = verify_math_answer(telemetry.full_text, task.get("ground_truth", ""))
            score = 1.0 if is_corr else 0.0
        elif task.get("task_type") == "code":
            code_block = extract_python_code(telemetry.full_text)
            if code_block:
                is_corr, _, _ = execute_sandboxed_code(code_block, task.get("assertions", ""))
                score = 1.0 if is_corr else 0.0

        run_id = save_probe_run(
            model_id=model_id,
            tier=1 if "pulse" in task["id"] else 2,
            task_id=task["id"],
            ttft_ms=telemetry.ttft_ms,
            tpot_ms=telemetry.tpot_ms,
            tps=telemetry.tps,
            universal_tokens=telemetry.universal_tokens,
            is_correct=is_corr,
            score=score,
            output_snippet=telemetry.full_text[:300],
            error=telemetry.error
        )
        print(f"Saved Run #{run_id} for {model_id} | TTFT: {telemetry.ttft_ms}ms | TPS: {telemetry.tps} | Pass: {is_corr}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LiveLLM Automated Cron Prober")
    parser.add_argument("--all-models", action="store_true", help="Probe all models, not just free ones")
    args = parser.parse_args()

    asyncio.run(run_cron_cycle(free_only=not args.all_models))
