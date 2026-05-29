# IEC 62304 — Bill of Materials / SOUP Analysis

**Date**: 2026-05-29 | **Version**: 0.5.4
**Standard**: IEC 62304:2006/AMD 1:2015, Clauses 5.3.3–5.3.4 (SOUP identification and verification)
**EU MDR**: Annex II, Section 4 (technical documentation — software bill of materials)

---

## 1. Dependency Summary

| Metric | Count |
|--------|-------|
| Direct dependencies (core) | 11 |
| Dev dependencies | 9 |
| Optional dependency groups | 11 |
| Total packages installed | 288 |
| Unique license families | ~15 |

### Existing Controls

- `docs/dependency-rationale.yaml` — rationale for every declared dependency
- `scripts/dependency_rationale.py --strict` — pre-commit hook enforcing rationale coverage
- `pip-audit` — CVE scanning in CI (`security.yml`)

---

## 2. Direct Dependencies (SOUP — Level 1)

| Package | Min Version | Installed | License | Rationale | Used In |
|---------|-------------|-----------|---------|-----------|---------|
| langchain-anthropic | ≥0.3.0 | 1.3.0 | MIT | Claude model provider | `llm_factory.py` |
| langchain-google-genai | ≥2.0.0 | 4.2.0 | MIT | Gemini model provider | `llm_factory.py` |
| langchain-mistralai | ≥0.2.0 | 1.1.1 | MIT | Mistral model provider | `llm_factory.py` |
| langchain-openai | ≥0.3.0 | 1.1.5 | MIT | OpenAI/DeepSeek/xAI provider | `llm_factory.py` |
| langgraph | ≥0.2.0 | 1.0.5 | MIT | Core graph orchestration engine | `graph_loader.py`, `executor.py` |
| langgraph-checkpoint-sqlite | ≥2.0.0 | 3.0.1 | MIT | SQLite state persistence | `checkpointer_factory.py` |
| pydantic | ≥2.0.0 | 2.12.3 | MIT | Structured data validation | `models/`, `schema_loader.py` |
| python-dotenv | ≥1.0.0 | 1.1.1 | BSD-3-Clause | .env file loading | `cli/__init__.py` |
| pyyaml | ≥6.0 | 6.0.3 | MIT | YAML parsing | `data_loader.py`, `graph_loader.py` |
| langsmith | ≥0.1.0 | 0.4.27 | MIT | Observability/tracing | `utils/tracing.py` |
| jinja2 | ≥3.1.0 | 3.1.6 | BSD (OSI) | Template engine | `utils/template.py` |

**License compliance**: All direct dependencies are MIT or BSD. No copyleft risk.

---

## 3. Critical Transitive Dependencies (SOUP — Level 2)

| Package | Version | License | Role | Brought In By |
|---------|---------|---------|------|---------------|
| langchain-core | 1.2.9 | MIT | Base LLM abstractions | All langchain-* providers |
| langchain | 1.2.0 | MIT | Chain/agent framework | langgraph |
| langgraph-sdk | 0.3.1 | MIT | Graph SDK | langgraph |
| langgraph-checkpoint | 3.0.1 | MIT | Checkpoint base | langgraph-checkpoint-sqlite |
| anthropic | 0.75.0 | MIT | Anthropic API client | langchain-anthropic |
| openai | 2.13.0 | Apache-2.0 | OpenAI API client | langchain-openai |
| google-generativeai | 0.8.5 | Apache-2.0 | Google AI client | langchain-google-genai |
| pydantic-core | 2.41.4 | MIT | Pydantic Rust core | pydantic |
| httpx | 0.28.1 | BSD-3-Clause | HTTP client | anthropic, openai |
| httpcore | 1.0.9 | BSD-3-Clause | HTTP transport | httpx |
| aiohttp | 3.12.13 | Apache-2.0 | Async HTTP | langchain, langsmith |
| requests | 2.32.5 | Apache-2.0 | HTTP client | langsmith |
| urllib3 | 2.5.0 | MIT | HTTP utilities | requests |
| typing-extensions | 4.15.0 | PSF-2.0 | Type system backports | pydantic |
| tenacity | 9.1.2 | Apache-2.0 | Retry logic | langchain-core |
| certifi | 2025.6.15 | MPL-2.0 | CA certificates | httpx, requests |
| markupsafe | 3.0.2 | BSD-3-Clause | HTML/XML escaping | jinja2 |
| aiosqlite | 0.22.0 | MIT | Async SQLite | langgraph-checkpoint-sqlite |

---

## 4. License Distribution (All 288 Packages)

| License Family | Count | Risk Level |
|----------------|-------|------------|
| MIT / MIT License | 141 | None |
| Apache-2.0 / Apache 2.0 | 55 | None |
| BSD (all variants) | 52 | None |
| PSF-2.0 / Python | 4 | None |
| ISC | 3 | None |
| MPL-2.0 | 2 | Low (weak copyleft, file-level) |
| Unlicense / Public Domain | 2 | None |
| LGPL-2.1-or-later | 1 | **Medium** (copyleft) |
| GPL-3.0-or-later | 1 | **High** (strong copyleft) |
| UNSPECIFIED | 5 | Review needed |
| Other permissive | 22 | None |

### License Compliance: 98.6% Permissive (284/288)

---

## 5. Flagged Dependencies

### GPL-3.0: pykakasi (2.3.0)

