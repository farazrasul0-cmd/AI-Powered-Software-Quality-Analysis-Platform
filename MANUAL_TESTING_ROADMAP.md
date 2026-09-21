# End-to-End Manual Testing Roadmap & Production Validation Guide
*CodeSentinel AI — Software Quality & Architecture Analysis Platform*

---

| Document Attribute | Specification |
| :--- | :--- |
| **Document Title** | CodeSentinel AI End-to-End Manual Testing Roadmap & Production Validation Guide |
| **System Version** | `v1.0.0-release` |
| **Testing Purpose** | Comprehensive Phase-by-Phase Black-Box & Grey-Box Production Validation |
| **Target Audience** | Manual QA Testers, SREs, Product Evaluators, Research Reviewers |
| **Dev Environment** | Windows 10/11 (PowerShell 7+ / 5.1), Python 3.12+, Node.js 20+, Git 2.40+ |
| **Deployment Target** | Local Standalone (SQLite + In-Memory RAG) & Multi-Container Cluster (Docker Compose) |

---

## Important Testing Rules & Protocol

This manual testing guide is designed for **strict sequential phase-by-phase execution**. As a manual tester, you must follow these rules without deviation:

1. **Strict Start from Phase 0**: Never skip ahead to UI or ML testing without validating the runtime environment and dependencies in Phase 0.
2. **Zero-Assumption Principle**: Never assume that because a command succeeded in a previous session, it still works. Execute every verification step.
3. **Stop-on-Failure Protocol (CRITICAL)**:
   - If any command, API response, UI screen, or assertion fails: **STOP IMMEDIATELY**.
   - Do **NOT** proceed to the next phase or attempt speculative manual fixes.
   - Capture the exact terminal output, browser console logs, network response, and screenshots.
   - File a standardized bug report using [`docs/BUG_REPORT_TEMPLATE.md`](docs/BUG_REPORT_TEMPLATE.md) and report it to the development team.
4. **Phase Sign-Off Criteria**: A phase can only be marked with `[x]` after:
   - All specified commands run with exit code `0`.
   - Expected outputs and HTTP status codes match the manual guide.
   - Browser console has 0 unhandled errors (`Red` exceptions).
   - Related log files or terminal output contain zero unhandled tracebacks.

---

## Section 1: Human Testing Mode Instructions

### 1.1 How to Use This Document
- Work through the document sequentially: **Phase 0 $\to$ Phase A $\to$ Phase B $\to \dots \to$ Phase M**.
- Check the box `[ ]` $\to$ `[x]` as each step passes.
- Maintain the **Testing Status Tracking Table** in Section 2.

### 1.2 How to Collect Diagnostic Logs
When an error occurs, collect logs based on the subsystem:
- **Frontend / Browser**: Press `F12` in Chrome/Edge/Firefox.
  - *Console Tab*: Filter by `Errors` and screenshot or right-click $\to$ "Save as..." to export logs.
  - *Network Tab*: Select the failed request (red text), view *Headers*, *Payload*, and *Preview/Response*.
- **Backend Gateway (FastAPI / Uvicorn)**:
  - Check the active terminal running `uvicorn app.main:app`.
  - Copy the Python traceback including the originating exception and request path.
- **Docker Container Logs** (When running in Mode B):
  ```powershell
  docker compose logs backend --tail=100
  docker compose logs celery_worker --tail=100
  docker compose logs postgres --tail=50
  docker compose logs redis --tail=50
  docker compose logs qdrant --tail=50
  ```

### 1.3 How to Report Errors Back to the Team
1. Open [`docs/BUG_REPORT_TEMPLATE.md`](docs/BUG_REPORT_TEMPLATE.md).
2. Fill out every section: Phase ID, Step Number, Command/URL, Expected Behavior, Actual Behavior, and Error Logs.
3. Submit the report and wait for code resolution and verification instructions before re-testing.

---

## Section 2: Master Testing Status Tracking Table

