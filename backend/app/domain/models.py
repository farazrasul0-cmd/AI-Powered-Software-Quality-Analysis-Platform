"""Pure domain models and data transfer objects for repository intelligence."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ImportEdge:
    """Represents a directional dependency edge where source_module imports target_module."""

    source_module: str
    target_module: str
    is_internal: bool
    imported_symbols: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CircularDependencyViolation:
    """Represents a circular dependency loop (cycle) between modules."""

    cycle_path: list[str]
    description: str

    @property
    def cycle_length(self) -> int:
        return len(self.cycle_path)


@dataclass
class ModuleCoupling:
    """Afferent (incoming) and Efferent (outgoing) coupling metrics for a module."""

    module_name: str
    afferent_coupling: int  # Ca: number of other modules that depend on this module
    efferent_coupling: int  # Ce: number of other modules this module depends on

    @property
    def instability(self) -> float:
        """I = Ce / (Ca + Ce). Measures resilience to change (0 = stable, 1 = unstable)."""
        total = self.afferent_coupling + self.efferent_coupling
        return round(self.efferent_coupling / total, 2) if total > 0 else 0.0


@dataclass
class DependencyGraph:
    """Directed dependency graph across repository modules."""

    nodes: set[str] = field(default_factory=set)
    edges: list[ImportEdge] = field(default_factory=list)
    circular_dependencies: list[CircularDependencyViolation] = field(default_factory=list)
    coupling_metrics: list[ModuleCoupling] = field(default_factory=list)


@dataclass(frozen=True)
class DiffHunk:
    """Represents a modified chunk in a unified git diff."""

    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    added_lines: list[int] = field(default_factory=list)
    deleted_lines: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class FileDiff:
    """Represents changes in a single file from a Git diff."""

    old_path: str | None
    new_path: str
    is_new: bool
    is_deleted: bool
    is_modified: bool
    hunks: list[DiffHunk] = field(default_factory=list)

    @property
    def total_added_lines(self) -> int:
        return sum(len(h.added_lines) for h in self.hunks)

    @property
    def total_deleted_lines(self) -> int:
        return sum(len(h.deleted_lines) for h in self.hunks)