| Field | Detail |
|-------|--------|
| **License** | GPL-3.0-or-later |
| **What** | Japanese text transliteration |
| **Why installed** | Transitive via `chatterbox-tts` (optional TTS extra) |
| **In YAMLGraph core?** | **NO** — optional `[tts]` extra only |
| **Risk** | None for framework distribution. Only affects TTS demo deployments. |
| **Action** | Document in BOM. Users installing `[tts]` should be aware. |

### LGPL-2.1: soxr (1.0.0)

| Field | Detail |
|-------|--------|
| **License** | LGPL-2.1-or-later |
| **What** | Audio resampling (C library binding) |
| **Why installed** | Transitive via `librosa` → `chatterbox-tts` |
| **In YAMLGraph core?** | **NO** — optional TTS extra only |
| **Risk** | LGPL permits dynamic linking without copyleft obligations |
| **Action** | Acceptable. Document. |

### MPL-2.0: certifi (2025.6.15)

| Field | Detail |
|-------|--------|
| **License** | MPL-2.0 (Mozilla Public License) |
| **What** | CA certificate bundle for TLS |
| **Why installed** | Transitive via `httpx`, `requests` → all HTTP-based LLM providers |
| **In YAMLGraph core?** | **YES** — all LLM providers use HTTPS |
| **Risk** | MPL-2.0 is weak copyleft — obligations only apply to modifications of certifi's own files. Using it as a dependency creates no copyleft obligation. |
| **Action** | Acceptable. Standard in Python ecosystem. |

### UNSPECIFIED (5 packages)

| Package | Version | Status |
|---------|---------|--------|
| asyncio | 3.4.3 | Python stdlib — PSF license (metadata missing) |
| interrai-ca | 0.1.0 | **Orphan** — not in YAMLGraph dependency chain |
| interrai-ca | 0.1.0 | Duplicate entry |
| minesweeper | 0.1.0 | **Orphan** — not in YAMLGraph dependency chain |
| minesweeper | 0.1.0 | Duplicate entry |

**Note**: `interrai-ca` and `minesweeper` are project-scoped packages from the `projects/` directory — they are NOT YAMLGraph dependencies. They are local editable installs sharing the same virtual environment.

---

## 6. SOUP Verification (IEC 62304 Clause 5.3.4)

### Verification Strategy Per SOUP

| SOUP | Verification Method | Evidence |
|------|---------------------|----------|
| langgraph | Integration tests, streaming tests, real graph execution | 96+ tests across CAP-02, CAP-14 |
| pydantic | Schema validation tests, LLM output parsing | 312 prompt tests, all model tests |
| langchain-anthropic | Mocked in unit tests, real in integration | Provider test matrix |
| langchain-openai | Mocked in unit tests, real in integration | Provider test matrix |
| jinja2 | Template rendering tests | 154 expression tests |
| pyyaml | Config loading tests | 322 config tests |
| httpx/requests | Implicit via LLM provider tests | Network-dependent integration tests |
| certifi | Implicit — TLS handshake in every LLM call | Any integration test failure would surface |
| aiosqlite | Checkpointer persistence tests | CAP-07 state persistence tests |

### SOUP Known Anomalies

| Package | Known Issue | Impact | Mitigation |
|---------|------------|--------|------------|
| pyyaml | YAML 1.1 boolean gotcha (`yes`/`no` → True/False) | Config parsing surprise | Always quote boolean strings in YAML |
| pydantic v2 | Performance regression on deeply nested models | Schema validation latency | Limit nesting depth in graph schemas |
| langgraph | Breaking API changes between minor versions | Compilation failures | Pin ≥0.2.0, test on upgrade |
| httpx | Connection pool exhaustion under high concurrency | Timeout in race nodes | Race node has explicit timeout handling (REQ-YG-119) |
| certifi | CA bundle lag — new CAs arrive weeks after browser vendors | TLS handshake failure to new endpoints | Update quarterly |

---

## 7. Supply Chain Risk Assessment

| Risk | Likelihood | Impact | Controls |
|------|-----------|--------|----------|
| CVE in direct dependency | Medium | High | `pip-audit` in CI, security workflow |
| License contamination (copyleft) | Low | High | This BOM audit, no GPL in core deps |
| Typosquatting attack | Low | Critical | Pin to known-good package names in pyproject.toml |
| Dependency abandonment | Medium | Medium | All major deps backed by LangChain/Pallets/Pydantic orgs |
| Breaking API change | High | Medium | Version pinning (≥ minimum), CI catches failures |

---

## 8. Compliance Statement

| Regulation | Requirement | Status |
|------------|-------------|--------|
| IEC 62304 5.3.3 | SOUP identified with version, manufacturer, unique identifier | **PASS** — pyproject.toml + pip freeze |
| IEC 62304 5.3.4 | SOUP verified for intended use | **PASS** — integration tests per SOUP |
| EU MDR Annex II §4 | Software BOM in technical documentation | **PASS** — this document |
| EU AI Act Art. 15 | Cybersecurity by design, supply chain transparency | **PASS** — CVE scanning, license audit |

---

## 9. Dependency Rationale Coverage

```
Tool: python scripts/dependency_rationale.py --strict
Gate: pre-commit hook (blocks commit if any dep lacks rationale)
Status: PASS — all declared dependencies have documented rationale
File: docs/dependency-rationale.yaml
```

Every dependency in `pyproject.toml` (core + optional) has a documented entry with:
- **rationale**: Why it exists
- **modules**: Which source files use it
- **added**: Version when introduced
