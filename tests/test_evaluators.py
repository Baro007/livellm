"""
LiveLLM - Tests for Evaluators
Verifies SymPy symbolic equivalence, sandboxed code execution, and JSON validation.
"""

import pytest
from livellm.evaluators.math_eval import extract_boxed_answer, verify_math_answer
from livellm.evaluators.code_eval import extract_python_code, execute_sandboxed_code
from livellm.evaluators.format_eval import extract_and_validate_json


def test_extract_boxed_answer():
    text1 = r"The final calculation yields \boxed{\frac{8}{33}} after simplification."
    assert extract_boxed_answer(text1) == r"\frac{8}{33}"

    text2 = r"Nested brackets: \boxed{\sqrt{2x + 5}}."
    assert extract_boxed_answer(text2) == r"\sqrt{2x + 5}"

    text3 = "Final answer: 42"
    assert extract_boxed_answer(text3) == "42"


def test_sympy_symbolic_math_equivalence():
    # Fractions vs decimal
    is_corr, ans, msg = verify_math_answer(r"The result is \boxed{0.5}.", "1/2")
    assert is_corr is True

    # LaTeX fraction vs standard division
    is_corr, ans, msg = verify_math_answer(r"\boxed{\frac{8}{33}}", "8/33")
    assert is_corr is True

    # Radical simplification
    is_corr, ans, msg = verify_math_answer(r"\boxed{\sqrt{16}}", "4")
    assert is_corr is True

    # Incorrect answer
    is_corr, ans, msg = verify_math_answer(r"\boxed{1/3}", "1/4")
    assert is_corr is False


def test_sandboxed_code_execution():
    code_good = """
def length_of_longest_substring(s: str) -> int:
    char_map = {}
    left = 0
    max_len = 0
    for right, char in enumerate(s):
        if char in char_map and char_map[char] >= left:
            left = char_map[char] + 1
        char_map[char] = right
        max_len = max(max_len, right - left + 1)
    return max_len
"""
    assertions = """
assert length_of_longest_substring("abcabcbb") == 3
assert length_of_longest_substring("bbbbb") == 1
assert length_of_longest_substring("") == 0
"""
    passed, dur, msg = execute_sandboxed_code(code_good, assertions)
    assert passed is True
    assert "All unit tests passed" in msg

    # Failing assertion
    assertions_fail = 'assert length_of_longest_substring("abc") == 99'
    passed_fail, _, _ = execute_sandboxed_code(code_good, assertions_fail)
    assert passed_fail is False


def test_json_format_evaluation():
    valid_raw = '{"calculation": 57661, "status": "ok"}'
    is_val, data, msg = extract_and_validate_json(valid_raw, required_keys=["calculation", "status"])
    assert is_val is True
    assert data["calculation"] == 57661

    # Wrapped in markdown
    markdown_wrapped = '```json\n{"calculation": 57661, "status": "ok"}\n```'
    is_val, data, msg = extract_and_validate_json(markdown_wrapped, required_keys=["calculation"])
    assert is_val is True
    assert data["calculation"] == 57661

    # Invalid JSON
    invalid_raw = '{bad_json: True}'
    is_val, _, _ = extract_and_validate_json(invalid_raw)
    assert is_val is False
