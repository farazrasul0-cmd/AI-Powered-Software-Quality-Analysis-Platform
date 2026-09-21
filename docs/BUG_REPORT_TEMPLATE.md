# Standardized Manual Testing Bug Report Form
*AI-Powered Software Quality Analysis Platform*

> [!IMPORTANT]
> When a step in [`MANUAL_TESTING_ROADMAP.md`](../MANUAL_TESTING_ROADMAP.md) fails, **STOP IMMEDIATELY**. Do not proceed to subsequent steps. Copy this template, fill out every section, and submit it for debugging and resolution.

---

## 1. Issue Overview

| Field | Value |
| :--- | :--- |
| **Bug Report ID** | `BUG-YYYYMMDD-001` *(e.g., BUG-20260920-001)* |
| **Testing Phase** | `[Phase 0 / Phase A / Phase B / ... / Phase M]` |
| **Step Number** | `[e.g., Step A.5, Step D.2, Step G.3]` |
| **Severity Level** | `[CRITICAL / HIGH / MEDIUM / LOW]` |
| **Reporter** | Manual QA Tester / Evaluator |
| **Date & Time** | `YYYY-MM-DD HH:MM:SS` |
| **Operating Environment** | Windows 10/11 PowerShell / Chrome DevTools / Docker |

---

## 2. Description & Summary
*Provide a concise 1-2 sentence description of what failed.*

> **Example**: "FastAPI fails to initialize with SQLite fallback when `DATABASE_URL` is omitted, throwing a KeyError in `session.py`."

---

## 3. Reproduction Steps
*List the exact sequence of commands or browser clicks executed:*

1. Run command: `...`
2. Open browser URL: `...`
3. Click on button: `...`
4. Observe failure.

---

## 4. Expected vs. Actual Behavior

### Expected Behavior
*What should have occurred according to the testing guide?*

### Actual Behavior
*What actually occurred? (e.g., error message, blank screen, crash)*

---

## 5. Error Logs & Terminal Diagnostics
*Paste the full, unedited terminal output, Python traceback, or npm error log below:*

```text
[PASTE LOGS HERE]
```

---

## 6. Browser Console & Network Diagnostics (If Applicable)
*Press `F12` in Chrome/Edge. Paste console red errors and failed network request details:*

- **Console Error**:
```javascript
// Paste browser console error here
```

- **Network Request**:
  - **URL**: `http://localhost:8000/api/v1/...`
  - **Method**: `[GET / POST / PUT / DELETE]`
  - **Status Code**: `[e.g., 500 Internal Server Error / 404 Not Found]`
  - **Response Body**:
```json
// Paste network response body here
```

---

## 7. Screenshots or Visual Evidence (Optional)
*Reference any screenshots or screen recordings captured:*
- `[Attach screenshot or note filename/path]`

---

## 8. Resolution & Developer Notes *(To be filled by engineer)*
- **Root Cause**:
- **Affected Component**:
- **Fix Commit / PR**:
- **Regression Verification**:
