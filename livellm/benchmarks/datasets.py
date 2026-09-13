"""
LiveLLM - Current Production Models & Real Benchmark Tasks
Reflects the latest frontier models (GPT-4o, Claude 3.5 Sonnet, Gemini 2.0, DeepSeek R1/V3, Llama 3.3).
"""

from typing import List, Dict, Any

SUPPORTED_MODELS: List[Dict[str, Any]] = [
    {
        "id": "gpt-4o",
        "name": "GPT-4o (2024-11-20)",
        "provider": "OpenAI",
        "tier": "Flagship Multimodal",
        "baseline_tps": 94.0,
        "baseline_ttft_ms": 310.0,
        "base_accuracy": 0.94,
    },
    {
        "id": "gpt-4o-mini",
        "name": "GPT-4o Mini",
        "provider": "OpenAI",
        "tier": "Efficient",
        "baseline_tps": 135.0,
        "baseline_ttft_ms": 220.0,
        "base_accuracy": 0.88,
    },
    {
        "id": "claude-3-5-sonnet-20241022",
        "name": "Claude 3.5 Sonnet (New)",
        "provider": "Anthropic",
        "tier": "Flagship Coding/Math",
        "baseline_tps": 78.0,
        "baseline_ttft_ms": 380.0,
        "base_accuracy": 0.96,
    },
    {
        "id": "claude-3-5-haiku-20241022",
        "name": "Claude 3.5 Haiku",
        "provider": "Anthropic",
        "tier": "Fast Agentic",
        "baseline_tps": 115.0,
        "baseline_ttft_ms": 260.0,
        "base_accuracy": 0.89,
    },
    {
        "id": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash",
        "provider": "Google",
        "tier": "Next-Gen Speed",
        "baseline_tps": 160.0,
        "baseline_ttft_ms": 240.0,
        "base_accuracy": 0.93,
    },
    {
        "id": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro",
        "provider": "Google",
        "tier": "2M Long Context",
        "baseline_tps": 65.0,
        "baseline_ttft_ms": 460.0,
        "base_accuracy": 0.92,
    },
    {
        "id": "deepseek-chat",
        "name": "DeepSeek V3 (671B MoE)",
        "provider": "DeepSeek",
        "tier": "Open Frontier MoE",
        "baseline_tps": 62.0,
        "baseline_ttft_ms": 580.0,
        "base_accuracy": 0.92,
    },
    {
        "id": "deepseek-reasoner",
        "name": "DeepSeek R1 (Reasoning)",
        "provider": "DeepSeek",
        "tier": "RL Reasoning / CoT",
        "baseline_tps": 48.0,
        "baseline_ttft_ms": 750.0,
        "base_accuracy": 0.97,
    },
    {
        "id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B (Groq LPU)",
        "provider": "Groq / Meta",
        "tier": "Ultra-Low Latency",
        "baseline_tps": 280.0,
        "baseline_ttft_ms": 180.0,
        "base_accuracy": 0.89,
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
