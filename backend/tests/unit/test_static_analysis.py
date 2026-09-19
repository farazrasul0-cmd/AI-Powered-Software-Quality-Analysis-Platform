"""Unit tests and benchmarks for Static Analysis Engine."""

from pathlib import Path

from app.domain.enums import FindingCategory, FindingSeverity
from app.infrastructure.static_analysis.debt import TechnicalDebtEstimator
from app.infrastructure.static_analysis.engine import StaticAnalysisEngine

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "fixtures" / "static_samples"


def test_clean_control_code_zero_false_positives():
    clean_file = FIXTURES_DIR / "clean_control.py"
    content = clean_file.read_text(encoding="utf-8")

    result = StaticAnalysisEngine.analyze_python_file(str(clean_file), content)
    assert len(result.issues) == 0, f"Expected 0 issues on clean control, got: {result.issues}"
    assert result.metric.maintainability_index >= 75.0
    assert result.complexity_report.max_cyclomatic_complexity <= 3


def test_sql_injection_detection():
    sqli_file = FIXTURES_DIR / "sec_sqli.py"
    content = sqli_file.read_text(encoding="utf-8")

    result = StaticAnalysisEngine.analyze_python_file(str(sqli_file), content)
    sqli_issues = [i for i in result.issues if i.cwe_id == "CWE-89"]
    assert len(sqli_issues) == 1
    assert sqli_issues[0].severity == FindingSeverity.CRITICAL
    assert sqli_issues[0].category == FindingCategory.SECURITY
    assert "SQL Injection" in sqli_issues[0].title


def test_hardcoded_secrets_detection():
    secret_file = FIXTURES_DIR / "sec_hardcoded_secrets.py"
    content = secret_file.read_text(encoding="utf-8")

    result = StaticAnalysisEngine.analyze_python_file(str(secret_file), content)
    secret_issues = [i for i in result.issues if i.cwe_id == "CWE-798"]
    assert len(secret_issues) >= 1
    assert secret_issues[0].severity == FindingSeverity.CRITICAL


def test_insecure_deserialization_detection():
    pickle_file = FIXTURES_DIR / "sec_insecure_deserialization.py"
    content = pickle_file.read_text(encoding="utf-8")

    result = StaticAnalysisEngine.analyze_python_file(str(pickle_file), content)
    pickle_issues = [i for i in result.issues if i.cwe_id == "CWE-502"]
    assert len(pickle_issues) == 1
    assert pickle_issues[0].severity == FindingSeverity.HIGH


def test_command_injection_detection():
    cmd_file = FIXTURES_DIR / "sec_command_injection.py"
    content = cmd_file.read_text(encoding="utf-8")

    result = StaticAnalysisEngine.analyze_python_file(str(cmd_file), content)
    cmd_issues = [i for i in result.issues if i.cwe_id == "CWE-78"]
    assert len(cmd_issues) == 1
    assert cmd_issues[0].severity == FindingSeverity.HIGH


def test_weak_cryptography_detection():
    crypto_file = FIXTURES_DIR / "sec_weak_crypto.py"
    content = crypto_file.read_text(encoding="utf-8")

    result = StaticAnalysisEngine.analyze_python_file(str(crypto_file), content)
    crypto_issues = [i for i in result.issues if i.cwe_id == "CWE-327"]
    assert len(crypto_issues) == 1
    assert crypto_issues[0].severity == FindingSeverity.MEDIUM


def test_maintainability_smells_detection():
    smell_file = FIXTURES_DIR / "smell_maintainability.py"
    content = smell_file.read_text(encoding="utf-8")

    result = StaticAnalysisEngine.analyze_python_file(str(smell_file), content)
    rule_ids = {i.rule_id for i in result.issues}
    assert "SMELL-DEEP-NESTING" in rule_ids
    assert "SMELL-UNREACHABLE-CODE" in rule_ids
    assert "SMELL-TOO-MANY-PARAMS" in rule_ids


def test_technical_debt_calculation():
    smell_file = FIXTURES_DIR / "smell_maintainability.py"
    content = smell_file.read_text(encoding="utf-8")

    result = StaticAnalysisEngine.analyze_python_file(str(smell_file), content)
    debt = TechnicalDebtEstimator.calculate_total_debt(result.issues)
    assert debt.total_minutes > 0
    assert debt.total_hours > 0.0
    assert "CODE_SMELL" in debt.by_category