| Phase | System Under Test | Status | Date Verified | Blocking Issues | Resolution |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **Phase 0** | Host Environment & Toolchain Validation | `[PASSED]` | 2026-09-21 | None | All toolchains verified (Python 3.12, Node v24.14, npm 11.11, Git, Docker 29.8) |
| **Phase A** | Frontend Application Shell & Build | `[PASSED]` | 2026-09-21 | None | Vite build, Vitest (2/2), and TypeScript typecheck (0 errors) |
| **Phase B** | Backend Gateway & Standalone Execution | `[PASSED]` | 2026-09-21 | Ruff N803/N806 lint warnings | Added ignore flags in pyproject.toml; all 61 tests & OpenAPI /health verified |
| **Phase C** | Repository Ingestion & Intelligence Engine | `[PASSED]` | 2026-09-21 | None | Repository registration, AST parser, and Tarjan circular dependency SCC verified |
| **Phase D** | Static Analysis & AST Security Scanner | `[PASSED]` | 2026-09-21 | None | 13/13 static & security tests passed (McCabe, Halstead, CWE-89/78/502/798/327) |
| **Phase E** | ML Defect Prediction & TreeSHAP Attribution | `[PASSED]` | 2026-09-21 | None | Pre-trained defect_model_v1.joblib, sub-20ms scoring, and local TreeSHAP phi_i verified |
| **Phase F** | AST Semantic Chunker & Hybrid AI Review | `[PASSED]` | 2026-09-21 | None | Syntactic chunker, dual-mode vector store, and false-positive suppression verified |
| **Phase G** | Quality Scoring & Radar Scorecard Viewer | `[PASSED]` | 2026-09-21 | Celery Redis hang & SQLite locks | Added fast Redis check in analysis.py; enabled SQLite WAL mode in session.py |
| **Phase H** | Academic Benchmarks Evaluation (RQ1–RQ3) | `[PASSED]` | 2026-09-21 | None | RQ1 F1=1.000, RQ2 Recall@20%=80.0%, RQ3 FPSR=100.0% verified |
| **Phase I** | Standardized Reporting & Export Engine | `[PASSED]` | 2026-09-21 | Missing async repo_name resolution | Resolved repo_name asynchronously in exports.py; SARIF, MD, HTML verified |
| **Phase J** | GitHub CI/CD Actions & Webhook Security | `[PASSED]` | 2026-09-21 | None | Unsigned rejection (HTTP 401) and constant-time HMAC SHA-256 verified |
| **Phase K** | Real-Time SSE Event Streaming | `[PASSED]` | 2026-09-21 | None | text/event-stream connection and SSE progress payloads verified |
| **Phase L** | Container Orchestration (Docker Compose) | `[PASSED]` | 2026-09-21 | Non-root path, CORS, ML deps, volumes | Installed to /usr/local, CORS type relaxed, ML deps added, ml_engine mounted |
| **Phase M** | Production Readiness & Release Sign-Off | `[PASSED]` | 2026-09-21 | None | Ruff (0), MyPy (74/74), Pytest (61/61), Vitest (2/2), Vite build (26.17s) |

---

# Phase-by-Phase Detailed Test Plan

---

## Phase 0: Host Environment & Toolchain Validation

### Objective
Verify that the host machine satisfies all runtime prerequisites, compilers, language runtimes, package managers, and port allocations required for both standalone and containerized execution.

### Prerequisites
- Host machine running Windows 10/11 with PowerShell.

### Test Steps & Commands

#### Step 0.1: Runtime & Toolchain Version Checks
Run the following commands in PowerShell:

```powershell
python --version
node --version
npm --version
git --version
docker --version
docker compose version
```

- [ ] **Expected Output**:
  - Python: `Python 3.11.x` or `Python 3.12.x`
  - Node.js: `v18.x.x` or `v20.x.x` (or newer LTS)
  - npm: `9.x.x` or `10.x.x`
  - Git: `git version 2.x.x`
  - Docker: `Docker version 24.x+` (optional for Standalone Mode A, mandatory for Mode B)

#### Step 0.2: Port Availability Verification
Ensure no conflicting background services occupy platform ports:

```powershell
Get-NetTCPConnection -LocalPort 8000, 5173, 5432, 6379, 6333 -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, State, OwningProcess
```

- [ ] **Expected Output**:
  - No active listening sockets on `8000` (FastAPI) or `5173` (Vite).
  - If ports `5432`, `6379`, or `6333` are occupied by local services, ensure you run in **Standalone Mode A** or stop conflicting processes before testing Docker Mode B.

#### Step 0.3: Environment Configuration Template
Verify that `.env.example` exists in the project root and create your active `.env`:

```powershell
Test-Path .env.example
Copy-Item .env.example .env
Get-Content .env -Head 10
```

- [ ] **Expected Output**:
  - `True` for `Test-Path`.
  - Content shows environment keys: `APP_ENV=development`, `DATABASE_URL=...`, `SECRET_KEY=...`.

---

## Phase A: Frontend Application Shell & Build Testing

### Objective
Validate frontend dependency resolution, TypeScript strict compilation, unit test execution, production bundling, and local development server loading with zero runtime exceptions.

