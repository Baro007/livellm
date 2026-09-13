"""
LiveLLM - Current Production Models & Real Benchmark Tasks
Reflects the latest frontier models (GPT-4o, Claude 3.5 Sonnet, Gemini 2.0, DeepSeek R1/V3, Llama 3.3).
"""

from typing import List, Dict, Any

SUPPORTED_MODELS: List[Dict[str, Any]] = [
    {
        "id": "gemini-3.8-flash",
        "name": "Gemini 3.8 Flash (2026)",
        "provider": "Google AI Studio",
        "tier": "Frontier Speed & Multimodal",
        "baseline_tps": 185.0,
        "baseline_ttft_ms": 210.0,
        "base_accuracy": 0.95,
    },
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "Google AI Studio",
        "tier": "Sub-Second Latency",
        "baseline_tps": 160.0,
        "baseline_ttft_ms": 240.0,
        "base_accuracy": 0.93,
    },
    {
        "id": "qwen/qwen3.8-27b",
        "name": "Qwen 3.8 27B (Groq LPU)",
        "provider": "Groq",
        "tier": "Ultra-Low Latency Inference",
        "baseline_tps": 320.0,
        "baseline_ttft_ms": 160.0,
        "base_accuracy": 0.92,
    },
    {
        "id": "groq/compound-mini",
        "name": "Groq Compound-Mini",
        "provider": "Groq",
        "tier": "Agentic Reasoning & Search",
        "baseline_tps": 290.0,
        "baseline_ttft_ms": 190.0,
        "base_accuracy": 0.91,
    },
    {
        "id": "openai/gpt-6-astra",
        "name": "GPT-6 Astra (2026 Frontier)",
        "provider": "OpenRouter / OpenAI",
        "tier": "Universal Frontier Reasoning",
        "baseline_tps": 82.0,
        "baseline_ttft_ms": 420.0,
        "base_accuracy": 0.98,
    },
    {
        "id": "anthropic/claude-fable-5.1",
        "name": "Claude Fable 5.1 (2026)",
        "provider": "OpenRouter / Anthropic",
        "tier": "Autonomous Systems & Code",
        "baseline_tps": 75.0,
        "baseline_ttft_ms": 450.0,
        "base_accuracy": 0.97,
    },
    {
        "id": "nvidia/nemotron-3.5-lightning:free",
        "name": "Nvidia Nemotron 3.5 Lightning (:free)",
        "provider": "OpenRouter (Zero-Cost)",
        "tier": "Zero-Cost Community",
        "baseline_tps": 45.0,
        "baseline_ttft_ms": 850.0,
        "base_accuracy": 0.88,
    },
    {
        "id": "gpt-4o",
        "name": "GPT-4o (OpenAI Standard)",
        "provider": "OpenAI / OpenRouter",
        "tier": "Multimodal Standard",
        "baseline_tps": 94.0,
        "baseline_ttft_ms": 310.0,
        "base_accuracy": 0.94,
    },
    {
        "id": "deepseek-chat",
        "name": "DeepSeek V3 / V4",
        "provider": "DeepSeek / OpenRouter",
        "tier": "Open Frontier MoE",
        "baseline_tps": 68.0,
        "baseline_ttft_ms": 520.0,
        "base_accuracy": 0.93,
    },
]

TIER_1_PULSE_TASKS: List[Dict[str, Any]] = [
    {
        "id": "pulse_json_arithmetic_01",
        "task_type": "format_and_math",
        "prompt": (
            "You are an automated API endpoint. Compute the exact integer value of 1847 * 29 + 4829 - 731. "
            "Respond ONLY with a valid raw JSON object. Do not include markdown formatting or backticks.\n"
            'Schema: {"calculation": int, "status": "ok"}'
        ),
        "expected_calculation": 1847 * 29 + 4829 - 731,  # 57661
        "required_keys": ["calculation", "status"],
    },
    {
        "id": "pulse_json_factors_02",
        "task_type": "format",
        "prompt": (
            "Provide all prime factors of 840 in sorted ascending order. "
            "Output RAW JSON ONLY without any markdown or code blocks:\n"
            '{"factors": [2, 2, 2, 3, 5, 7], "count": 6}'
        ),
        "required_keys": ["factors", "count"],
    },
    {
        "id": "pulse_reasoning_03",
        "task_type": "math",
        "prompt": (
            "A train travels 120 km at 60 km/h, then 180 km at 90 km/h. "
            "What is the total travel time in hours? "
            "Show brief reasoning and put your final answer strictly inside \\boxed{...}."
        ),
        "ground_truth": "4",
    },
]

TIER_2_REASONING_TASKS: List[Dict[str, Any]] = [
    {
        "id": "math_symbolic_01",
        "task_type": "math",
        "title": "Algebraic Radical Equation",
        "prompt": (
            "Solve for real x in the equation: sqrt(2*x + 5) - sqrt(x - 1) = 2. "
            "Determine the smaller real solution if multiple exist. Put the exact final number for x inside \\boxed{...}."
        ),
        "ground_truth": "2",
    },
    {
        "id": "math_symbolic_02",
        "task_type": "math",
        "title": "Combinatorics Fraction Simplification",
        "prompt": (
            "Evaluate the exact fraction: C(10, 3) / C(12, 4). "
            "Simplify the fraction completely into irreducible form a/b and write it strictly inside \\boxed{...}."
        ),
        "ground_truth": "8/33",
    },
    {
        "id": "math_symbolic_03",
        "task_type": "math",
        "title": "Trigonometric Exact Angle",
        "prompt": (
            "What is the exact value of cos(pi/12) * sin(pi/12)? "
            "Simplify completely and put your final exact fractional answer inside \\boxed{...}."
        ),
        "ground_truth": "1/4",
    },
    {
        "id": "code_algorithm_01",
        "task_type": "code",
        "title": "Longest Substring Without Repeating Characters",
        "prompt": (
            "Write a Python function `length_of_longest_substring(s: str) -> int` that finds "
            "the length of the longest substring without duplicate characters. "
            "Wrap your code strictly inside a ```python ... ``` block."
        ),
        "assertions": """
assert length_of_longest_substring("abcabcbb") == 3
assert length_of_longest_substring("bbbbb") == 1
assert length_of_longest_substring("pwwkew") == 3
assert length_of_longest_substring("") == 0
assert length_of_longest_substring("abcdef") == 6
assert length_of_longest_substring("dvdf") == 3
""",
    },
    {
        "id": "code_algorithm_02",
        "task_type": "code",
        "title": "Merge Overlapping Intervals",
        "prompt": (
            "Write a Python function `merge_intervals(intervals: list[list[int]]) -> list[list[int]]` "
            "that merges all overlapping intervals and returns the result sorted. "
            "Wrap your code strictly inside a ```python ... ``` block."
        ),
        "assertions": """
assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]
assert merge_intervals([[1,4],[4,5]]) == [[1,5]]
assert merge_intervals([]) == []
assert merge_intervals([[1,4],[2,3]]) == [[1,4]]
""",
    },
]
