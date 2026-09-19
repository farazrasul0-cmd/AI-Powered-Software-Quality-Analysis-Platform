"""AST-Based Security Pattern Scanner (CWE Vulnerability Rules)."""

import ast
import re

from app.domain.enums import FindingCategory, FindingSeverity
from app.infrastructure.db.models.issue import Issue

# Regex for detecting potential hardcoded credentials in assignments
SECRET_KEYWORD_REGEX = re.compile(
    r"(?i)\b(api_key|apikey|secret|password|passwd|auth_token|access_token|private_key)\b"
)
DUMMY_VALUE_REGEX = re.compile(
    r"(?i)^(none|null|dummy|test|example|default|true|false|changeme|\$\{.+\}|\{.*\}|)$"
)


class SecurityScanner:
    """Scans Python AST for Common Weakness Enumeration (CWE) security vulnerabilities."""

    @classmethod
    def scan_file(cls, file_path: str, code_str: str, tree: ast.AST) -> list[Issue]:
        issues: list[Issue] = []

        for node in ast.walk(tree):
            # 1. SQL Injection (CWE-89)
            cls._check_sqli(file_path, node, issues)

            # 2. Hardcoded Secrets (CWE-798)
            cls._check_hardcoded_secrets(file_path, node, issues)

            # 3. Insecure Deserialization (CWE-502)
            cls._check_insecure_deserialization(file_path, node, issues)

            # 4. OS Command Injection (CWE-78)
            cls._check_command_injection(file_path, node, issues)

            # 5. Broken / Weak Cryptography (CWE-327)
            cls._check_weak_crypto(file_path, node, issues)

        return issues

    @classmethod
    def _check_sqli(cls, file_path: str, node: ast.AST, issues: list[Issue]) -> None:
        """Detects raw string formatting or f-strings passed into database execute methods."""
        if not isinstance(node, ast.Call):
            return

        # Check for .execute(...) or .raw(...) calls
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id

        if func_name in {"execute", "executemany", "raw_sql", "raw"}:
            if node.args:
                first_arg = node.args[0]
                # Check if formatted string or binary op % / +
                is_tainted = False
                if isinstance(first_arg, ast.JoinedStr):  # f-string
                    is_tainted = True
                elif isinstance(first_arg, ast.BinOp) and isinstance(
                    first_arg.op, (ast.Add, ast.Mod)
                ):
                    is_tainted = True
                elif isinstance(first_arg, ast.Call):
                    # string.format(...)
                    if (
                        isinstance(first_arg.func, ast.Attribute)
                        and first_arg.func.attr == "format"
                    ):
                        is_tainted = True

                if is_tainted:
                    issues.append(
                        Issue(
                            report_id="",
                            rule_id="SEC-CWE-89-SQLI",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.CRITICAL,
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=getattr(node, "end_lineno", node.lineno),
                            title="SQL Injection Risk Detected (CWE-89)",
                            description="Direct dynamic string formatting or interpolation detected inside SQL execute call.",
                            snippet=f".{func_name}(...)",
                            remediation="Use parameterized queries with prepared statements (e.g. `cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))`).",
                            cwe_id="CWE-89",
                        )
                    )

    @classmethod
    def _check_hardcoded_secrets(cls, file_path: str, node: ast.AST, issues: list[Issue]) -> None:
        """Detects assignment of literal non-trivial strings to sensitive variable names."""
        if isinstance(node, ast.Assign):
            for target in node.targets:
                var_name = ""
                if isinstance(target, ast.Name):
                    var_name = target.id
                elif isinstance(target, ast.Attribute):
                    var_name = target.attr

                if var_name and SECRET_KEYWORD_REGEX.search(var_name):
                    # Check if assigned value is a literal non-empty string
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        val = node.value.value.strip()
                        if len(val) >= 6 and not DUMMY_VALUE_REGEX.match(val):
                            issues.append(
                                Issue(
                                    report_id="",
                                    rule_id="SEC-CWE-798-SECRET",
                                    category=FindingCategory.SECURITY,
                                    severity=FindingSeverity.CRITICAL,
                                    file_path=file_path,
                                    line_start=node.lineno,
                                    line_end=node.lineno,
                                    title="Hardcoded Credential or Token Detected (CWE-798)",
                                    description=f"Variable '{var_name}' appears to be assigned a hardcoded plaintext secret.",
                                    snippet=f"{var_name} = '***'",
                                    remediation="Store secrets in external environment variables or a secrets manager (e.g. AWS Secrets Manager, HashiCorp Vault).",
                                    cwe_id="CWE-798",
                                )
                            )

    @classmethod
    def _check_insecure_deserialization(
        cls, file_path: str, node: ast.AST, issues: list[Issue]
    ) -> None:
        """Detects unsafe deserialization via pickle or pyyaml without SafeLoader."""
        if not isinstance(node, ast.Call):
            return

        # pickle.loads() or pickle.load()
        if isinstance(node.func, ast.Attribute):
            mod_name = getattr(node.func.value, "id", "")
            method_name = node.func.attr

            if mod_name == "pickle" and method_name in {"load", "loads"}:
                issues.append(
                    Issue(
                        report_id="",
                        rule_id="SEC-CWE-502-PICKLE",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.HIGH,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        title="Insecure Deserialization via pickle (CWE-502)",
                        description="Unpickling untrusted data can lead to arbitrary remote code execution (RCE).",
                        snippet=f"pickle.{method_name}(...)",
                        remediation="Use secure serialization formats like JSON, Protocol Buffers, or HMAC-signed tokens.",
                        cwe_id="CWE-502",
                    )
                )

            # yaml.load without SafeLoader
            elif mod_name == "yaml" and method_name == "load":
                has_safe_loader = False
                for kw in node.keywords:
                    if kw.arg == "Loader":
                        if isinstance(kw.value, ast.Attribute) and "Safe" in kw.value.attr:
                            has_safe_loader = True
                        elif isinstance(kw.value, ast.Name) and "Safe" in kw.value.id:
                            has_safe_loader = True

                if not has_safe_loader:
                    issues.append(
                        Issue(
                            report_id="",
                            rule_id="SEC-CWE-502-YAML",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.HIGH,
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            title="Insecure YAML Deserialization (CWE-502)",
                            description="Using `yaml.load()` without specifying `SafeLoader` allows arbitrary Python object instantiation.",
                            snippet="yaml.load(...)",
                            remediation="Replace with `yaml.safe_load(...)`.",
                            cwe_id="CWE-502",
                        )
                    )

    @classmethod
    def _check_command_injection(cls, file_path: str, node: ast.AST, issues: list[Issue]) -> None:
        """Detects subprocess execution with shell=True or os.system."""
        if not isinstance(node, ast.Call):
            return

        if isinstance(node.func, ast.Attribute):
            mod_name = getattr(node.func.value, "id", "")
            attr_name = node.func.attr

            # os.system(cmd) or os.popen(cmd)
            if mod_name == "os" and attr_name in {"system", "popen"}:
                issues.append(
                    Issue(
                        report_id="",
                        rule_id="SEC-CWE-78-OS-SYSTEM",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.HIGH,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        title="Command Injection Risk via os.system (CWE-78)",
                        description="`os.system()` executes commands directly in a subshell, leaving applications vulnerable to command injection.",
                        snippet=f"os.{attr_name}(...)",
                        remediation="Use `subprocess.run([...], shell=False)` with arguments passed as an explicit list.",
                        cwe_id="CWE-78",
                    )
                )

            # subprocess.Popen(..., shell=True)
            elif mod_name == "subprocess" and attr_name in {
                "Popen",
                "run",
                "call",
                "check_call",
                "check_output",
            }:
                for kw in node.keywords:
                    if (
                        kw.arg == "shell"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value is True
                    ):
                        issues.append(
                            Issue(
                                report_id="",
                                rule_id="SEC-CWE-78-SHELL-TRUE",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.HIGH,
                                file_path=file_path,
                                line_start=node.lineno,
                                line_end=node.lineno,
                                title="Subprocess with shell=True (CWE-78)",
                                description="Running subprocesses with `shell=True` passes input through the system shell, enabling command injection if arguments are unquoted.",
                                snippet=f"subprocess.{attr_name}(..., shell=True)",
                                remediation="Set `shell=False` and pass arguments as a list of strings.",
                                cwe_id="CWE-78",
                            )
                        )

    @classmethod
    def _check_weak_crypto(cls, file_path: str, node: ast.AST, issues: list[Issue]) -> None:
        """Detects usage of weak or broken hash algorithms (MD5, SHA1)."""
        if not isinstance(node, ast.Call):
            return

        if isinstance(node.func, ast.Attribute):
            mod_name = getattr(node.func.value, "id", "")
            attr_name = node.func.attr

            if mod_name == "hashlib" and attr_name.lower() in {"md5", "sha1"}:
                issues.append(
                    Issue(
                        report_id="",
                        rule_id="SEC-CWE-327-WEAK-HASH",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.MEDIUM,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        title=f"Weak Cryptographic Hash '{attr_name.upper()}' (CWE-327)",
                        description=f"`hashlib.{attr_name}()` is cryptographically broken and vulnerable to collision attacks.",
                        snippet=f"hashlib.{attr_name}()",
                        remediation="Use secure collision-resistant algorithms such as SHA-256 (`hashlib.sha256()`) or SHA-3.",
                        cwe_id="CWE-327",
                    )
                )
