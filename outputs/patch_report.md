# AS-IR Failure Patch Report (v0.3)

## Failure Diagnosis

- **Patch ID**: F1
- **Failure type**: slip
- **Failure hypothesis**: insufficient_normal_force_under_low_friction (confidence: medium)
- **Relation delta**: attempted -> degraded -> broken
- **Validation status**: passed

## Applied Patch

- **Force adjustment**: increase_grip_force
- **Contact adjustment**: shift_contact_position
- **Restart from phase**: P3

## Phase Comparison (Failure vs Patched)

| Phase | Failure Status | Patched Status |
|-------|---------------|----------------|
| P1 (approach) | success | success |
| P2 (align) | success | success |
| P3 (contact) | success | success |
| P4 (grasp) | warning | success |
| P5 (lift) | failure | success |

## Physical Invariants

- **no_slip**: violated -> satisfied
- **cup_upright**: violated -> satisfied

## Risk Policy

- Failure run: **ORANGE** — phase-level failure detected
- Patched run: **GREEN** — stable grasp maintained

## Learning Update

- Patch **F1** validated.
- Patch F1 validation passed: increase_grip_force + shift_contact_position. Grasp succeeded with slip_score < 0.3, cup_tilt < 8deg.
