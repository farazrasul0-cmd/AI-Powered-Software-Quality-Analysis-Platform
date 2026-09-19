"""Secure Git Cloner with SSRF guards, shallow depth, disk quota, and ephemeral cleanup."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.core.security import is_safe_repository_url


class GitCloneError(Exception):
    pass


class GitCloner:
    def __init__(self, temp_base_dir: str | None = None) -> None:
        self.base_dir = temp_base_dir or settings.TEMP_STORAGE_PATH
        os.makedirs(self.base_dir, exist_ok=True)

    def clone_repository(
        self,
        repo_url: str,
        branch: str = "main",
        timeout_seconds: int | None = None,
    ) -> Path:
        """Securely clones a repository using a shallow clone (depth 1) into a temporary directory."""
        timeout = timeout_seconds or settings.GIT_CLONE_TIMEOUT_SECONDS

        # 1. SSRF Validation
        is_safe, reason = is_safe_repository_url(repo_url)
        if not is_safe:
            raise GitCloneError(f"Security validation failed for URL '{repo_url}': {reason}")

        # 2. Create isolated ephemeral directory
        target_dir = Path(tempfile.mkdtemp(prefix="repo_", dir=self.base_dir))

        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            "--single-branch",
            "--branch",
            branch,
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.symlinks=false",
            repo_url,
            str(target_dir),
        ]

        logger.info(f"Cloning {repo_url} (branch: {branch}) into {target_dir}...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            if result.returncode != 0:
                # If branch failed, attempt cloning default HEAD
                if "Remote branch" in result.stderr and "not found" in result.stderr:
                    logger.warning(f"Branch {branch} not found. Attempting default branch clone...")
                    fallback_cmd = [
                        "git",
                        "clone",
                        "--depth",
                        "1",
                        "-c",
                        "core.hooksPath=/dev/null",
                        "-c",
                        "core.symlinks=false",
                        repo_url,
                        str(target_dir),
                    ]
                    fallback_res = subprocess.run(
                        fallback_cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )
                    if fallback_res.returncode != 0:
                        raise GitCloneError(f"Git clone failed: {fallback_res.stderr.strip()}")
                else:
                    raise GitCloneError(f"Git clone failed: {result.stderr.strip()}")

            # Check disk usage cap
            total_size_bytes = sum(f.stat().st_size for f in target_dir.glob("**/*") if f.is_file())
            max_size_bytes = settings.MAX_REPO_SIZE_MB * 1024 * 1024
            if total_size_bytes > max_size_bytes:
                self.cleanup(target_dir)
                raise GitCloneError(
                    f"Repository size ({total_size_bytes // (1024 * 1024)}MB) exceeds limit of {settings.MAX_REPO_SIZE_MB}MB"
                )

            return target_dir

        except subprocess.TimeoutExpired:
            self.cleanup(target_dir)
            raise GitCloneError(f"Git clone timed out after {timeout} seconds") from None
        except Exception as e:
            self.cleanup(target_dir)
            if not isinstance(e, GitCloneError):
                raise GitCloneError(f"Unexpected clone error: {str(e)}") from e
            raise

    @staticmethod
    def cleanup(dir_path: Path) -> None:
        """Safely removes an ephemeral clone directory, handling readonly git files."""
        if not dir_path or not dir_path.exists():
            return

        def _remove_readonly(func, path, _):
            import stat

            os.chmod(path, stat.S_IWRITE)
            func(path)

        try:
            shutil.rmtree(dir_path, onerror=_remove_readonly)
            logger.info(f"Cleaned up ephemeral repository directory {dir_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup directory {dir_path}: {e}")
