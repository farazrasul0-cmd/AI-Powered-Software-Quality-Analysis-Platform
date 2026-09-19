"""Unit tests for Vector Database and RAG Context Retrieval."""

import pytest

from app.infrastructure.rag.chunker import CodeChunk
from app.infrastructure.rag.retriever import ContextRetriever
from app.infrastructure.rag.vector_store import FastCodeEmbedder, InMemoryVectorStore


def test_fast_code_embedder_dimension_and_normalization():
    """Verifies that the embedding generator produces normalized 384-dimensional vectors."""
    v1 = FastCodeEmbedder.embed_text("def authenticate_user(token: str) -> bool:")
    v2 = FastCodeEmbedder.embed_text("class PaymentGatewayClient:")

    assert len(v1) == 384
    assert len(v2) == 384

    # Norm should be approximately 1.0
    import numpy as np

    assert np.isclose(np.linalg.norm(v1), 1.0, atol=1e-4)
    assert np.isclose(np.linalg.norm(v2), 1.0, atol=1e-4)


@pytest.mark.asyncio
async def test_in_memory_vector_store_indexing_and_search():
    """Verifies indexing and hybrid semantic/lexical search in the in-memory vector store."""
    store = InMemoryVectorStore()

    chunk1 = CodeChunk(
        chunk_id="chk-1",
        file_path="src/auth/jwt.py",
        language="python",
        symbol_name="verify_jwt_signature",
        symbol_type="FUNCTION",
        scope_path=["verify_jwt_signature"],
        start_line=10,
        end_line=25,
        content="def verify_jwt_signature(token, secret):\n    return jwt.decode(token, secret)",
        docstring="Decodes and validates token signature",
        imported_symbols=["jwt"],
    )

    chunk2 = CodeChunk(
        chunk_id="chk-2",
        file_path="src/database/queries.py",
        language="python",
        symbol_name="fetch_all_orders",
        symbol_type="FUNCTION",
        scope_path=["fetch_all_orders"],
        start_line=1,
        end_line=15,
        content="def fetch_all_orders(db):\n    return db.query(Order).all()",
        docstring="Retrieves orders list",
        imported_symbols=["sqlalchemy"],
    )

    indexed_count = await store.index_chunks("repo-123", [chunk1, chunk2])
    assert indexed_count == 2

    # Query 1: Semantic match for authentication
    results = await store.search("repo-123", query="validate authentication token", limit=2)
    assert len(results) > 0
    assert results[0].chunk.symbol_name == "verify_jwt_signature"
    assert results[0].score > 0.3

    # Query 2: Exact symbol filter
    filtered = await store.search(
        "repo-123", query="database", limit=2, symbol_filter="fetch_all_orders"
    )
    assert len(filtered) == 1
    assert filtered[0].chunk.symbol_name == "fetch_all_orders"

    # Repository isolation
    isolated = await store.search("repo-different", query="token", limit=2)
    assert len(isolated) == 0

    # Purge
    await store.delete_repository("repo-123")
    empty_results = await store.search("repo-123", query="token", limit=2)
    assert len(empty_results) == 0


@pytest.mark.asyncio
async def test_context_retriever_for_code_chunk():
    """Verifies that ContextRetriever retrieves external symbol dependencies."""
    store = InMemoryVectorStore()
    retriever = ContextRetriever(store)

    auth_util = CodeChunk(
        chunk_id="dep-1",
        file_path="src/utils/crypto.py",
        language="python",
        symbol_name="crypto.hash_password",
        symbol_type="FUNCTION",
        scope_path=["hash_password"],
        start_line=1,
        end_line=10,
        content="def hash_password(pw: str) -> str: return bcrypt.hash(pw)",
    )
    await store.index_chunks("repo-xyz", [auth_util])

    caller_chunk = CodeChunk(
        chunk_id="caller-1",
        file_path="src/api/auth.py",
        language="python",
        symbol_name="login",
        symbol_type="FUNCTION",
        scope_path=["login"],
        start_line=20,
        end_line=40,
        content="def login(req): hash_password(req.password)",
        imported_symbols=["crypto.hash_password"],
    )

    related = await retriever.retrieve_context_for_chunk("repo-xyz", caller_chunk, limit=2)
    assert len(related) >= 1
    assert related[0].symbol_name == "crypto.hash_password"

    prompt_text = retriever.format_context_for_prompt(related)
    assert "crypto.hash_password" in prompt_text
    assert "bcrypt.hash" in prompt_text
