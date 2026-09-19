"""Language and project structure detector."""

from pathlib import Path

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".md": "Markdown",
}

PROJECT_SIGNATURES: dict[str, list[str]] = {
    "FastAPI": ["fastapi", "from fastapi import", "import fastapi"],
    "Django": ["manage.py", "django", "from django import"],
    "Flask": ["flask", "from flask import", "Flask(__name__)"],
    "React": ["react", "react-dom", "import React"],
    "Next.js": ["next.config.js", "next.config.mjs", "next.config.ts"],
    "Express": ["express", "require('express')", "from 'express'"],
    "Rust Cargo": ["Cargo.toml"],
    "Go Module": ["go.mod"],
    "Java Maven": ["pom.xml"],
    "Java Gradle": ["build.gradle", "build.gradle.kts"],
}


class LanguageDetector:
    @staticmethod
    def detect_languages(repo_path: Path) -> tuple[str | None, dict[str, int]]:
        """Scans indexed files and tallies line counts per language."""
        counts: dict[str, int] = {}

        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue

            parts = file_path.parts
            if any(
                p.startswith(".") or p in {"node_modules", "vendor", "dist", "build"} for p in parts
            ):
                continue

            ext = file_path.suffix.lower()
            lang = EXTENSION_LANGUAGE_MAP.get(ext)
            if lang and lang not in {"JSON", "YAML", "TOML", "Markdown"}:
                try:
                    line_count = sum(
                        1
                        for line in file_path.open(encoding="utf-8", errors="ignore")
                        if line.strip()
                    )
                    counts[lang] = counts.get(lang, 0) + line_count
                except Exception:
                    pass

        if not counts:
            return None, {}

        primary_language = max(counts.items(), key=lambda x: x[1])[0]
        return primary_language, counts

    @staticmethod
    def detect_project_type(repo_path: Path) -> list[str]:
        """Detects high-level frameworks and project types present in the repository."""
        detected_types: list[str] = []

        # Check file presence
        file_names = {f.name.lower() for f in repo_path.glob("*") if f.is_file()}

        if "cargo.toml" in file_names:
            detected_types.append("Rust Cargo")
        if "go.mod" in file_names:
            detected_types.append("Go Module")
        if "pom.xml" in file_names:
            detected_types.append("Java Maven")
        if "build.gradle" in file_names or "build.gradle.kts" in file_names:
            detected_types.append("Java Gradle")
        if "manage.py" in file_names:
            detected_types.append("Django")

        # Check requirements or package.json
        req_file = repo_path / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text(encoding="utf-8", errors="ignore").lower()
                if "fastapi" in content and "FastAPI" not in detected_types:
                    detected_types.append("FastAPI")
                if "flask" in content and "Flask" not in detected_types:
                    detected_types.append("Flask")
                if "django" in content and "Django" not in detected_types:
                    detected_types.append("Django")
            except Exception:
                pass

        pkg_json = repo_path / "package.json"
        if pkg_json.exists():
            try:
                content = pkg_json.read_text(encoding="utf-8", errors="ignore").lower()
                if "next" in content:
                    detected_types.append("Next.js")
                elif "react" in content:
                    detected_types.append("React")
                if "express" in content:
                    detected_types.append("Express")
            except Exception:
                pass

        return detected_types or ["Generic Software Project"]
