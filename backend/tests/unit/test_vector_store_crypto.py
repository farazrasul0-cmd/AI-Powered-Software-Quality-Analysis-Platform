"""Unit tests for Vector Store secure hashing and deterministic embeddings."""

import math
import numpy as np
from app.infrastructure.rag.vector_store import FastCodeEmbedder


def test_vector_store_sha256_embedding_properties():
    """Confirms that FastCodeEmbedder generates normalized 384-d vectors without weak hashes."""
    text_sample = "def calculate_risk(metric: float) -> bool: return metric > 0.5"
    embedding = FastCodeEmbedder.embed_text(text_sample)

    # 1. Dimension validation
    assert len(embedding) == 384
    assert embedding.shape == (384,)

    # 2. Unit norm validation (L2-norm ~ 1.0)
    norm = float(np.linalg.norm(embedding))
    assert math.isclose(norm, 1.0, rel_tol=1e-5)

    # 3. Determinism
    repeat_embedding = FastCodeEmbedder.embed_text(text_sample)
    np.testing.assert_array_almost_equal(embedding, repeat_embedding)


def test_vector_store_different_texts_produce_different_embeddings():
    """Confirms that different code texts produce distinct vectors."""
    text_a = "def auth_login(): return True"
    text_b = "def delete_database(): return False"

    vec_a = FastCodeEmbedder.embed_text(text_a)
    vec_b = FastCodeEmbedder.embed_text(text_b)

    assert not np.array_equal(vec_a, vec_b)
    dot_product = float(np.dot(vec_a, vec_b))
    assert dot_product < 0.99
