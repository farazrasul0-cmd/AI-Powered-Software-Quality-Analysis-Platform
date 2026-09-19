"""Vector Database and Semantic Indexing Subsystem.

Provides hybrid dense semantic and sparse BM25 symbol retrieval over
grammar-aware code chunks with Qdrant and in-memory dual-mode support.
"""

import hashlib
import math
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np

from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.rag.chunker import CodeChunk


@dataclass
class SearchResult:
    """Represents a retrieved code chunk with similarity ranking."""

    chunk: CodeChunk
    score: float
    match_type: str  # "dense", "sparse", "hybrid"


class FastCodeEmbedder:
    """Deterministic, high-throughput code embedding generator.

    Produces normalized 384-dimensional dense vectors using subword hashing,
    token positioning, and keyword weighting.
    """

    DIMENSION: int = 384

    @classmethod
    def embed_text(cls, text: str) -> np.ndarray:
        """Generates a unit-normalized vector for code or query text."""
        vec = np.zeros(cls.DIMENSION, dtype=np.float32)
        if not text:
            return vec

        # Tokenize by symbols, camelCase, snake_case
        tokens = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|\d+|[a-zA-Z_]+", text)
        if not tokens:
            return vec

        for idx, token in enumerate(tokens):
            tok_lower = token.lower()
            # Positional decay
            pos_weight = 1.0 / math.sqrt(idx + 1)
            # Hash to dimension slot
            h = int(hashlib.md5(tok_lower.encode("utf-8")).hexdigest(), 16)
            slot = h % cls.DIMENSION
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[slot] += sign * pos_weight

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec


class VectorStore(ABC):
    """Abstract vector storage and semantic search interface."""

    @abstractmethod
    async def index_chunks(self, repository_id: str, chunks: list[CodeChunk]) -> int:
        pass

    @abstractmethod
    async def search(
        self,
        repository_id: str,
        query: str,
        limit: int = 5,
        symbol_filter: str | None = None,
    ) -> list[SearchResult]:
        pass

    @abstractmethod
    async def delete_repository(self, repository_id: str) -> None:
        pass


class InMemoryVectorStore(VectorStore):
    """Fast in-memory vector store with hybrid dense and BM25-style lexical search."""

    def __init__(self) -> None:
        # repository_id -> list of CodeChunk
        self.chunks: dict[str, list[CodeChunk]] = defaultdict(list)
        # repository_id -> np.ndarray of shape (N, DIMENSION)
        self.embeddings: dict[str, np.ndarray] = {}
        # repository_id -> token -> list of chunk indices
        self.inverted_index: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))

    async def index_chunks(self, repository_id: str, chunks: list[CodeChunk]) -> int:
        """Indexes code chunks into in-memory dense and sparse indices."""
        if not chunks:
            return 0

        self.chunks[repository_id] = list(chunks)
        vecs = [FastCodeEmbedder.embed_text(f"{c.symbol_name} {c.docstring or ''} {c.content}") for c in chunks]
        self.embeddings[repository_id] = np.vstack(vecs)

        # Build sparse keyword index
        inv = defaultdict(list)
        for i, c in enumerate(chunks):
            text = f"{c.symbol_name} {c.file_path} {c.docstring or ''}"
            tokens = set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))
            for tok in tokens:
                inv[tok].append(i)
        self.inverted_index[repository_id] = inv

        return len(chunks)

    async def search(
        self,
        repository_id: str,
        query: str,
        limit: int = 5,
        symbol_filter: str | None = None,
    ) -> list[SearchResult]:
        """Executes hybrid dense-semantic and sparse-lexical retrieval."""
        chunks = self.chunks.get(repository_id, [])
        if not chunks or repository_id not in self.embeddings:
            return []

        # 1. Dense cosine similarity
        query_vec = FastCodeEmbedder.embed_text(query)
        matrix = self.embeddings[repository_id]
        dense_scores = np.dot(matrix, query_vec)

        # 2. Sparse lexical scores
        sparse_scores = np.zeros(len(chunks), dtype=np.float32)
        query_tokens = set(re.findall(r"[a-zA-Z0-9_]+", query.lower()))
        inv = self.inverted_index.get(repository_id, {})
        for tok in query_tokens:
            if tok in inv:
                for chunk_idx in inv[tok]:
                    sparse_scores[chunk_idx] += 1.0

        # Normalize sparse scores
        max_sparse = np.max(sparse_scores) if np.max(sparse_scores) > 0 else 1.0
        sparse_norm = sparse_scores / max_sparse

        # 3. Hybrid blend
        hybrid_scores = (0.6 * dense_scores) + (0.4 * sparse_norm)

        # 4. Rank and filter
        scored_indices = sorted(
            range(len(chunks)),
            key=lambda i: hybrid_scores[i],
            reverse=True,
        )

        results: list[SearchResult] = []
        for idx in scored_indices:
            chunk = chunks[idx]
            if symbol_filter and symbol_filter.lower() not in chunk.symbol_name.lower():
                continue

            results.append(
                SearchResult(
                    chunk=chunk,
                    score=float(hybrid_scores[idx]),
                    match_type="hybrid" if sparse_scores[idx] > 0 else "dense",
                )
            )
            if len(results) >= limit:
                break

        return results

    async def delete_repository(self, repository_id: str) -> None:
        """Purges indexed repository chunks."""
        self.chunks.pop(repository_id, None)
        self.embeddings.pop(repository_id, None)
        self.inverted_index.pop(repository_id, None)


