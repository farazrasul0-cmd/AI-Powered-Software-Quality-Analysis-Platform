"""Unit tests for Grammar-Aware Semantic AST Chunker."""

from app.infrastructure.rag.chunker import (
    PythonSemanticChunker,
    TypeScriptSemanticChunker,
    UnifiedSemanticChunker,
)


def test_python_semantic_chunking_classes_and_methods():
    """Verifies that Python AST chunker extracts class and method boundaries with signatures."""
    code = '''
"""Module docstring."""

import os
from math import sqrt

class PaymentProcessor:
    """Handles financial transactions."""

    def __init__(self, currency: str = "USD"):
        self.currency = currency

    def process(self, amount: float, account_id: str) -> bool:
        """Processes a single payment."""
        if amount <= 0:
            return False
        return True

def standalone_calculator(x: int, y: int) -> int:
    """Calculates sum."""
    return x + y
'''

    chunks = PythonSemanticChunker.chunk("src/billing/payment.py", code)

    # Should have: Class chunk, __init__ method, process method, and standalone_calculator
    symbols = {c.symbol_name: c for c in chunks}

    assert "PaymentProcessor" in symbols
    assert symbols["PaymentProcessor"].symbol_type == "CLASS"
    assert symbols["PaymentProcessor"].docstring == "Handles financial transactions."
    assert "os" in symbols["PaymentProcessor"].imported_symbols
    assert "math.sqrt" in symbols["PaymentProcessor"].imported_symbols

    assert "PaymentProcessor.process" in symbols
    assert symbols["PaymentProcessor.process"].symbol_type == "METHOD"
    assert "amount: float" in symbols["PaymentProcessor.process"].parameters
    assert "account_id: str" in symbols["PaymentProcessor.process"].parameters
    assert symbols["PaymentProcessor.process"].return_type == "bool"

    assert "standalone_calculator" in symbols
    assert symbols["standalone_calculator"].symbol_type == "FUNCTION"
    assert symbols["standalone_calculator"].return_type == "int"


def test_typescript_semantic_chunking():
    """Verifies that TypeScript chunker extracts interfaces, classes, and exported functions."""
    code = '''
import { useState, useEffect } from "react";
import axios from "axios";

export interface UserProfile {
  id: string;
  name: string;
}

export class UserService {
  async fetchUser(id: string): Promise<UserProfile> {
    return { id, name: "Alice" };
  }
}

export async function validateToken(token: string): Promise<boolean> {
  return token.length > 10;
}
'''

    chunks = TypeScriptSemanticChunker.chunk("src/services/user.ts", code)
    symbols = {c.symbol_name: c for c in chunks}

    assert "UserProfile" in symbols
    assert symbols["UserProfile"].symbol_type == "INTERFACE"

    assert "UserService" in symbols
    assert symbols["UserService"].symbol_type == "CLASS"

    assert "validateToken" in symbols
    assert symbols["validateToken"].symbol_type == "FUNCTION"

    # Verify imports captured
    assert "useState" in symbols["UserService"].imported_symbols
    assert "axios" in symbols["UserService"].imported_symbols


def test_unified_semantic_chunker_routing():
    """Verifies that UnifiedSemanticChunker routes correctly based on file extension."""
    py_chunks = UnifiedSemanticChunker.chunk_file(
        "api/app.py", "def main():\n    pass\n", language="python"
    )
    assert len(py_chunks) == 1
    assert py_chunks[0].language == "python"

    ts_chunks = UnifiedSemanticChunker.chunk_file(
        "web/index.ts", "export function hello() { return 'world'; }", language="typescript"
    )
    assert len(ts_chunks) == 1
    assert ts_chunks[0].language == "typescript"