### Prerequisites
- Phase 0 passed.
- Working directory: `frontend/`.

### Test Steps & Commands

#### Step A.1: Frontend Dependency Installation
Navigate to the `frontend/` directory and install packages:

```powershell
cd frontend
npm install
```

- [ ] **Expected Output**:
  - `added ... packages in ...s`
  - `audited ... packages in ...s`
  - Zero critical npm installation errors.

#### Step A.2: Static TypeScript Type Checking
Run the TypeScript compiler in no-emit mode:

```powershell
npm run typecheck
```

- [ ] **Expected Output**:
  - Command completes with exit code `0` and **zero type errors**.

#### Step A.3: Frontend Unit & Component Tests
Run the Vitest test harness:

```powershell
npm run test:run
```

- [ ] **Expected Output**:
  - Test files pass (e.g., `src/test/Dashboard.test.tsx`).
  - `✓ 2 passed (2)` (or all tests passing).
  - Exit code `0`.

#### Step A.4: Production Bundle Generation
Compile and package the frontend for production:

```powershell
npm run build
```

- [ ] **Expected Output**:
  - `vite v5.x.x building for production...`
  - `dist/index.html`, `dist/assets/index-*.js`, `dist/assets/index-*.css` created in $< 6.0\text{s}$.
  - Zero packaging errors.

#### Step A.5: Development Server & Browser Visual Check
Launch the development server:

```powershell
npm run dev
```

- [ ] **Manual Verification**:
  1. Open Chrome/Edge at `http://localhost:5173`.
  2. Verify the top navigation bar displays:
     - "Antigravity Quality Platform" logo and title.
     - "Phase 1 Foundation" badge.
     - Navigation tabs: **"Repository"** (Active) and **"Dashboard"** (Disabled until report loaded).
  3. Verify the main card displays "Repository Onboarding" with:
     - Input field for GitHub / Local Git repository URL.
     - Branch selection input (default: `main`).
     - "Start Quality Analysis" button.
  4. Open Browser DevTools (`F12` $\to$ Console):
     - Confirm **0 unhandled JavaScript errors** (red text).

*Note: Keep this terminal open or run in background, then open a second terminal for Phase B.*

---

## Phase B: Backend Gateway & Standalone Execution Testing (Mode A)

### Objective
Verify backend virtual environment setup, Python dependencies, database schema initialization in standalone SQLite mode, FastAPI OpenAPI endpoints, and health probes.

### Prerequisites
- Phase 0 passed.
- Working directory: `backend/`.

### Test Steps & Commands

#### Step B.1: Virtual Environment Setup & Dependencies
In a new PowerShell terminal:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

- [ ] **Expected Output**:
  - Packages installed cleanly including `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `scikit-learn`, `shap`, `pytest`, `ruff`, `mypy`.

#### Step B.2: Code Quality & Type Safety Audit
Verify backend linting and type annotations:

```powershell
ruff check app ../ml_engine
mypy app
```

- [ ] **Expected Output**:
  - `All checks passed!`
  - `Success: no issues found in 74 source files`

#### Step B.3: Automated Backend Unit & Integration Tests
Run pytest across all unit and integration suites:

```powershell
pytest -v tests/unit
pytest -v tests/integration
```

- [ ] **Expected Output**:
  - 52 unit tests passed.
  - 6 integration tests passed.
  - Total: **58 passed in $< 5\text{s}$**.

#### Step B.4: Launch FastAPI Server (Standalone Mode)
Start Uvicorn server:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Manual Verification**:
  1. Terminal displays:
     - `INFO: Started server process`
     - `INFO: Waiting for application startup.`
     - `INFO: Application startup complete.`
     - `INFO: Uvicorn running on http://0.0.0.0:8000`
  2. Open another terminal or browser to verify health probe:
     ```powershell
     curl -s http://localhost:8000/api/v1/health
     ```
     Response JSON:
     ```json
     {"status":"ok","environment":"development","version":"1.0.0"}
     ```
  3. Navigate to `http://localhost:8000/docs` in browser:
     - Swagger UI loads with sections: `health`, `repositories`, `analysis`, `reports`, `events`, `reviews`, `scorecard`, `benchmarks`, `exports`, `webhooks`.

---

## Phase C: Repository Ingestion & Intelligence Engine Testing

### Objective
Verify the platform's ability to safely register a repository, detect primary programming languages, construct AST dependency graphs, detect circular imports via Tarjan's algorithm, and parse unified git diffs.

