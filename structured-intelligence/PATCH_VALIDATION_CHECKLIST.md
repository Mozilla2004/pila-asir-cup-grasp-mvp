# Patch Validation Checklist

Use this checklist before any L2 (validated) writeback.

---

## 1. Code Quality
- [ ] Code runs without errors (`python3 run_demo.py`)
- [ ] No `None` in HTML output
- [ ] No syntax errors in Python files

## 2. PILa / AS-IR Terminology
- [ ] No `root_cause` in main output path
- [ ] No `causal proof` or `guaranteed repair` claims
- [ ] `failure_hypothesis` used instead of `root_cause`

## 3. Stage-by-Stage Trace
- [ ] P0-P8 all present in output
- [ ] Each stage has required fields

## 4. HTML Report
- [ ] No `None` in rendered HTML
- [ ] Language switching works (EN/ZH)
- [ ] Version numbers consistent

## 5. Writeback Authority
- [ ] Writeback level identified as L0 / L1 / L2 / L3
- [ ] Strategic claims blocked unless human-approved
- [ ] CHANGELOG updated only after validation

## 6. Scope Boundary
- [ ] All modified files within scope boundary
- [ ] No forbidden changes made

---

*Part of the PILa / AS-IR structured intelligence governance framework.*
