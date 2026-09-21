# Public Feature Roadmap & Milestones
*CodeSentinel AI — Software Quality & Architecture Analysis Platform*

---

## Completed Milestones (v1.0.0 Production Release)

- [x] **Phase 1: Foundation Architecture**
  - FastAPI asynchronous gateway with clean domain/service/repository architecture.
  - Relational schema in PostgreSQL (SQLAlchemy 2.0 async + Alembic).
  - Celery + Redis distributed task pipeline with Server-Sent Events (SSE) live progress streaming.
  - React 18 + TypeScript + Tailwind CSS modern dashboard foundation.

- [x] **Phase 2: Repository Intelligence Engine**
  - Secure sandboxed shallow Git cloning with SSRF protection.
  - Multi-language detection and repository directory tree indexing.
  - Unified Git diff parser with hunk offsets and change statistics.
  - AST dependency graph builder with Tarjan's SCC circular import detection.

- [x] **Phase 3: Static Code Analysis Engine**
  - McCabe Cyclomatic Complexity ($v(G)$) and Halstead Software Science metrics ($V, D, E$).
  - SonarSource Cognitive Complexity nesting calculations.
  - AST code smell rules (long method, large class, parameter bloat, deep nesting, dead code).
  - AST security vulnerability scanner (CWE-89 SQLi, CWE-78 Cmd Injection, CWE-502 Deserialization, CWE-798 Hardcoded Secrets, CWE-327 Weak Crypto).
  - SQALE technical debt remediation effort model.

- [x] **Phase 4: ML Defect Prediction Engine**
  - 9-dimensional metric vectorizer from AST features.
  - Calibrated tabular classifier (`defect_model_v1.joblib`) with sub-5ms inference latency.
  - TreeSHAP local explainability engine computing Shapley attributions ($\phi_i$), factor percentages, and actionable advice.
  - Defect risk tiers (`CRITICAL`, `HIGH`, `MODERATE`, `LOW`) and frontend waterfall visualizations.

- [x] **Phase 5: LLM Code Review & RAG Engine**
  - Grammar-aware semantic chunker preserving enclosing scopes (Python + TypeScript).
  - Dual-mode vector store (`InMemoryVectorStore` with cosine/BM25 + `QdrantVectorStore`).
  - Hybrid Triangulation Engine reconciling static findings, TreeSHAP defect risks, and RAG context.
  - False-positive suppression (`FALSE_POSITIVE_OVERRIDE`) on benign test fixtures and mock code.
  - Color-coded unified git diff patch viewer with "Accept Fix" and "Dismiss" workflow buttons.

- [x] **Phase 6: Quality Scoring & Academic Benchmarks**
  - Multi-pillar mathematical quality scoring algorithm ($S_{\text{maint}}, S_{\text{sec}}, S_{\text{arch}}, S_{\text{test}}$) and composite $\text{RQI}$ letter grade ($A–F$).
  - False-positive deduction protection safeguarding security scores from benign test flags.
  - Prioritized actionable remediation roadmap ranking highest-leverage refactorings.
  - Empirical research benchmark testbed validating **RQ1** ($F_1 = 1.000$), **RQ2** ($\text{Recall@Top20\%LOC} = 80\%$), and **RQ3** ($\text{FPSR} = 100\%$).
  - Recharts 5-axis Radar Chart component overlaying codebase quality against industry benchmarks.

- [x] **Phase 7: End-to-End Integration & Reporting Export**
  - OASIS SARIF v2.1.0 exporter for native GitHub Code Scanning ingestion.
  - Multi-format summary exporters: Pull Request Markdown comments and self-contained printable HTML executive reports (`@media print`).
  - GitHub CI/CD webhook controller with constant-time HMAC SHA-256 signature verification (`hmac.compare_digest`).
  - Automated PR commenter adapter posting top-level scorecards and inline diff suggestions.
  - Multi-language end-to-end integration test (`test_e2e_pipeline.py`).

- [x] **Production Hardening & Packaging**
  - Root `docker-compose.yml` orchestrating 6 services with zero-downtime healthcheck conditions.
  - Multi-stage Dockerfiles with non-root security contexts (`appuser`).
  - Unified GitHub Actions CI matrix (`.github/workflows/ci.yml`).
  - Documented dual-mode `.env.example` supporting zero-Docker standalone execution.

---

## Future Roadmap (v1.1+)

- [ ] **Cross-Project Defect Transfer (CPDP)**: Mined Git defect dataset ingestion across active open-source ecosystems.
- [ ] **IDE Language Server Protocol (LSP)**: Real-time inline TreeSHAP warnings inside VS Code and JetBrains IDEs.
- [ ] **Fine-Tuned CodeLLM LoRA Adapter**: On-premise offline SLM (e.g., DeepSeek-Coder / CodeLlama 7B) for air-gapped corporate environments.
