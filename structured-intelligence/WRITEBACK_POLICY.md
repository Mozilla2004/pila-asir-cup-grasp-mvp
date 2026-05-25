# Writeback Policy

This document defines the operational rules for ClaudeCode writeback to the repository.

---

## Core Principle

> **Distributed Coding ≠ Distributed Writeback**

ClaudeCode may write code autonomously within bounded scope, but writeback to the repository follows explicit authority rules.

---

## Writeback Levels

### L0 — No Writeback
Generated content stays in conversation context only.

### L1 — Trace / Audit Writeback
ClaudeCode autonomously writes runtime traces, audit notes, and risk records.

### L2 — Validated Writeback
ClaudeCode writes to repository after successful validation.

### L3 — Strategic Writeback
Human approval required before any writeback.

---

## Enforcement Rules

1. **Default to Lowest Level** — If writeback level is unclear, default to L0.
2. **Validation Before L2** — No L2 writeback without successful validation.
3. **Human Approval for L3** — No L3 writeback without explicit human approval.
4. **Scope Boundary Enforcement** — No writes outside scope boundary.
5. **Forbidden Change Enforcement** — No forbidden changes regardless of level.
6. **Violation Revert** — Revert immediately if violation detected.

---

*Part of the PILa / AS-IR structured intelligence governance framework.*