class QdrantVectorStore(VectorStore):
    """Qdrant-backed vector store connecting via REST client with automatic in-memory fallback."""

    def __init__(self, host: str = "localhost", port: int = 6333, collection: str = "code_symbols") -> None:
        self.host = host
        self.port = port
        self.collection = collection
        self.base_url = f"http://{host}:{port}"
        self.fallback = InMemoryVectorStore()

    async def _is_healthy(self) -> bool:
        """Verifies if Qdrant service is reachable."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(f"{self.base_url}/healthz")
                return res.status_code == 200
        except Exception:
            return False

    async def index_chunks(self, repository_id: str, chunks: list[CodeChunk]) -> int:
        """Indexes chunks into Qdrant collection or falls back to in-memory store."""
        healthy = await self._is_healthy()
        if not healthy:
            logger.debug("Qdrant service unreachable at %s; using in-memory vector store", self.base_url)
            return await self.fallback.index_chunks(repository_id, chunks)

        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Ensure collection exists
            await client.put(
                f"{self.base_url}/collections/{self.collection}",
                json={
                    "vectors": {"size": FastCodeEmbedder.DIMENSION, "distance": "Cosine"}
                },
            )

            points: list[dict[str, Any]] = []
            for c in chunks:
                vec = FastCodeEmbedder.embed_text(f"{c.symbol_name} {c.docstring or ''} {c.content}")
                points.append({
                    "id": abs(hash(c.chunk_id)) % (2**63 - 1),
                    "vector": vec.tolist(),
                    "payload": {
                        "chunk_id": c.chunk_id,
                        "repository_id": repository_id,
                        "file_path": c.file_path,
                        "language": c.language,
                        "symbol_name": c.symbol_name,
                        "symbol_type": c.symbol_type,
                        "start_line": c.start_line,
                        "end_line": c.end_line,
                        "content": c.content,
                        "docstring": c.docstring,
                    },
                })

            if points:
                await client.put(
                    f"{self.base_url}/collections/{self.collection}/points",
                    json={"points": points},
                )

        return len(chunks)

    async def search(
        self,
        repository_id: str,
        query: str,
        limit: int = 5,
        symbol_filter: str | None = None,
    ) -> list[SearchResult]:
        """Searches Qdrant with payload filter on repository_id."""
        healthy = await self._is_healthy()
        if not healthy:
            return await self.fallback.search(repository_id, query, limit, symbol_filter)

        import httpx

        query_vec = FastCodeEmbedder.embed_text(query).tolist()
        filter_conditions: list[dict[str, Any]] = [
            {"key": "repository_id", "match": {"value": repository_id}}
        ]
        if symbol_filter:
            filter_conditions.append({"key": "symbol_name", "match": {"text": symbol_filter}})

        search_payload = {
            "vector": query_vec,
            "filter": {"must": filter_conditions},
            "limit": limit,
            "with_payload": True,
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{self.base_url}/collections/{self.collection}/points/search",
                json=search_payload,
            )
            if resp.status_code != 200:
                return await self.fallback.search(repository_id, query, limit, symbol_filter)

            data = resp.json().get("result", [])
            results: list[SearchResult] = []
            for hit in data:
                p = hit.get("payload", {})
                chunk = CodeChunk(
                    chunk_id=p.get("chunk_id", ""),
                    file_path=p.get("file_path", ""),
                    language=p.get("language", "python"),
                    symbol_name=p.get("symbol_name", ""),
                    symbol_type=p.get("symbol_type", "FUNCTION"),
                    scope_path=[p.get("symbol_name", "")],
                    start_line=p.get("start_line", 1),
                    end_line=p.get("end_line", 1),
                    content=p.get("content", ""),
                    docstring=p.get("docstring"),
                )
                results.append(
                    SearchResult(
                        chunk=chunk,
                        score=float(hit.get("score", 0.0)),
                        match_type="dense",
                    )
                )
            return results

    async def delete_repository(self, repository_id: str) -> None:
        """Deletes repository points from Qdrant."""
        await self.fallback.delete_repository(repository_id)
        if await self._is_healthy():
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{self.base_url}/collections/{self.collection}/points/delete",
                    json={"filter": {"must": [{"key": "repository_id", "match": {"value": repository_id}}]}},
                )


# Global Vector Store Instance
vector_store: VectorStore = QdrantVectorStore(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT,
    collection=settings.QDRANT_COLLECTION_NAME,
)
