"""Curated Ground-Truth Benchmark Corpus for RQ1-RQ3 Experiments."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GroundTruthFinding:
    rule_id: str
    category: str
    severity: str
    line: int
    is_genuine_defect: bool
    is_test_fixture_false_positive: bool = False


@dataclass
class BenchmarkSample:
    sample_id: str
    file_path: str
    sloc: int
    code_content: str
    expected_defect: bool
    ground_truth_findings: list[GroundTruthFinding] = field(default_factory=list)
    true_defects_count: int = 0
    benign_alerts_count: int = 0


BENCHMARK_CORPUS: list[BenchmarkSample] = [
    # 1. Critical Security Flaws (Genuine Bugs)
    BenchmarkSample(
        sample_id="SEC_01_SQLI_CMD",
        file_path="src/gateway/query_handler.py",
        sloc=45,
        code_content="""import os
import sqlite3

def search_records(user_query: str):
    conn = sqlite3.connect("app.db")
    # CWE-89: Direct SQL concatenation
    query = f"SELECT * FROM accounts WHERE username = '{user_query}'"
    return conn.cursor().execute(query).fetchall()

def run_diagnostic(host: str):
    # CWE-78: Command Injection via os.system
    os.system(f"ping -c 1 {host}")
""",
        expected_defect=True,
        ground_truth_findings=[
            GroundTruthFinding(
                rule_id="SEC-SQLI",
                category="SECURITY",
                severity="CRITICAL",
                line=8,
                is_genuine_defect=True,
            ),
            GroundTruthFinding(
                rule_id="SEC-CMD-INJ",
                category="SECURITY",
                severity="CRITICAL",
                line=13,
                is_genuine_defect=True,
            ),
        ],
        true_defects_count=2,
        benign_alerts_count=0,
    ),

    # 2. Maintainability & Extreme Complexity (Genuine Smells)
    BenchmarkSample(
        sample_id="MAINT_01_DEEP_NESTING",
        file_path="src/legacy/parser_engine.py",
        sloc=120,
        code_content="""def process_matrix(data, flags, mode, threshold, max_iters, logger, cache):
    # Deep nesting and cognitive complexity > 18
    results = []
    if data is not None:
        for row in data:
            if row.is_valid():
                for cell in row.cells:
                    if cell.value > threshold:
                        if mode == "AGGRESSIVE":
                            for k in range(max_iters):
                                if flags.get("turbo"):
                                    results.append(cell.value * 2)
                                else:
                                    results.append(cell.value)
                        elif mode == "CONSERVATIVE":
                            results.append(cell.value // 2)
    return results
""",
        expected_defect=True,
        ground_truth_findings=[
            GroundTruthFinding(
                rule_id="SMELL-DEEP-NESTING",
                category="CODE_SMELL",
                severity="HIGH",
                line=8,
                is_genuine_defect=True,
            ),
            GroundTruthFinding(
                rule_id="SMELL-PARAMETER-BLOAT",
                category="CODE_SMELL",
                severity="MEDIUM",
                line=1,
                is_genuine_defect=True,
            ),
        ],
        true_defects_count=2,
        benign_alerts_count=0,
    ),

    # 3. Test Fixture with Mock Password (False Alarm Candidate for RQ3)
    BenchmarkSample(
        sample_id="FP_01_TEST_MOCK_AUTH",
        file_path="tests/fixtures/mock_credentials.py",
        sloc=35,
        code_content="""import unittest

class MockAuthTest(unittest.TestCase):
    def setUp(self):
        # Benign test fixture string triggers pattern-based scanner
        self.mock_user = "test_user_qa"
        self.mock_password = "dummy_password_secret_123"
        self.mock_api_token = "mock-bearer-token-xyz"

    def test_auth_dummy(self):
        self.assertEqual(len(self.mock_password), 24)
""",
        expected_defect=False,
        ground_truth_findings=[
            GroundTruthFinding(
                rule_id="SEC-PWD-HARDCODED",
                category="SECURITY",
                severity="HIGH",
                line=7,
                is_genuine_defect=False,
                is_test_fixture_false_positive=True,
            ),
        ],
        true_defects_count=0,
        benign_alerts_count=1,
    ),

    # 4. Clean Idiomatic High-Quality Module (Defect Free)
    BenchmarkSample(
        sample_id="CLEAN_01_MATH_UTILS",
        file_path="src/utils/math_utils.py",
        sloc=30,
        code_content="""from typing import Sequence

def compute_mean(values: Sequence[float]) -> float:
    \"\"\"Computes the arithmetic mean of a sequence.\"\"\"
    if not values:
        return 0.0
    return sum(values) / len(values)

def clamp(val: float, min_val: float, max_val: float) -> float:
    \"\"\"Clamps value within [min_val, max_val] interval.\"\"\"
    return max(min_val, min(val, max_val))
""",
        expected_defect=False,
        ground_truth_findings=[],
        true_defects_count=0,
        benign_alerts_count=0,
    ),

    # 5. Defect-Prone High-Risk Module (Subtle Logic/Resource Leak)
    BenchmarkSample(
        sample_id="DEFECT_01_UNCLOSED_SOCKET",
        file_path="src/network/client_stream.py",
        sloc=70,
        code_content="""import socket

def stream_logs(server_ip: str, port: int, payload: bytes):
    # Resource leak: socket created but never closed in error cases
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, port))
    s.sendall(payload)
    data = s.recv(1024)
    # Missing try/finally s.close()
    return data
""",
        expected_defect=True,
        ground_truth_findings=[
            GroundTruthFinding(
                rule_id="BUG-RESOURCE-LEAK",
                category="BUG_RISK",
                severity="HIGH",
                line=5,
                is_genuine_defect=True,
            )
        ],
        true_defects_count=1,
        benign_alerts_count=0,
    ),
]
