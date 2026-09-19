"""Unit tests for AST Parsing and McCabe Cyclomatic Complexity."""

from app.infrastructure.ast_parser.metrics_calc import (
    calculate_maintainability_index,
    estimate_halstead_metrics,
)
from app.infrastructure.ast_parser.python_visitor import analyze_python_source


def test_simple_function_analysis():
    code = """
def add(a, b):
    \"\"\"Docstring.\"\"\"
    return a + b
"""
    metrics = analyze_python_source(code)
    assert metrics.sloc > 0
    assert metrics.function_count == 1
    assert metrics.class_count == 0
    assert metrics.total_cyclomatic_complexity == 1
    assert metrics.functions[0].name == "add"
    assert metrics.functions[0].has_docstring is True


def test_complex_branching_function():
    code = """
def evaluate(x, y, z):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
    elif y > 0:
        while z > 0:
            z -= 1
    else:
        try:
            return x / y
        except ZeroDivisionError:
            return 0
"""
    metrics = analyze_python_source(code)
    assert metrics.function_count == 1
    # Base (1) + if (1) + for (1) + if (1) + elif (1) + while (1) + except (1) = 7
    assert metrics.max_cyclomatic_complexity >= 6


def test_class_with_methods():
    code = """
class Calculator:
    def __init__(self):
        self.val = 0

    def add(self, n):
        if n > 0:
            self.val += n
        return self.val
"""
    metrics = analyze_python_source(code)
    assert metrics.class_count == 1
    assert metrics.function_count == 2
    assert len(metrics.classes[0].methods) == 2


def test_halstead_and_maintainability():
    code = "x = 10\ny = 20\nz = x + y\nprint(z)"
    halstead = estimate_halstead_metrics(code)
    assert halstead["vocabulary"] > 0
    assert halstead["volume"] > 0

    mi = calculate_maintainability_index(
        sloc=4, cyclomatic_complexity=1, halstead_volume=halstead["volume"]
    )
    assert 0 <= mi <= 100