### Prerequisites
- Backend running on `http://localhost:8000`.

### Test Steps & Commands

#### Step C.1: Register a Local Repository
Send a POST request to onboard a repository:

```powershell
$repoPayload = @{
    name = "demo-repo"
    url = "https://github.com/example/demo-repo"
    default_branch = "main"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/repositories/" -Method Post -Body $repoPayload -ContentType "application/json"
$response | ConvertTo-Json
$global:REPO_ID = $response.id
Write-Host "Created Repository ID: $global:REPO_ID"
```

- [ ] **Expected Output**:
  - HTTP 201 / 200 response with `id`, `name: "demo-repo"`, `status: "ACTIVE"`.

#### Step C.2: Validate AST Dependency Graph & Circular Import Detection
Verify Tarjan's Strongly Connected Components (SCC) circular import detection algorithm via unit execution:

```powershell
pytest -k "test_dependency_graph" -v
```

- [ ] **Expected Output**:
  - Circular dependency chains detected cleanly without crashing.
  - Test passes: `PASSED [100%]`.

#### Step C.3: Validate Unified Git Diff Parser
Verify the diff parsing utility:

```powershell
pytest -k "test_diff_parser" -v
```

- [ ] **Expected Output**:
  - Hunk headers, added lines (`+`), and deleted lines (`-`) parsed into structured DTOs.
  - Test passes: `PASSED [100%]`.

---

## Phase D: Static Analysis & AST Security Scanner Testing

### Objective
Verify that the static engine computes McCabe Cyclomatic Complexity, Halstead metrics, and accurately detects AST-level code smells and critical security vulnerabilities across test fixtures without false negatives.

### Prerequisites
- Test fixtures in [`fixtures/static_samples/`](fixtures/static_samples).

### Test Steps & Commands

#### Step D.1: Verify Static Metric Calculation
Run complexity and maintainability index tests:

```powershell
pytest -k "test_static_analysis" -v
```

- [ ] **Expected Output**:
  - McCabe Cyclomatic Complexity correctly identifies branch points (`if`, `for`, `while`, `except`).
  - Halstead Software Science metrics compute vocabulary, length, volume, and effort.
  - Tests pass: `PASSED [100%]`.

#### Step D.2: Verify AST Security Scanner on Vulnerable Fixtures
Run security scanner tests against test fixtures:

```powershell
pytest -k "test_security" -v
```

- [ ] **Verification Matrix**:
  - [ ] **CWE-89 (SQL Injection)**: Flagged in `sec_sqli.py` (`SELECT * FROM users WHERE user = '` string concatenation).
  - [ ] **CWE-78 (Command Injection)**: Flagged in `sec_command_injection.py` (`os.system` with untrusted input).
  - [ ] **CWE-502 (Insecure Deserialization)**: Flagged in `sec_insecure_deserialization.py` (`pickle.loads(user_input)`).
  - [ ] **CWE-798 (Hardcoded Secrets)**: Flagged in `sec_hardcoded_secrets.py` (high-entropy API keys and passwords).
  - [ ] **CWE-327 (Weak Cryptography)**: Flagged in `sec_weak_crypto.py` (`hashlib.md5()`, `DES`).
  - [ ] All security tests report `PASSED`.

---

## Phase E: ML Defect Risk Prediction & TreeSHAP Attribution Testing

### Objective
Verify that the pre-trained machine learning model (`defect_model_v1.joblib`) loads into memory, performs sub-20ms inference on software metrics, maps outputs to Defect Risk Tiers, and generates local TreeSHAP attribution feature explanations ($\phi_i$).

### Prerequisites
- Serialized model present at `ml_engine/serialized/defect_model_v1.joblib`.

### Test Steps & Commands

#### Step E.1: Verify Model File Existence & Integrity
Check model artifact:

```powershell
Test-Path "..\ml_engine\serialized\defect_model_v1.joblib"
(Get-Item "..\ml_engine\serialized\defect_model_v1.joblib").Length
```

- [ ] **Expected Output**:
  - `True`. File size is $> 50\text{ KB}$.

#### Step E.2: Verify Defect Predictor & SHAP Explainer Unit Tests
Run ML engine test suite:

```powershell
pytest -k "test_defect_prediction" -v
```

