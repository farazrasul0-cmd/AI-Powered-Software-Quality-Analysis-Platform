"""McCabe Cyclomatic and Cognitive Complexity AST Analyzers."""

import ast
from dataclasses import dataclass, field


@dataclass
class FunctionComplexity:
    name: str
    line_start: int
    line_end: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    param_count: int
    sloc: int


@dataclass
class ClassComplexity:
    name: str
    line_start: int
    line_end: int
    methods: list[FunctionComplexity] = field(default_factory=list)
    sloc: int = 0


@dataclass
class ComplexityReport:
    module_cyclomatic_complexity: int
    max_cyclomatic_complexity: int
    module_cognitive_complexity: int
    functions: list[FunctionComplexity] = field(default_factory=list)
    classes: list[ClassComplexity] = field(default_factory=list)


class CognitiveComplexityVisitor(ast.NodeVisitor):
    """Calculates Cognitive Complexity based on SonarSource specification.

    - Increments on: if, elif, else, for, while, except, bool_op sequences.
    - Adds nesting penalty for control structures nested within other control structures.
    """

    def __init__(self) -> None:
        self.complexity = 0
        self.nesting_level = 0

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1 + self.nesting_level
        self.nesting_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.nesting_level -= 1

        # Check else / elif
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # elif: does not increment nesting level for the elif itself
                self.visit(node.orelse[0])
            else:
                self.complexity += 1 + self.nesting_level
                self.nesting_level += 1
                for stmt in node.orelse:
                    self.visit(stmt)
                self.nesting_level -= 1

    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1 + self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.complexity += 1 + self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1 + self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1 + self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # Each consecutive boolean operator adds 1
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


class McCabeComplexityVisitor(ast.NodeVisitor):
    """Calculates classic McCabe Cyclomatic Complexity."""

    def __init__(self) -> None:
        self.complexity = 1

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


def analyze_complexity(tree: ast.AST) -> ComplexityReport:
    """Traverses an AST tree and produces detailed function, class, and module complexity metrics."""
    functions: list[FunctionComplexity] = []
    classes: list[ClassComplexity] = []

    for node in tree.body if hasattr(tree, "body") else []:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            mccabe = McCabeComplexityVisitor()
            mccabe.visit(node)

            cognitive = CognitiveComplexityVisitor()
            cognitive.visit(node)

            end_line = getattr(node, "end_lineno", node.lineno)
            fn_sloc = max(1, end_line - node.lineno + 1)

            functions.append(
                FunctionComplexity(
                    name=node.name,
                    line_start=node.lineno,
                    line_end=end_line,
                    cyclomatic_complexity=mccabe.complexity,
                    cognitive_complexity=cognitive.complexity,
                    param_count=len(node.args.args),
                    sloc=fn_sloc,
                )
            )

        elif isinstance(node, ast.ClassDef):
            class_methods: list[FunctionComplexity] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mccabe = McCabeComplexityVisitor()
                    mccabe.visit(item)

                    cognitive = CognitiveComplexityVisitor()
                    cognitive.visit(item)

                    end_line = getattr(item, "end_lineno", item.lineno)
                    method_sloc = max(1, end_line - item.lineno + 1)

                    class_methods.append(
                        FunctionComplexity(
                            name=item.name,
                            line_start=item.lineno,
                            line_end=end_line,
                            cyclomatic_complexity=mccabe.complexity,
                            cognitive_complexity=cognitive.complexity,
                            param_count=len(item.args.args),
                            sloc=method_sloc,
                        )
                    )

            cls_end = getattr(node, "end_lineno", node.lineno)
            classes.append(
                ClassComplexity(
                    name=node.name,
                    line_start=node.lineno,
                    line_end=cls_end,
                    methods=class_methods,
                    sloc=max(1, cls_end - node.lineno + 1),
                )
            )

    all_fn = functions + [m for c in classes for m in c.methods]
    total_mccabe = sum(f.cyclomatic_complexity for f in all_fn) if all_fn else 1
    max_mccabe = max((f.cyclomatic_complexity for f in all_fn), default=1)
    total_cognitive = sum(f.cognitive_complexity for f in all_fn) if all_fn else 0

    return ComplexityReport(
        module_cyclomatic_complexity=total_mccabe,
        max_cyclomatic_complexity=max_mccabe,
        module_cognitive_complexity=total_cognitive,
        functions=functions,
        classes=classes,
    )
