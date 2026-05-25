# Coding Authority Policy

This repository supports AI-assisted coding with explicit authority boundaries.

The default governance mode is:

> **Distributed Coding + Bounded Writeback**

ClaudeCode may autonomously:
- Inspect files
- Propose implementation paths
- Modify code within task scope
- Create runtime traces
- Write audit notes
- Record remaining risks
- Update CHANGELOG after validation

ClaudeCode may NOT autonomously:
- Change core project positioning
- Claim real-robot validation
- Claim replacement of VLA / World Model / Controller
- Convert `failure_hypothesis` into `root_cause`
- Write speculative claims into README
- Update whitepaper-level conclusions without human approval

---

## 1. Coding Modes

### 1.1 Centralized Coding
The human defines the goal, implementation path, boundaries, and writeback content. ClaudeCode executes.

### 1.2 Distributed Coding
The human defines the goal, boundaries, and forbidden changes. ClaudeCode may autonomously choose implementation paths within scope.

### 1.3 Runtime Coding Agent Mode
ClaudeCode autonomously identifies issues, generates patches, validates results with minimal human guidance.

---

## 2. Writeback Levels

| Level | Name | Permission |
|-------|------|------------|
| L0 | No Writeback | None |
| L1 | Trace Writeback | Autonomous |
| L2 | Validated Writeback | After validation |
| L3 | Strategic Writeback | Human approval required |

---

## 3. Forbidden Actions

ClaudeCode must NEVER autonomously:
- Convert `failure_hypothesis` to `root_cause`
- Claim `causal proof` or `guaranteed repair`
- Add real-robot validation claims
- Claim replacement of VLA / World Model / Controller

---

*Part of the PILa / AS-IR structured intelligence governance framework.*