- [ ] **Expected Output**:
  - `DefectPredictor` loads and scores metrics vector:
    `[loc, cyclomatic_complexity, halstead_volume, num_classes, num_functions, coupling_between_objects]`.
  - Predicted defect probability $P(\text{defect}) \in [0.0, 1.0]$.
  - Risk tier mapped:
    - $\ge 0.75$: `CRITICAL`
    - $\ge 0.50$: `HIGH`
    - $\ge 0.25$: `MEDIUM`
    - $< 0.25$: `LOW`
  - `TreeSHAPExplainer` returns attribution dictionary with feature names and local shap values $\phi_i$.
  - All tests pass: `PASSED [100%]`.

---

## Phase F: AST Semantic Chunker & Hybrid AI Review Testing

### Objective
Validate grammar-aware AST chunking for Python and TypeScript, verify dual-mode hybrid vector store (In-Memory BM25/Cosine vs Qdrant), and test hybrid triangulation with false-positive suppression.

### Prerequisites
- Python AST fixtures and vector store modules in `backend/app/infrastructure/`.

### Test Steps & Commands

#### Step F.1: Verify AST Semantic Chunker
Run chunker unit test:

```powershell
pytest -k "test_semantic_chunker" -v
```

- [ ] **Expected Output**:
  - Functions and classes chunked along exact syntactic boundaries without slicing tokens mid-scope.
  - Tests pass: `PASSED [100%]`.

#### Step F.2: Verify Dual-Mode Vector Store Fallback
Run vector store unit test:

```powershell
pytest -k "test_vector_store" -v
```

- [ ] **Expected Output**:
  - `InMemoryVectorStore` supports document upsert, cosine similarity, and BM25 lexical keyword matching without external Qdrant connection.
  - Tests pass: `PASSED [100%]`.

#### Step F.3: Verify Hybrid Triangulation & False-Positive Suppression
Run hybrid review unit test:

```powershell
pytest -k "test_hybrid_review" -v
```

- [ ] **Expected Output**:
  - Benchmarked against `clean_control.py`:
    - Benign mock credentials and test patterns correctly suppressed (`FALSE_POSITIVE_OVERRIDE`).
  - Benchmarked against real vulnerabilities (`sec_sqli.py`):
    - Confirmed security issue receives high priority ranking and automated unified git diff fix suggestion.
  - Tests pass: `PASSED [100%]`.

---

## Phase G: Quality Scoring & Radar Scorecard Viewer Testing

### Objective
Verify the multi-pillar quality scoring algorithm ($\text{RQI}$), radar scorecard breakdown (Maintainability, Security, Architecture, Testing), letter grade computation ($A$ through $F$), and frontend radar chart rendering.

### Prerequisites
- Backend running on `http://localhost:8000`.
- Frontend running on `http://localhost:5173`.

### Test Steps & Commands

#### Step G.1: Verify Scoring Algorithm Unit Tests
Run scoring engine tests:

```powershell
pytest -k "test_scoring" -v
```

- [ ] **Expected Output**:
  - Formula: $\text{RQI} = 0.35 S_{\text{sec}} + 0.30 S_{\text{maint}} + 0.20 S_{\text{arch}} + 0.15 S_{\text{test}}$.
  - False-positive security alerts do not degrade $S_{\text{sec}}$ (immunity rule verified).
  - Letter grade thresholds: $\ge 90 \to A$, $\ge 80 \to B$, $\ge 70 \to C$, $\ge 60 \to D$, $< 60 \to F$.
  - Tests pass: `PASSED [100%]`.

#### Step G.2: End-to-End Pipeline Trigger via API
Trigger an analysis job:

```powershell
$analysisPayload = @{
    repository_id = $global:REPO_ID
    branch = "main"
} | ConvertTo-Json

$job = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analysis/trigger" -Method Post -Body $analysisPayload -ContentType "application/json"
$global:JOB_ID = $job.id
Write-Host "Triggered Job ID: $global:JOB_ID (Status: $($job.status))"
```

- [ ] **Expected Output**:
  - Response contains `id`, `status: "COMPLETED"` (or `QUEUED`), and `repository_id`.

#### Step G.3: Retrieve Scorecard Data
Fetch radar scorecard for the generated report:

```powershell
$report = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reports/job/$global:JOB_ID" -Method Get
$global:REPORT_ID = $report.id

$scorecard = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reports/$global:REPORT_ID/scorecard" -Method Get
$scorecard | ConvertTo-Json -Depth 4
```

- [ ] **Expected Output**:
  - Contains:
    - `overall_rqi` (numerical float).
    - `letter_grade` (`A`, `B`, `C`, `D`, or `F`).
    - `pillar_scores`: Maintainability, Security, Architecture, Testing.
    - `radar_data`: 5-axis array formatted for Recharts.
    - `top_recommendations`: List of top 3 actionable fixes.

