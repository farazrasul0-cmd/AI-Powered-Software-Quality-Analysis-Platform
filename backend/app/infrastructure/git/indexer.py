"""Repository file indexing and tree walking with ignore filters."""

from collections.abc import Generator
from pathlib import Path

IGNORED_DIRS = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "target",
    "bin",
    "obj",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

IGNORED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".dll",
    ".so",
    ".dylib",
    ".exe",
    ".bin",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".webp",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".sqlite",
    ".db",
    ".lock",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}


class FileIndexer:
    @staticmethod
    def is_text_source_file(file_path: Path) -> bool:
        if file_path.suffix.lower() in IGNORED_EXTENSIONS:
            return False
        # Quick check for null bytes to avoid binary files
        try:
            with file_path.open("rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk:
                    return False
            return True
        except Exception:
            return False

    @classmethod
    def walk_repository(cls, repo_root: Path) -> Generator[Path, None, None]:
        """Walks repository and yields only analyzable source files."""
        for path in repo_root.rglob("*"):
            if not path.is_file():
                continue

            # Check if any parent directory is in IGNORED_DIRS
            rel_parts = path.relative_to(repo_root).parts
            if any(part in IGNORED_DIRS for part in rel_parts[:-1]):
                continue

            if cls.is_text_source_file(path):
                yield path

    @classmethod
    def index_all(cls, repo_root: Path) -> list[Path]:
        return list(cls.walk_repository(repo_root))
