"""
LiveLLM - Mathematical & Symbolic Evaluator
Uses SymPy to verify mathematical outputs independent of formatting differences.
Extracts \\boxed{...} or equivalent answer tags and checks algebraic equality.
"""

import re
from typing import Tuple, Optional
import sympy
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def extract_boxed_answer(text: str) -> Optional[str]:
    """
    Extracts the content inside LaTeX \\boxed{...} or fallback patterns.
    Handles nested braces properly.
    """
    if not text:
        return None

    # 1. Search for \boxed{
    idx = text.rfind(r"\boxed{")
    if idx != -1:
        start = idx + len(r"\boxed{")
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        if depth == 0:
            return text[start : i - 1].strip()

    # 2. Fallback: <answer>...</answer>
    tag_match = re.search(r"<answer>(.*?)</answer>", text, re.DOTALL | re.IGNORECASE)
    if tag_match:
        return tag_match.group(1).strip()

    # 3. Fallback: "The answer is ..." or "Final Answer: ..."
    phrase_match = re.search(
        r"(?:the\s+final\s+answer\s+is|the\s+answer\s+is|final\s+answer:?)\s*([^\n\.]+)",
        text,
        re.IGNORECASE,
    )
    if phrase_match:
        candidate = phrase_match.group(1).strip()
        # Clean potential markdown
        candidate = candidate.strip("$*` \t")
        return candidate

    return None


def clean_latex_math(expr_str: str) -> str:
    """Cleans LaTeX notation into SymPy parseable strings."""
    if not expr_str:
        return ""
    s = expr_str.strip()
    s = s.strip("$ \n\t")
    # Replace common LaTeX constructs
    s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", s)
    s = s.replace(r"\cdot", "*").replace(r"\times", "*")
    s = s.replace(r"\pi", "pi")
    s = s.replace(r"\left", "").replace(r"\right", "")
    s = s.replace(r"\%", "/100")
    s = s.replace(",", "")  # 1,000 -> 1000
    return s.strip()


def verify_math_answer(model_output: str, ground_truth: str) -> Tuple[bool, Optional[str], str]:
    """
    Verifies model output against ground truth using SymPy symbolic equivalence.
    Returns: (is_correct, extracted_answer, debug_message)
    """
    extracted = extract_boxed_answer(model_output)
    if not extracted:
        return False, None, "No boxed or tagged answer found in output"

    clean_extracted = clean_latex_math(extracted)
    clean_gt = clean_latex_math(ground_truth)

    # Direct string match (fast path)
    if clean_extracted.lower() == clean_gt.lower():
        return True, extracted, "Exact string match"

    # SymPy symbolic equality test
    try:
        expr_cand = parse_expr(clean_extracted, transformations=_TRANSFORMATIONS, evaluate=True)
        expr_gt = parse_expr(clean_gt, transformations=_TRANSFORMATIONS, evaluate=True)

        diff = sympy.simplify(expr_cand - expr_gt)
        if diff == 0:
            return True, extracted, f"Symbolically identical (diff=0): {expr_cand} == {expr_gt}"
        
        # Float evaluation test for numerical tolerances (e.g. 1/3 vs 0.33333333)
        try:
            val_cand = float(expr_cand.evalf())
            val_gt = float(expr_gt.evalf())
            if abs(val_cand - val_gt) < 1e-6:
                return True, extracted, f"Numerically equivalent within 1e-6: {val_cand} ~= {val_gt}"
        except Exception:
            pass

        return False, extracted, f"Symbolic mismatch: {expr_cand} != {expr_gt}"

    except Exception as e:
        # Fallback to normalized alphanumeric match if sympy cannot parse (e.g. complex coordinate tuples)
        norm_cand = re.sub(r"\s+", "", clean_extracted)
        norm_gt = re.sub(r"\s+", "", clean_gt)
        if norm_cand == norm_gt:
            return True, extracted, "Normalized string match after parse exception"
        return False, extracted, f"SymPy parsing/evaluation error: {str(e)}"