#### Step G.4: Browser Visual Check of Dashboard & Radar Chart
1. In `http://localhost:5173`, click **"Dashboard"** tab (or let onboarding redirect).
2. [ ] **Visual Verifications**:
   - [ ] Top banner displays repository name, commit hash, and branch.
   - [ ] **Overall Quality Gauge**: Shows composite RQI score and Letter Grade badge with matching color (Green for A/B, Yellow for C, Red for D/F).
   - [ ] **4 Pillar Metric Cards**: Maintainability, Security, Architecture, Testing scores displayed with trend icons.
   - [ ] **Radar Scorecard**: 5-axis Recharts polygon rendered cleanly with interactive tooltips on hover.
   - [ ] **Top Recommendations Card**: Displays priority fixes with severity pills (`CRITICAL`, `HIGH`, `MEDIUM`).
   - [ ] **Code Review & Diff Viewer**: Displays analyzed files, TreeSHAP waterfall bars, and unified diff suggestions.

---

## Phase H: Academic Benchmarks Evaluation (RQ1–RQ3) Testing

### Objective
Verify that the empirical academic benchmark testbed can be queried through API endpoints to produce quantitative evidence for Research Questions 1, 2, and 3.

### Prerequisites
- Backend running on `http://localhost:8000`.

### Test Steps & Commands

#### Step H.1: Query Benchmark Corpus
Retrieve labeled ground-truth benchmark samples:

```powershell
$corpus = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/benchmarks/corpus" -Method Get
Write-Host "Corpus Sample Count: $($corpus.Count)"
$corpus[0] | ConvertTo-Json
```

- [ ] **Expected Output**:
  - Array of benchmark samples containing file path, ground truth label (`is_defective`), flaw categories, and lines of code.

#### Step H.2: Execute Benchmark Experiments (RQ1–RQ3)
Invoke the benchmark evaluator:

```powershell
$benchmarks = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/benchmarks/experiments" -Method Get
$benchmarks | ConvertTo-Json -Depth 5
```

- [ ] **Expected Output & Verification**:
  - [ ] **RQ1 (Triangulation Performance)**:
    - `f1_score` $\ge 0.95$ (Platform Result: $1.000$).
    - Demonstrates improvement over standalone static baseline.
  - [ ] **RQ2 (Defect Concentration / Effort-Aware Ranking)**:
    - `recall_at_top_20_percent_loc` $\ge 0.70$ (Platform Result: $0.800$ vs Random baseline $0.200$).
  - [ ] **RQ3 (False-Positive Suppression)**:
    - `false_positive_suppression_rate` $= 1.000$ ($100.0\%$).
    - Retained critical security detections $= 1.000$ ($100.0\%$).

---

## Phase I: Standardized Reporting & Export Testing

### Objective
Verify that analysis reports can be exported in industry-standard formats: OASIS SARIF v2.1.0 (for GitHub Code Scanning), PR Markdown summaries, and print-ready standalone HTML reports.

### Prerequisites
- Active `$global:REPORT_ID` from Phase G.

### Test Steps & Commands

#### Step I.1: OASIS SARIF v2.1.0 Compliance
Export SARIF log via API:

```powershell
$sarif = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reports/$global:REPORT_ID/export/sarif" -Method Get
Write-Host "SARIF Schema: $($sarif.'$schema')"
Write-Host "SARIF Version: $($sarif.version)"
Write-Host "Tool Name: $($sarif.runs[0].tool.driver.name)"
Write-Host "Results Count: $($sarif.runs[0].results.Count)"
```

- [ ] **Expected Output**:
  - `version: "2.1.0"`
  - `tool.driver.name: "AI-Powered Software Quality Analysis Platform"`
  - `results` array contains validated security findings with rule IDs and physical locations.

#### Step I.2: GitHub Pull Request Markdown Export
Export PR comment Markdown:

```powershell
$md = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reports/$global:REPORT_ID/export/markdown" -Method Get
$md.markdown | Select-String "Repository Quality Index"
```

- [ ] **Expected Output**:
  - Markdown text with summary table, pillar scores, defect risks, and collapsible recommendations.

#### Step I.3: Standalone Print-Ready HTML Executive Report
Export HTML executive report:

```powershell
$html = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reports/$global:REPORT_ID/export/html" -Method Get
$htmlPath = "$env:TEMP\quality_report_$global:REPORT_ID.html"
$html.html | Out-File -FilePath $htmlPath -Encoding utf8
Write-Host "Saved report to: $htmlPath"
Start-Process $htmlPath
```

