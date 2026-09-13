"""
LiveLLM - Format & Negative Constraints Evaluator
Measures instruction-following fidelity: JSON schema validation and negative constraint adherence.
"""

import json
import re
from typing import Tuple, Dict, Any, Optional


def extract_and_validate_json(text: str, required_keys: Optional[list] = None) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Validates whether the model adhered to strict JSON output instructions.
    Checks for illegal wrapping or parse errors.
    """
    if not text:
        return False, None, "Empty response"

    cleaned = text.strip()
    # Check if model broke instructions by adding markdown code fences
    has_markdown_fences = bool(re.search(r"```(?:json)?", cleaned))

    # Try direct parse
    try:
        data = json.loads(cleaned)
        if required_keys:
            missing = [k for k in required_keys if k not in data]
            if missing:
                return False, data, f"Missing required keys: {missing}"
        penalty_msg = " (Warning: markdown fences included despite raw JSON instruction)" if has_markdown_fences else ""
        return True, data, f"Valid JSON{penalty_msg}"
    except json.JSONDecodeError:
        pass

    # Try extracting inside ```json ... ```
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL)
    if match:
        candidate = match.group(1).strip()
        try:
            data = json.loads(candidate)
            if required_keys:
                missing = [k for k in required_keys if k not in data]
                if missing:
                    return False, data, f"Missing required keys: {missing}"
            return True, data, "Valid JSON inside markdown block (failed strict zero-markdown constraint)"
        except json.JSONDecodeError as e:
            return False, None, f"JSON inside markdown is invalid: {e.msg}"

    # Try finding outermost braces { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace : last_brace + 1]
        try:
            data = json.loads(candidate)
            return False, data, "JSON had pre/post narrative text (instruction drift)"
        except json.JSONDecodeError:
            pass

    return False, None, "Could not extract valid JSON structure"
