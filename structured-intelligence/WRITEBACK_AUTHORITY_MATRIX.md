# Writeback Authority Matrix

This document defines what ClaudeCode may write back to the repository, under what conditions, and at what authority level.

---

## Writeback Level Definitions

### L0 — No Writeback
Content is generated for inspection only. Nothing is written to the repository.

### L1 — Trace / Audit Writeback
ClaudeCode autonomously writes runtime traces, audit notes, and risk records.

### L2 — Validated Writeback
ClaudeCode writes to repository after successful validation.

### L3 — Strategic Writeback
Human approval required before any writeback.

---

## File-Level Authority Matrix

| File | L0 | L1 | L2 | L3 |
|------|----|----|----|----|
| `src/*.py` | Preview only | — | After validation | — |
| `outputs/*.json` | Preview | Autonomous | — | — |
| `outputs/*.html` | Preview | — | After validation | — |
| `docs/*.md` | Preview | — | After validation | — |
| `CHANGELOG.md` | — | — | After validation | — |
| `README.md` | — | — | — | Human approval |
| `docs/00_positioning.md` | — | — | — | Human approval |

---

*Part of the PILa / AS-IR structured intelligence governance framework.*
