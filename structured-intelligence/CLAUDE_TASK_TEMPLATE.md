# ClaudeCode Task Template

Use this template when assigning tasks to ClaudeCode in this repository.

---

## Task Definition

```yaml
task_id: "T-XXX"
title: "Task title"
description: "What needs to be done and why"
priority: P0 | P1 | P2
```

---

## Governance Fields

```yaml
coding_mode: centralized | distributed | runtime_agent
writeback_level: L0 | L1 | L2 | L3
scope_boundary:
  - "src/*.py"
  - "outputs/*.json"
forbidden_changes:
  - "Do not modify positioning docs"
  - "Do not change failure_hypothesis to root_cause"
validation_required: true | false
human_approval_required: true | false
```

---

## Completion Criteria

- [ ] All specified files modified as requested
- [ ] No forbidden changes made
- [ ] Validation passed (if required)
- [ ] Human approval obtained (if required)
- [ ] CHANGELOG updated (L2+ writebacks)

---

*Part of the PILa / AS-IR structured intelligence governance framework.*
