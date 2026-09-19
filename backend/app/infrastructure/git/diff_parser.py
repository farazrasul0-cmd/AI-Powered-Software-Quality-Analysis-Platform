"""Git Unified Diff Parser."""

import re

from app.domain.models import DiffHunk, FileDiff

HUNK_HEADER_REGEX = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class GitDiffParser:
    """Parses standard unified git diff text output into structured domain objects."""

    @classmethod
    def parse_diff(cls, diff_text: str) -> list[FileDiff]:
        if not diff_text or not diff_text.strip():
            return []

        file_diffs: list[FileDiff] = []
        current_old_path: str | None = None
        current_new_path: str | None = None
        current_hunks: list[DiffHunk] = []
        is_new = False
        is_deleted = False

        lines = diff_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]

            if line.startswith("diff --git "):
                # Finish previous file diff if present
                if current_new_path is not None:
                    file_diffs.append(
                        FileDiff(
                            old_path=current_old_path,
                            new_path=current_new_path,
                            is_new=is_new,
                            is_deleted=is_deleted,
                            is_modified=not (is_new or is_deleted),
                            hunks=current_hunks,
                        )
                    )
                # Reset for next file
                current_old_path = None
                current_new_path = None
                current_hunks = []
                is_new = False
                is_deleted = False
                i += 1
                continue

            if line.startswith("new file mode "):
                is_new = True
                i += 1
                continue

            if line.startswith("deleted file mode "):
                is_deleted = True
                i += 1
                continue

            if line.startswith("--- a/"):
                current_old_path = line[6:]
                i += 1
                continue
            elif line.startswith("--- /dev/null"):
                current_old_path = None
                is_new = True
                i += 1
                continue

            if line.startswith("+++ b/"):
                current_new_path = line[6:]
                i += 1
                continue
            elif line.startswith("+++ /dev/null"):
                current_new_path = current_old_path or "deleted"
                is_deleted = True
                i += 1
                continue

            # Hunk header
            match = HUNK_HEADER_REGEX.match(line)
            if match:
                old_start = int(match.group(1))
                old_lines = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_lines = int(match.group(4)) if match.group(4) else 1

                added: list[int] = []
                deleted: list[int] = []

                curr_new_line = new_start
                curr_old_line = old_start

                i += 1
                while i < len(lines) and not lines[i].startswith(("diff --git ", "@@ ")):
                    hunk_line = lines[i]
                    if hunk_line.startswith("+"):
                        added.append(curr_new_line)
                        curr_new_line += 1
                    elif hunk_line.startswith("-"):
                        deleted.append(curr_old_line)
                        curr_old_line += 1
                    elif hunk_line.startswith(" "):
                        curr_new_line += 1
                        curr_old_line += 1
                    i += 1

                current_hunks.append(
                    DiffHunk(
                        old_start=old_start,
                        old_lines=old_lines,
                        new_start=new_start,
                        new_lines=new_lines,
                        added_lines=added,
                        deleted_lines=deleted,
                    )
                )
                continue

            i += 1

        # Append last file diff
        if current_new_path is not None:
            file_diffs.append(
                FileDiff(
                    old_path=current_old_path,
                    new_path=current_new_path,
                    is_new=is_new,
                    is_deleted=is_deleted,
                    is_modified=not (is_new or is_deleted),
                    hunks=current_hunks,
                )
            )

        return file_diffs
