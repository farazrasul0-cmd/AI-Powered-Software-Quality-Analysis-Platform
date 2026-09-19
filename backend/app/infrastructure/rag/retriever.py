"""Diff-Aware RAG Context Retriever.

Gathers related AST definitions, caller signatures, and interface contracts
from the vector store to supply the LLM with grounded codebase context.
"""


from app.infrastructure.rag.chunker import CodeChunk
from app.infrastructure.rag.vector_store import VectorStore, vector_store


class ContextRetriever:
    """Retrieves relevant code dependencies and symbol definitions for diff reviews."""

    def __init__(self, store: VectorStore | None = None) -> None:
        self.store = store or vector_store

    async def retrieve_context_for_chunk(
        self,
        repository_id: str,
        target_chunk: CodeChunk,
        limit: int = 3,
    ) -> list[CodeChunk]:
        """Retrieves external symbols referenced by target chunk."""
        related_chunks: list[CodeChunk] = []
        seen_ids = {target_chunk.chunk_id}

        # 1. Search by imported symbols
        for sym in target_chunk.imported_symbols[:4]:
            results = await self.store.search(
                repository_id=repository_id,
                query=sym,
                limit=2,
                symbol_filter=sym.split(".")[-1],
            )
            for res in results:
                if res.chunk.chunk_id not in seen_ids and res.score > 0.35:
                    seen_ids.add(res.chunk.chunk_id)
                    related_chunks.append(res.chunk)
                    if len(related_chunks) >= limit:
                        return related_chunks

        # 2. Search by semantic similarity of docstring and signature
        if len(related_chunks) < limit:
            query = f"{target_chunk.symbol_name} {target_chunk.docstring or ''}"
            results = await self.store.search(
                repository_id=repository_id,
                query=query,
                limit=limit - len(related_chunks),
            )
            for res in results:
                if res.chunk.chunk_id not in seen_ids and res.score > 0.30:
                    seen_ids.add(res.chunk.chunk_id)
                    related_chunks.append(res.chunk)

        return related_chunks

    @staticmethod
    def format_context_for_prompt(chunks: list[CodeChunk]) -> str:
        """Formats retrieved chunks into a prompt block for the LLM."""
        if not chunks:
            return "No external symbol context required."

        blocks: list[str] = []
        for c in chunks:
            blocks.append(
                f"--- Symbol: {c.symbol_name} ({c.symbol_type}) in {c.file_path}:{c.start_line}-{c.end_line} ---\n"
                f"{c.content.strip()}"
            )
        return "\n\n".join(blocks)