- [ ] **Manual Browser Verification**:
  1. File opens in default web browser.
  2. Displays executive header: Project Name, Grade Badge, Radar Scores, and Executive Summary.
  3. Press `Ctrl + P` (Print Preview):
     - Confirm `@media print` styling removes navigation bars and formats pages cleanly with page-break protection.

#### Step I.4: Frontend Modal Verification
1. On `http://localhost:5173`, click **"Export Report"** button in top right of dashboard.
2. [ ] **Modal Verifications**:
   - [ ] "OASIS SARIF v2.1.0" tab shows downloadable JSON.
   - [ ] "Markdown" tab shows formatted PR preview with "Copy to Clipboard" button.
   - [ ] "Executive HTML" tab shows "Download HTML" and "Print Report" buttons.

---

## Phase J: GitHub CI/CD Actions & Webhook Security Testing

### Objective
Verify that the webhook receiver enforces constant-time HMAC SHA-256 signature verification (`X-Hub-Signature-256`), rejects forged payloads, and processes valid GitHub push/pull_request events.

### Prerequisites
- Backend running on `http://localhost:8000`.

### Test Steps & Commands

#### Step J.1: Reject Unsigned / Malicious Webhook Delivery
Send a webhook payload without a signature header:

```powershell
$fakePayload = '{"action":"opened","pull_request":{"id":123}}'
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/webhooks/github" -Method Post -Body $fakePayload -ContentType "application/json"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "Unsigned request rejected with HTTP status: $statusCode"
}
```

- [ ] **Expected Output**:
  - Rejection with HTTP `401 Unauthorized` or `400 Bad Request`.

#### Step J.2: Verify Constant-Time HMAC Signature Verification
Run webhook security unit test:

```powershell
pytest -k "test_exports_and_webhooks_api" -v
```

- [ ] **Expected Output**:
  - Valid HMAC SHA-256 signatures are accepted (`200 OK`).
  - Altered or spoofed signatures are rejected with `401 Unauthorized`.
  - Tests pass: `PASSED [100%]`.

---

## Phase K: Real-Time SSE Event Streaming Testing

### Objective
Verify that long-running analysis workflows publish real-time progress events over Server-Sent Events (SSE), allowing the frontend UI to display live progress bars and step transitions without page reloads.

### Prerequisites
- Backend running on `http://localhost:8000`.

### Test Steps & Commands

#### Step K.1: Stream Events via HTTP
Connect to the event stream for an analysis job:

```powershell
$jobStreamUrl = "http://localhost:8000/api/v1/events/stream/$global:JOB_ID"
Write-Host "Connecting to SSE stream at: $jobStreamUrl"
# Fetch first event batch
$streamResponse = Invoke-WebRequest -Uri $jobStreamUrl -Headers @{ "Accept" = "text/event-stream" } -TimeoutSec 5
$streamResponse.Content
```

- [ ] **Expected Output**:
  - MIME type: `text/event-stream`.
  - Contains events formatted with `event: progress` and `data: {"status": ..., "progress_percent": ...}`.

#### Step K.2: Browser Visual Verification of Analysis Animation
1. On `http://localhost:5173`, navigate to "Repository" tab.
2. Enter repository URL `https://github.com/example/demo-repo` and click **"Start Quality Analysis"**.
3. [ ] **Visual Verifications**:
   - [ ] Progress bar advances smoothly: $0\% \to 25\% \to 50\% \to 75\% \to 100\%$.
   - [ ] Step indicator updates:
     1. Ingesting & Git Shallow Clone
     2. AST Complexity & Security Scanning
     3. ML Defect Probability Scoring
     4. LLM Semantic Triangulation
     5. Multi-Pillar RQI Calculation
   - [ ] Automatically transitions to the Quality Dashboard upon completion.

---

## Phase L: Container Orchestration & Production Cluster Testing (Mode B)

### Objective
Verify the multi-container Docker Compose deployment topology, service health checks, inter-service networking, Celery worker task consumption, and Nginx reverse proxy.

### Prerequisites
- Docker Desktop or Docker daemon running.
- Clean working directory with `.env` configured.

### Test Steps & Commands

#### Step L.1: Launch Multi-Container Production Cluster
From project root, execute:

```powershell
docker compose up -d --build
```

- [ ] **Expected Output**:
  - Container images build without errors:
    - `docker/Dockerfile.backend`
    - `docker/Dockerfile.frontend`
  - 6 services launched: `postgres`, `redis`, `qdrant`, `backend`, `celery_worker`, `frontend`.

