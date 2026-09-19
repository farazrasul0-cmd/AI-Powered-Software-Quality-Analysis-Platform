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


class DependencyGraphBuilder:
    """Builds an import dependency graph from Python source files and detects architectural circular dependencies."""

    @classmethod
    def build_graph(cls, repo_root: Path, py_files: list[Path]) -> DependencyGraph:
        # 1. Map relative module identifiers (e.g. 'app.services.auth' or 'services.auth')
        module_path_map: dict[str, Path] = {}
        for p in py_files:
            rel = p.relative_to(repo_root)
            # Remove .py and convert slashes to dots
            parts = list(rel.parts)
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]
            if parts[-1] == "__init__":
                parts = parts[:-1]
            mod_name = ".".join(parts) if parts else "root"
            module_path_map[mod_name] = p
            # Also store with first part omitted if inside root package
            if len(parts) > 1:
                module_path_map[".".join(parts[1:])] = p

        all_modules = set(module_path_map.keys())
        edges: list[ImportEdge] = []
        adj_list: dict[str, set[str]] = defaultdict(set)

        # 2. Extract AST imports for each Python file
        for mod_name, file_path in module_path_map.items():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content)
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = alias.name
                        is_internal = any(
                            target == m or target.startswith(m + ".") or m.startswith(target + ".")
                            for m in all_modules
                        )
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
                        elif not is_internal:
                            edges.append(
                                ImportEdge(
                                    source_module=mod_name,
                                    target_module=target.split(".")[0],
                                    is_internal=False,
                                    imported_symbols=[alias.asname or alias.name],
                                )
                            )

                elif isinstance(node, ast.ImportFrom):
                    imported_names = [a.name for a in node.names]
                    if node.level and node.level > 0:
                        # Relative import e.g. from .utils import helper
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

        # 3. Detect Cycles using Tarjan's Strongly Connected Components
        cycles = cls._detect_cycles(all_modules, adj_list)

        # 4. Calculate Afferent and Efferent Coupling
        coupling_list = cls._compute_coupling(all_modules, adj_list)

        return DependencyGraph(
            nodes=all_modules,
            edges=edges,
            circular_dependencies=cycles,
            coupling_metrics=coupling_list,
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
        # Check prefix matches
        for m in sorted(all_modules, key=len, reverse=True):
            if target == m or target.startswith(m + "."):
                return m
        return None

    @classmethod
    def _detect_cycles(
        cls, nodes: set[str], adj: dict[str, set[str]]
    ) -> list[CircularDependencyViolation]:
        """Detects circular dependencies using Tarjan's SCC algorithm."""
        index = 0
        indices: dict[str, int] = {}
        lowlink: dict[str, int] = {}
        on_stack: set[str] = set()
        stack: list[str] = []
        sccs: list[list[str]] = []

        def strongconnect(v: str):
            nonlocal index
            indices[v] = index
            lowlink[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)

            for w in adj.get(v, set()):
                if w not in indices:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], indices[w])

            if lowlink[v] == indices[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.append(w)
                    if w == v:
                        break
                if len(scc) > 1:
                    sccs.append(scc)

        for node in nodes:
            if node not in indices:
                strongconnect(node)

        violations: list[CircularDependencyViolation] = []
        for scc in sccs:
            cycle = scc + [scc[0]]
            violations.append(
                CircularDependencyViolation(
                    cycle_path=cycle,
                    description=f"Circular dependency detected: {' -> '.join(cycle)}",
                )
            )
        return violations

    @staticmethod
    def _compute_coupling(nodes: set[str], adj: dict[str, set[str]]) -> list[ModuleCoupling]:
        # Efferent coupling (Ce): out-degree to internal modules
        # Afferent coupling (Ca): in-degree from internal modules
        afferent_counts: dict[str, int] = defaultdict(int)
        for _src, targets in adj.items():
            for t in targets:
                if t in nodes:
                    afferent_counts[t] += 1

        results = []
        for n in sorted(nodes):
            ce = len(adj.get(n, set()))
            ca = afferent_counts.get(n, 0)
            results.append(
                ModuleCoupling(module_name=n, afferent_coupling=ca, efferent_coupling=ce)
            )
        return results
