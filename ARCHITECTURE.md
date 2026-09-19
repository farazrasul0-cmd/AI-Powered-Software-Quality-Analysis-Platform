# System Architecture & Technical Specifications
*AI-Powered Software Quality Analysis Platform*

---

## 1. High-Level Architecture Overview

The platform uses a layered microservices-oriented topology combining static AST analysis, machine learning defect prediction, and Large Language Model (LLM) contextual code review:

```
[ React 18 + TypeScript Dashboard (Vite + Tailwind + Recharts) ]
                             │
                             ▼ (HTTPS / REST / SSE)
         [ FastAPI API Gateway (Auth, Pydantic DTOs, SSE Stream) ]
                             │
       ┌─────────────────────┴─────────────────────┐
       ▼                                           ▼
[ PostgreSQL 16 ]                           [ Redis 7.x ]
(Relational Metadata, Runs, Metrics,         (Broker, Task Queue &
 Vulnerabilities, Quality Scores)             Pub/Sub Progress Stream)
                                                   │
                                                   ▼
                                [ Celery Worker Orchestrator ]
                                       (Canvas DAG Pipeline)
                                                   │
                                                   ▼
                         ┌─────────────────────────────────────────┐
                         │   Hardened Sandbox Execution Boundary   │
                         │   (Non-root, cgroups v2, No-net AST)    │
                         └─────────────────┬───────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
[ Static Analysis Engine ]      [ ML Defect Prediction ]        [ LLM RAG Code Review Engine ]
• Tree-sitter / Python AST      • CK Metric Extractor           • Grammar-Aware AST Chunker
• McCabe Cyclomatic Complexity  • Calibrated Tabular Classifier • Hybrid Retriever (Dense + Sparse)
• Halstead Software Science     • TreeSHAP Local Attributions   • Qdrant Vector DB Index
• AST Security Scanner (CWE)    • Risk Tiers (CRITICAL to LOW)  • Structured Output Guardrails
```

---

## 2. Architectural Principles

1. **Decoupled Asynchronous Processing**:
   The FastAPI web gateway remains 100% non-blocking. Heavy computation tasks (repository cloning, AST traversal, embedding indexing, ML defect classification, and LLM review calls) are dispatched through Celery queues with live progress streamed to clients via Server-Sent Events (SSE).
2. **Hardened Sandbox Ingestion**:
   Untrusted Git repositories are cloned shallowly (`--depth 1`), `.git` hooks are disabled (`core.hooksPath=/dev/null`), and source code is analyzed strictly via AST parsing &mdash; **never dynamically imported or executed**.
3. **Hybrid Triangulation Synthesis**:
   - **Static Engine**: High-speed, deterministic syntactic checks and vulnerability patterns.
   - **ML Defect Prediction**: Statistical defect probabilities using software engineering metrics (McCabe, Halstead, LOC, coupling) and local TreeSHAP attributions ($\phi_i$).
   - **LLM RAG Engine**: Contextual reasoning on elevated-risk code sections, cross-validating static alerts to eliminate false positives on test fixtures and mock code.
4. **Standardized Interoperability**:
   - Native export to **OASIS SARIF v2.1.0** for seamless ingestion into GitHub Security Code Scanning.
   - GitHub webhook receiver with constant-time HMAC SHA-256 signature verification (`hmac.compare_digest`).
   - Self-contained printable executive HTML reports (`@media print`) and PR Markdown comments.

---

## 3. Data & Storage Layer

- **PostgreSQL 16**: Relational storage for `repositories`, `analysis_jobs`, `analysis_reports`, `issues`, `file_metrics`, `defect_predictions`, and `review_comments`.
- **SQLite (Fallback)**: Zero-dependency async SQLite database for local standalone demonstrations and automated unit tests.
- **Redis 7.x**: In-memory message broker for Celery queues and real-time SSE event publishing.
- **Qdrant Vector DB**: Vector collection for 384-dimensional dense semantic code chunks with payload filtering.
- **InMemoryVectorStore (Fallback)**: Pure Python local vector store with cosine similarity and BM25 lexical search for offline environments.
