"""Unit tests for Git Unified Diff Parser."""

from app.infrastructure.git.diff_parser import GitDiffParser

SAMPLE_DIFF = """diff --git a/app/auth.py b/app/auth.py
index 83a21..94b32 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -10,6 +10,8 @@ def authenticate_user(username, password):
     user = db.query(username)
     if not user:
         return False
+    if not verify_password(password, user.password_hash):
+        return False
     return user
diff --git a/app/new_feature.py b/app/new_feature.py
new file mode 100644
--- /dev/null
+++ b/app/new_feature.py
@@ -0,0 +1,5 @@
+def new_func():
+    print("Hello from new feature")
+    return True
"""


def test_parse_multi_file_diff():
    file_diffs = GitDiffParser.parse_diff(SAMPLE_DIFF)
    assert len(file_diffs) == 2

    # File 1: Modified auth.py
    diff1 = file_diffs[0]
    assert diff1.old_path == "app/auth.py"
    assert diff1.new_path == "app/auth.py"
    assert diff1.is_modified is True
    assert diff1.is_new is False
    assert len(diff1.hunks) == 1
    assert diff1.total_added_lines == 2
    assert diff1.total_deleted_lines == 0

    # File 2: New file new_feature.py
    diff2 = file_diffs[1]
    assert diff2.old_path is None
    assert diff2.new_path == "app/new_feature.py"
    assert diff2.is_new is True
    assert diff2.is_modified is False
    assert len(diff2.hunks) == 1
    assert diff2.total_added_lines == 3


def test_empty_diff():
    assert GitDiffParser.parse_diff("") == []
    assert GitDiffParser.parse_diff("   ") == []
