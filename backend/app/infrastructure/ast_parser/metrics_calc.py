"""Halstead Software Science and Maintainability Index calculator."""

import math
import re
from typing import Any


def calculate_maintainability_index(
    sloc: int, cyclomatic_complexity: int, halstead_volume: float
) -> float:
    """Calculates the standard Maintainability Index (MI) scaled from 0 to 100.

    Standard formula: MI = max(0, (171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(LOC)) * 100 / 171)
    """
    if sloc <= 0:
        return 100.0

    v = max(halstead_volume, 1.0)
    g = max(cyclomatic_complexity, 1)
    loc = max(sloc, 1)

    raw_mi = 171.0 - 5.2 * math.log(v) - 0.23 * g - 16.2 * math.log(loc)
    normalized_mi = max(0.0, min(100.0, raw_mi))
    return round(normalized_mi, 2)


def estimate_halstead_metrics(code_str: str) -> dict[str, Any]:
    """Extracts operators and operands to estimate Halstead program metrics."""
    # Simple lexical token categorization
    operator_patterns = [
        r"[+\-*/%]=?",
        r"==|!=|<=|>=|<|>",
        r"&&|\|\||!",
        r"&|\||\^|~|<<|>>",
        r"=|\(|\)|\[|\]|\{|\}|,|;|:|\.",
        r"\band\b|\bor\b|\bnot\b|\bin\b|\bis\b",
        r"\bif\b|\belse\b|\belif\b|\bfor\b|\bwhile\b|\breturn\b|\bdef\b|\bclass\b",
    ]
    combined_op = re.compile("|".join(operator_patterns))

    operators = combined_op.findall(code_str)
    # Identifiers and numbers as operands
    operand_pattern = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b|\b\d+(\.\d+)?\b")
    all_tokens = operand_pattern.findall(code_str)
    operands = [
        tok[0] if isinstance(tok, tuple) else tok for tok in all_tokens if tok not in operators
    ]

    n1 = len(set(operators))  # distinct operators
    n2 = len(set(operands))  # distinct operands
    total_operators = len(operators)  # total operators
    total_operands = len(operands)  # total operands

    n = max(n1 + n2, 1)  # vocabulary
    length = total_operators + total_operands  # length

    volume = length * math.log2(n) if n > 1 else 0.0
    difficulty = ((n1 / 2.0) * (total_operands / max(n2, 1))) if n2 > 0 else 1.0
    effort = difficulty * volume
    bugs = volume / 3000.0  # estimated defect count

    return {
        "distinct_operators": n1,
        "distinct_operands": n2,
        "total_operators": total_operators,
        "total_operands": total_operands,
        "vocabulary": n,
        "length": length,
        "volume": round(volume, 2),
        "difficulty": round(difficulty, 2),
        "effort": round(effort, 2),
        "estimated_bugs": round(bugs, 3),
    }
