---
name: jarvis-healthcheck
description: Full-stack health diagnostic for Jarvis. Runs 6 layers covering CLI tools, Python env, Ollama runtime, global symlink, doctrine integrity, and a live boot smoke test. Produces a HEALTHY/DEGRADED/DOWN verdict and escalates to other skills for fixes.
context_cost: heavy
model_tier: sonnet
capability_class: workflow
---

# jarvis-healthcheck

When invoked, run all 6 diagnostic layers in sequence. Output a structured report with a final verdict. Surface exact fix commands for blocking issues. Escalate to `/jarvis-audit` for doctrine violations. **Do not auto-fix system-level state** — always surface commands for the user to run and wait for approval before touching any repo files.

## How to invoke

```
/jarvis-healthcheck
```

---

## Layer 1 — CLI Tools

Use the Bash tool to check each tool via `command -v`:

Check: `claude`, `gemini`, `codex`, `ollama`, `python3`

Classify each result:
- `[ok]` — found
- `[--]` — absent (mark as BLOCKING if `ollama` is missing; mark as STANDBY if `codex` is missing; WARN for others)

---

## Layer 2 — Python Environment

Use the Glob tool to check `.venv/bin/pip` exists in the repo root.

Then run:
```bash
.venv/bin/pip show openai 2>/dev/null | grep -E "^Name:|^Version:"
```

Check:
- `.venv/` directory present
- `openai` package installed
- `docs/requirements.txt` exists (Glob)

---

## Layer 3 — Ollama Runtime

Run:
```bash
curl -s http://localhost:11434/api/tags 2>/dev/null
```

Parse the JSON response:
- If no response or connection refused → Ollama is DOWN → surface: `ollama serve`
- If response contains model list → check for `llama3.1` (or the value of `$JARVIS_MODEL` env var if set)
- If model absent → surface: `ollama pull llama3.1`

---

## Layer 4 — Global Symlink / PATH

Run:
```bash
which jarvis 2>/dev/null
```

- If found: report the resolved path `[ok]`
- If absent: mark DEGRADED — note that the symlink needs to be recreated (requires user approval, not auto-fixed)

---

## Layer 5 — Doctrine Integrity

Run these checks inline (do not spawn a sub-skill — run the grep checks directly):

**5a. Hardcoded absolute paths in scripts/**
```bash
grep -rn "/home/" scripts/ 2>/dev/null
```
Flag any matches as DOCTRINE FAIL with file:line.

**5b. .env committed to git**
```bash
git ls-files | grep -E "^\.env$"
```
If `.env` appears in tracked files → DOCTRINE FAIL.

**5c. Unguarded cloud SDK imports**
Use Grep tool on `scripts/*.py` for pattern `from openai|import openai` — then verify each match has `localhost` in the same file's `base_url` assignment. Flag any file where `openai` is imported but `localhost` is not present.

---

## Layer 6 — Boot Sequence Smoke Test

This layer confirms the full Phase 2 pipeline is live: Python → .venv → Ollama → model response.

Run a minimal classification call using the same system prompt as `jarvis.py`:

```bash
.venv/bin/python3 - <<'EOF'
import os, sys
try:
    from openai import OpenAI
except ImportError:
    print("FAIL: openai not installed")
    sys.exit(1)

base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
client = OpenAI(base_url=base_url, api_key="ollama")
model = os.getenv("JARVIS_MODEL", "llama3.1")

CLASSIFY_SYSTEM = (
    "You are a routing classifier. "
    "Reply with exactly one word: RESEARCH, DIGEST, or BUILD.\n"
    "RESEARCH = lookup, explain, summarize external knowledge.\n"
    "DIGEST = analyze or summarize text/logs the user provides.\n"
    "BUILD = write, create, or modify code or scripts.\n"
    "No other output. One word only."
)

try:
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CLASSIFY_SYSTEM},
            {"role": "user", "content": "explain what docker is"},
        ],
        temperature=0,
    )
    result = r.choices[0].message.content.strip().upper()
    print(f"SMOKE_RESULT:{result}")
except Exception as e:
    print(f"FAIL:{e}")
EOF
```

- If output contains `SMOKE_RESULT:RESEARCH` → PASS
- Any other output → FAIL — report raw output for diagnosis

---

## Output Format

Print the full structured report after all layers complete:

```
=== JARVIS HEALTH REPORT — <timestamp> ===

[LAYER 1 — CLI TOOLS]
  [ok] claude
  [ok] gemini
  [--] codex        (STANDBY — not blocking)
  [ok] ollama
  [ok] python3

[LAYER 2 — PYTHON ENV]
  [ok] .venv present
  [ok] openai installed (version X.X.X)
  [ok] docs/requirements.txt present

[LAYER 3 — OLLAMA RUNTIME]
  [ok] Ollama serving at localhost:11434
  [ok] llama3.1 model present

[LAYER 4 — GLOBAL COMMAND]
  [ok] `jarvis` → /usr/local/bin/jarvis

[LAYER 5 — DOCTRINE]
  [ok] No hardcoded absolute paths in scripts/
  [ok] .env not in git
  [ok] No unguarded cloud SDK imports

[LAYER 6 — BOOT SMOKE TEST]
  [ok] Classification: RESEARCH  (prompt: "explain what docker is")

=== VERDICT: HEALTHY ===
```

**Verdict rules:**
- `HEALTHY` — all layers pass (STANDBY items do not affect verdict)
- `DEGRADED` — non-blocking failures only (symlink absent, codex missing, doctrine warnings)
- `DOWN` — any BLOCKING failure: Ollama not running, model not pulled, `.venv` absent, openai not installed

---

## Fix Escalation Protocol

After the report, if any failures exist, append a remediation block:

```
=== REMEDIATION ===

[BLOCKING]
  1. Ollama not running       → run: ollama serve
  2. llama3.1 not pulled      → run: ollama pull llama3.1

[DEGRADED — approval required]
  3. Global `jarvis` symlink absent → requires symlink creation outside repo (approval needed)

[DOCTRINE — invoke jarvis-audit]
  4. Hardcoded path in scripts/foo.sh:12

Approve invoking /jarvis-audit for doctrine issues? (yes / no)
```

Rules:
- BLOCKING items: surface as exact shell commands for the user to run — do not execute them
- DEGRADED items: list with `approval needed` note — do not execute without explicit yes
- DOCTRINE items: after user approves, invoke `/jarvis-audit` for full resolution

If all layers pass with no issues, output only:

```
Doctrine aligned. Stack is healthy. Ready to build.
```