#### Step L.2: Check Container Health Status
Inspect running containers:

```powershell
docker compose ps
```

- [ ] **Expected Output**:
  | Service | Name | State | Ports | Health |
  | :--- | :--- | :---: | :---: | :---: |
  | `postgres` | `quality_postgres` | `Up` | `5432/tcp` | `healthy` |
  | `redis` | `quality_redis` | `Up` | `6379/tcp` | `healthy` |
  | `qdrant` | `quality_qdrant` | `Up` | `6333/tcp` | `healthy` |
  | `backend` | `quality_backend` | `Up` | `8000/tcp` | `healthy` |
  | `celery_worker`| `quality_celery_worker`| `Up` | &mdash; | `healthy` / `running` |
  | `frontend` | `quality_frontend` | `Up` | `5173/tcp`, `80/tcp` | `healthy` / `running` |

#### Step L.3: Validate Cluster End-to-End Operation
1. Open browser to `http://localhost:5173` or `http://localhost:80`.
2. Verify frontend loads through Nginx reverse proxy.
3. Trigger an analysis through the UI.
4. Check Celery worker processing logs:
   ```powershell
   docker compose logs celery_worker --tail=20
   ```
   - [ ] Worker logs show: `Task app.workers.celery_app.run_full_analysis[...] succeeded in ...s`.

#### Step L.4: Clean Cluster Teardown
When testing finishes:

```powershell
docker compose down
```

- [ ] **Expected Output**: All 6 containers stopped and removed cleanly.

---

## Phase M: Production Readiness & Release Sign-Off

### Objective
Execute final regression suites, security sanity checks, documentation checks, and formal production release sign-off.

### Prerequisites
- All previous phases (Phase 0 through Phase L) completed and passing.

### Test Steps & Commands

#### Step M.1: Complete Automated Verification Suite
Run full test pass from repository root:

```powershell
# 1. Backend Linting & Types
cd backend
ruff check app ../ml_engine
mypy app

# 2. All 58 Backend Tests
pytest -v

# 3. Frontend Types & Tests
cd ..\frontend
npm run typecheck
npm run test:run
npm run build
cd ..
```

- [ ] **Expected Output**:
  - `ruff`: 0 errors.
  - `mypy`: 0 errors across 74 files.
  - `pytest`: 58/58 passed.
  - `vitest`: 2/2 passed.
  - `vite build`: built in $< 5\text{s}$.

#### Step M.2: Security & Repository Cleanliness Audit
Verify no sensitive credentials or temporary agent files exist in Git tracking:

```powershell
git status --short
git log -1
```

- [ ] **Expected Output**:
  - Working tree clean.
  - Most recent commit is the signed production release.
  - No secret keys, passwords, or internal agent configuration files committed.

---

## Troubleshooting Guide & Diagnostic Matrix

| Error Symptom | Probable Cause | Diagnostic Command | Remediation Step |
| :--- | :--- | :--- | :--- |
| `Port 8000 already in use` | Previous Uvicorn process still running | `Get-NetTCPConnection -LocalPort 8000` | Stop process: `Stop-Process -Id <PID> -Force` |
| `Cannot connect to Redis` | Redis is not running in Standalone Mode | Check `.env` setting for `REDIS_URL` | In Standalone Mode, Redis is optional. Set `REDIS_URL=""` or leave blank for in-memory pub/sub fallback. |
| `ModuleNotFoundError: No module named 'ml_engine'` | PYTHONPATH does not include repository root | `Write-Host $env:PYTHONPATH` | Run `$env:PYTHONPATH = "d:\projects\AI-Powered Software Quality Analysis Platform"` |
| `TypeError / AttributeError during TreeSHAP scoring` | Outdated `shap` or `scikit-learn` version mismatch | `pip show shap scikit-learn` | Reinstall requirements: `pip install -r requirements.txt --force-reinstall` |
| `Frontend displays 'Failed to fetch report'` | Backend gateway is down or CORS origin blocked | Check DevTools Network tab for HTTP 500 or CORS error | Ensure backend is running on `http://localhost:8000` and CORS permits `http://localhost:5173`. |
| `Docker: container unhealthy` | Service startup timeout before dependency ready | `docker compose logs <service>` | Increase healthcheck `start_period: 30s` in `docker-compose.yml`. |
| `Unsigned webhook rejected (401)` | Secret mismatch or missing `X-Hub-Signature-256` | Check `WEBHOOK_SECRET` in `.env` | Ensure testing client generates valid HMAC SHA-256 hash using the configured secret. |
