"""Dependency Graph Builder and Circular Import Detector."""

import ast
from collections import defaultdict
from pathlib import Path

from app.domain.models import (
    CircularDependencyViolation,
    DependencyGraph,
    ImportEdge,
    ModuleCoupling,
)


class RuntimeImportVisitor(ast.NodeVisitor):
    """AST visitor that extracts runtime import edges while ignoring TYPE_CHECKING guards."""

    def __init__(self) -> None:
        self.import_nodes: list[ast.Import | ast.ImportFrom] = []

    def visit_If(self, node: ast.If) -> None:
        # Check if condition is `TYPE_CHECKING` or `typing.TYPE_CHECKING`
        is_type_checking = False
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            is_type_checking = True
        elif isinstance(node.test, ast.Attribute) and node.test.attr == "TYPE_CHECKING":
            is_type_checking = True

        if is_type_checking:
            # Skip the body of `if TYPE_CHECKING:`; type-only annotations don't execute at runtime
            for child in node.orelse:
                self.visit(child)
        else:
            self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        self.import_nodes.append(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.import_nodes.append(node)


class TarjanSCCDetector:
    """Computes Strongly Connected Components (SCC) to identify circular dependency cycles."""

    def __init__(self, nodes: set[str], adj: dict[str, set[str]]) -> None:
        self.nodes = nodes
        self.adj = adj
        self.index = 0
        self.indices: dict[str, int] = {}
        self.lowlink: dict[str, int] = {}
        self.on_stack: set[str] = set()
        self.stack: list[str] = []
        self.sccs: list[list[str]] = []

    def detect_cycles(self) -> list[CircularDependencyViolation]:
        for node in sorted(self.nodes):
            if node not in self.indices:
                self._strongconnect(node)

        violations: list[CircularDependencyViolation] = []
        for scc in self.sccs:
            cycle = scc + [scc[0]]
            violations.append(
                CircularDependencyViolation(
                    cycle_path=cycle,
                    description=f"Circular dependency detected: {' -> '.join(cycle)}",
                )
            )
        return violations

    def _strongconnect(self, v: str) -> None:
        self.indices[v] = self.index
        self.lowlink[v] = self.index
        self.index += 1
        self.stack.append(v)
        self.on_stack.add(v)

        for w in sorted(self.adj.get(v, set())):
            if w not in self.indices:
                self._strongconnect(w)
                self.lowlink[v] = min(self.lowlink[v], self.lowlink[w])
            elif w in self.on_stack:
                self.lowlink[v] = min(self.lowlink[v], self.indices[w])

        if self.lowlink[v] == self.indices[v]:
            scc: list[str] = []
            while True:
                w = self.stack.pop()
                self.on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            if len(scc) > 1:
                self.sccs.append(scc)


class DependencyGraphBuilder:
    """Builds an import dependency graph from Python source files and detects architectural circular dependencies."""

    @classmethod
    def build_graph(cls, repo_root: Path, py_files: list[Path]) -> DependencyGraph:
        # 1. Map relative module identifiers
        module_path_map = cls._build_module_map(repo_root, py_files)
        all_modules = set(module_path_map.keys())

        edges: list[ImportEdge] = []
        adj_list: dict[str, set[str]] = defaultdict(set)

        # 2. Extract AST runtime imports
        for mod_name, file_path in module_path_map.items():
            cls._extract_file_imports(mod_name, file_path, all_modules, edges, adj_list)

        # 3. Detect Cycles using Tarjan's SCC
        detector = TarjanSCCDetector(all_modules, adj_list)
        cycles = detector.detect_cycles()

        # 4. Calculate Afferent and Efferent Coupling
        coupling_list = cls._compute_coupling(all_modules, adj_list)

        return DependencyGraph(
            nodes=all_modules,
            edges=edges,
            circular_dependencies=cycles,
            coupling_metrics=coupling_list,
        )

    @staticmethod
    def _build_module_map(repo_root: Path, py_files: list[Path]) -> dict[str, Path]:
        module_map: dict[str, Path] = {}
        for p in py_files:
            rel = p.relative_to(repo_root)
            parts = list(rel.parts)
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]
            if parts[-1] == "__init__":
                parts = parts[:-1]
            mod_name = ".".join(parts) if parts else "root"
            module_map[mod_name] = p
            if len(parts) > 1:
                module_map[".".join(parts[1:])] = p
        return module_map

    @classmethod
    def _extract_file_imports(
        cls,
        mod_name: str,
        file_path: Path,
        all_modules: set[str],
        edges: list[ImportEdge],
        adj_list: dict[str, set[str]],
    ) -> None:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
        except Exception:
            return

        visitor = RuntimeImportVisitor()
        visitor.visit(tree)

        for node in visitor.import_nodes:
            if isinstance(node, ast.Import):
                cls._handle_ast_import(node, mod_name, all_modules, edges, adj_list)
            elif isinstance(node, ast.ImportFrom):
                cls._handle_ast_import_from(node, mod_name, all_modules, edges, adj_list)

    @classmethod
    def _handle_ast_import(
        cls,
        node: ast.Import,
        mod_name: str,
        all_modules: set[str],
        edges: list[ImportEdge],
        adj_list: dict[str, set[str]],
    ) -> None:
        for alias in node.names:
            target = alias.name
            resolved = cls._resolve_internal_module(target, all_modules)
            if resolved and resolved != mod_name:
                edges.append(
                    ImportEdge(
                        source_module=mod_name,
                        target_module=resolved,
                        is_internal=True,
                        imported_symbols=[alias.asname or alias.name],
                    )
                )
                adj_list[mod_name].add(resolved)
            elif not resolved:
                edges.append(
                    ImportEdge(
                        source_module=mod_name,
                        target_module=target.split(".")[0],
                        is_internal=False,
                        imported_symbols=[alias.asname or alias.name],
                    )
                )

    @classmethod
    def _handle_ast_import_from(
        cls,
        node: ast.ImportFrom,
        mod_name: str,
        all_modules: set[str],
        edges: list[ImportEdge],
        adj_list: dict[str, set[str]],
    ) -> None:
        imported_names = [a.name for a in node.names]
        if node.level and node.level > 0:
            target = cls._resolve_relative_import(mod_name, node.level, node.module)
        else:
            target = node.module or ""

        resolved = cls._resolve_internal_module(target, all_modules)
        if resolved and resolved != mod_name:
            edges.append(
                ImportEdge(
                    source_module=mod_name,
                    target_module=resolved,
                    is_internal=True,
                    imported_symbols=imported_names,
                )
            )
            adj_list[mod_name].add(resolved)
        elif target:
            edges.append(
                ImportEdge(
                    source_module=mod_name,
                    target_module=target.split(".")[0],
                    is_internal=False,
                    imported_symbols=imported_names,
                )
            )

    @staticmethod
    def _resolve_relative_import(source_mod: str, level: int, module_name: str | None) -> str:
        parts = source_mod.split(".")
        if level <= len(parts):
            base = parts[:-level]
        else:
            base = []
        if module_name:
            base.append(module_name)
        return ".".join(base)

    @staticmethod
    def _resolve_internal_module(target: str, all_modules: set[str]) -> str | None:
        if target in all_modules:
            return target
        for m in sorted(all_modules, key=len, reverse=True):
            if target == m or target.startswith(m + "."):
                return m
        return None

    @staticmethod
    def _compute_coupling(nodes: set[str], adj: dict[str, set[str]]) -> list[ModuleCoupling]:
        afferent_counts: dict[str, int] = defaultdict(int)
        for _src, targets in adj.items():
            for t in targets:
                if t in nodes:
                    afferent_counts[t] += 1

        results: list[ModuleCoupling] = []
        for n in sorted(nodes):
            ce = len(adj.get(n, set()))
            ca = afferent_counts.get(n, 0)
            results.append(
                ModuleCoupling(module_name=n, afferent_coupling=ca, efferent_coupling=ce)
            )
        return results
