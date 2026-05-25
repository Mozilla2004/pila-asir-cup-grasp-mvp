# Structured Intelligence — Governance Framework

This directory contains the governance and operational templates for AI-assisted coding in the PILa / AS-IR project.

---

## Purpose

Define explicit authority boundaries for ClaudeCode when working on this repository:

- **When ClaudeCode is a centralized executor**
- **When ClaudeCode can do distributed autonomous coding**
- **When ClaudeCode is allowed independent writeback**
- **What content requires human confirmation before writeback**

Core principle:

> **Distributed Coding does not mean unrestricted writeback.**

---

## Files

| File | Description |
|------|-------------|
| `CODING_AUTHORITY_POLICY.md` | Defines centralized, distributed, and runtime coding modes |
| `WRITEBACK_AUTHORITY_MATRIX.md` | Maps files and content types to writeback levels (L0-L3) |
| `WRITEBACK_POLICY.md` | Operational writeback rules and enforcement |
| `WRITEBACK_LOG.md` | Records governance-layer writebacks |
| `CLAUDE_TASK_TEMPLATE.md` | Template for structuring ClaudeCode tasks with governance fields |
| `RUNTIME_TRACE_TEMPLATE.yaml` | Template for runtime trace output with governance metadata |
| `PATCH_VALIDATION_CHECKLIST.md` | Checklist for validating patches before writeback |

---

## Default Mode

> **Distributed Coding + Bounded Writeback**

---

## Writeback Levels

| Level | Name | Permission |
|-------|------|------------|
| L0 | No Writeback | Preview only |
| L1 | Trace Writeback | Autonomous |
| L2 | Validated Writeback | After validation |
| L3 | Strategic Writeback | Human approval required |

---

*Part of the PILa / AS-IR Cup-Grasp MVP v0.5.2-RC2 project.*
