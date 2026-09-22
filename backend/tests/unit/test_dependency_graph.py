"""Unit tests for Dependency Graph Builder and Tarjan's Cycle Detection."""

import tempfile
from pathlib import Path

from app.infrastructure.git.dependency_graph import DependencyGraphBuilder


def test_acyclic_dependency_graph():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # File A: imports B
        file_a = root / "module_a.py"
        file_a.write_text("from module_b import helper\ndef main(): helper()", encoding="utf-8")

        # File B: no internal imports
        file_b = root / "module_b.py"
        file_b.write_text("def helper(): pass", encoding="utf-8")

        graph = DependencyGraphBuilder.build_graph(root, [file_a, file_b])

        assert "module_a" in graph.nodes
        assert "module_b" in graph.nodes
        assert len(graph.circular_dependencies) == 0

        # module_b has Ca = 1 (imported by module_a), Ce = 0
        b_coupling = next(c for c in graph.coupling_metrics if c.module_name == "module_b")
        assert b_coupling.afferent_coupling == 1
        assert b_coupling.efferent_coupling == 0
        assert b_coupling.instability == 0.0

        # module_a has Ca = 0, Ce = 1 (depends on module_b)
        a_coupling = next(c for c in graph.coupling_metrics if c.module_name == "module_a")
        assert a_coupling.afferent_coupling == 0
        assert a_coupling.efferent_coupling == 1
        assert a_coupling.instability == 1.0


def test_circular_dependency_detection():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # File A: imports B
        file_a = root / "service_a.py"
        file_a.write_text("import service_b\ndef do_a(): pass", encoding="utf-8")

        # File B: imports A (creates cycle A -> B -> A)
        file_b = root / "service_b.py"
        file_b.write_text("import service_a\ndef do_b(): pass", encoding="utf-8")

        graph = DependencyGraphBuilder.build_graph(root, [file_a, file_b])

        assert len(graph.circular_dependencies) >= 1
        cycle = graph.circular_dependencies[0]
        assert "service_a" in cycle.cycle_path
        assert "service_b" in cycle.cycle_path
        assert "Circular dependency detected" in cycle.description


def test_relative_import_resolution():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        pkg = root / "pkg"
        pkg.mkdir()

        init_file = pkg / "__init__.py"
        init_file.write_text("", encoding="utf-8")

        file_x = pkg / "x.py"
        file_x.write_text("from .y import something", encoding="utf-8")

        file_y = pkg / "y.py"
        file_y.write_text("something = 42", encoding="utf-8")

        graph = DependencyGraphBuilder.build_graph(root, [init_file, file_x, file_y])
        assert len(graph.circular_dependencies) == 0
        internal_edges = [e for e in graph.edges if e.is_internal]
        assert len(internal_edges) >= 1


def test_type_checking_guarded_imports_ignored():
    """Confirms that imports inside `if TYPE_CHECKING:` blocks do not generate runtime circular edges."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # File A: imports B at runtime
        file_a = root / "model_a.py"
        file_a.write_text(
            "from model_b import ModelB\nclass ModelA:\n    pass\n",
            encoding="utf-8",
        )

        # File B: imports A ONLY inside `if TYPE_CHECKING:`
        file_b = root / "model_b.py"
        file_b.write_text(
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from model_a import ModelA\n"
            "class ModelB:\n"
            "    pass\n",
            encoding="utf-8",
        )

        graph = DependencyGraphBuilder.build_graph(root, [file_a, file_b])
        # Crucial check: 0 cycles detected!
        assert len(graph.circular_dependencies) == 0

