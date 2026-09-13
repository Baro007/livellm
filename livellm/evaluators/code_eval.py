"""
LiveLLM - Sandboxed Code Evaluator
Extracts generated Python code from model responses and executes it in an isolated
subprocess against predefined unit test assertions with strict execution timeouts.
"""

import ast
import re
import sys
import subprocess
import tempfile
import os
from typing import Tuple, Optional


def extract_python_code(text: str) -> Optional[str]:
    """Extracts executable python code block from markdown or raw text."""
    if not text:
        return None

    # Find ```python ... ``` blocks
    matches = re.findall(r"```(?:python|py)?\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if matches:
        # Prefer the longest code block
        return max(matches, key=len).strip()

    # Fallback: if text starts with def or import, might be raw code
    if "def " in text:
        lines = []
        in_code = False
        for line in text.splitlines():
            if line.strip().startswith(("import ", "from ", "def ", "class ", "    ", "\t")):
                in_code = True
                lines.append(line)
            elif in_code and (line.strip() == "" or line.startswith("#")):
                lines.append(line)
            elif in_code and not (line.startswith(" ") or line.startswith("\t")):
                # end of indented block
                if line.strip().startswith(("return ", "yield ", "if ", "for ", "while ", "try ", "except ")):
                    lines.append(line)
                else:
                    break
        if lines:
            return "\n".join(lines).strip()

    return None


def validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Validates AST syntax without executing."""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"


def execute_sandboxed_code(
    code: str,
    test_assertions: str,
    timeout_seconds: float = 3.0
) -> Tuple[bool, float, str]:
    """
    Executes code concatenated with test assertions in an isolated Python subprocess.
    Returns: (passed: bool, duration_seconds: float, message: str)
    """
    valid_syntax, err = validate_python_syntax(code)
    if not valid_syntax:
        return False, 0.0, f"Code syntax invalid: {err}"

    full_script = f"""# -*- coding: utf-8 -*-
import sys
import math
import collections
import itertools

# --- Candidate Solution ---
{code}

# --- Verification Assertions ---
{test_assertions}

print("__LIVELM_SUCCESS__")
"""

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(full_script)
        temp_path = f.name

    try:
        start_time = os.times().elapsed
        res = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        elapsed = os.times().elapsed - start_time

        if res.returncode == 0 and "__LIVELM_SUCCESS__" in res.stdout:
            return True, elapsed, "All unit tests passed"
        else:
            stderr_snippet = (res.stderr or res.stdout or "Test assertion failed").strip()
            # Truncate long tracebacks to last 4 lines
            lines = stderr_snippet.splitlines()
            short_err = "\n".join(lines[-4:]) if len(lines) > 4 else stderr_snippet
            return False, elapsed, f"Execution failed (code {res.returncode}): {short_err}"

    except subprocess.TimeoutExpired:
        return False, timeout_seconds, f"Timeout expired (> {timeout_seconds}s)"
    except Exception as e:
        return False, 0.0, f"Subprocess runner error: {str(e)}"
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
