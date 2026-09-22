"""Git Unified Diff Parser."""

import re

from app.domain.models import DiffHunk, FileDiff

HUNK_HEADER_REGEX = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _parse_hunk(
    header_match: re.Match, lines: list[str], start_idx: int
) -> tuple[DiffHunk, int]:
    """Parses a single diff hunk from its header line through its content lines."""
    old_start = int(header_match.group(1))
    old_lines = int(header_match.group(2)) if header_match.group(2) else 1
    new_start = int(header_match.group(3))
    new_lines = int(header_match.group(4)) if header_match.group(4) else 1

    added: list[int] = []
    deleted: list[int] = []
    curr_new_line = new_start
    curr_old_line = old_start

    idx = start_idx + 1
    while idx < len(lines) and not lines[idx].startswith(("diff --git ", "@@ ")):
        hunk_line = lines[idx]
        if hunk_line.startswith("+"):
            added.append(curr_new_line)
            curr_new_line += 1
        elif hunk_line.startswith("-"):
            deleted.append(curr_old_line)
            curr_old_line += 1
        elif hunk_line.startswith(" "):
            curr_new_line += 1
            curr_old_line += 1
        idx += 1

    hunk = DiffHunk(
        old_start=old_start,
        old_lines=old_lines,
        new_start=new_start,
        new_lines=new_lines,
        added_lines=added,
        deleted_lines=deleted,
    )
    return hunk, idx


def _create_file_diff(
    old_path: str | None,
    new_path: str,
    is_new: bool,
    is_deleted: bool,
    hunks: list[DiffHunk],
) -> FileDiff:
    """Builds a typed FileDiff entity."""
    return FileDiff(
        old_path=old_path,
        new_path=new_path,
        is_new=is_new,
        is_deleted=is_deleted,
        is_modified=not (is_new or is_deleted),
        hunks=hunks,
    )


class GitDiffParser:
    """Parses standard unified git diff text output into structured domain objects."""

    @classmethod
    def parse_diff(cls, diff_text: str) -> list[FileDiff]:
        if not diff_text or not diff_text.strip():
            return []

        file_diffs: list[FileDiff] = []
        old_path: str | None = None
        new_path: str | None = None
        hunks: list[DiffHunk] = []
        is_new = False
        is_deleted = False

        lines = diff_text.splitlines()
        idx = 0

        while idx < len(lines):
            line = lines[idx]

            if line.startswith("diff --git "):
                if new_path is not None:
                    file_diffs.append(_create_file_diff(old_path, new_path, is_new, is_deleted, hunks))
                old_path, new_path, hunks = None, None, []
                is_new, is_deleted = False, False
                idx += 1
            elif line.startswith("new file mode "):
                is_new = True
                idx += 1
            elif line.startswith("deleted file mode "):
                is_deleted = True
                idx += 1
            elif line.startswith("--- a/"):
                old_path = line[6:]
                idx += 1
            elif line.startswith("--- /dev/null"):
                old_path, is_new = None, True
                idx += 1
            elif line.startswith("+++ b/"):
                new_path = line[6:]
                idx += 1
            elif line.startswith("+++ /dev/null"):
                new_path = old_path or "deleted"
                is_deleted = True
                idx += 1
            else:
                match = HUNK_HEADER_REGEX.match(line)
                if match:
                    hunk, idx = _parse_hunk(match, lines, idx)
                    hunks.append(hunk)
                else:
                    idx += 1

        if new_path is not None:
            file_diffs.append(_create_file_diff(old_path, new_path, is_new, is_deleted, hunks))

        return file_diffs
