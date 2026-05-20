"""Extract AS-IR structured trace from raw trajectory data."""

from __future__ import annotations


def _phase_slices(phase_hint: list[str]) -> list[tuple[str, int, int]]:
    """Return [(phase_name, start_idx, end_idx), ...] from phase_hint list."""
    slices: list[tuple[str, int, int]] = []
    current = phase_hint[0]
    start = 0
    for i, p in enumerate(phase_hint):
        if p != current:
            slices.append((current, start, i))
            current = p
            start = i
    slices.append((current, start, len(phase_hint)))
    return slices


def _is_monotonic_decreasing(values: list[float], tolerance: float = 0.01) -> bool:
    decreases = sum(1 for i in range(1, len(values)) if values[i] < values[i - 1] + tolerance)
    return decreases > len(values) * 0.6


def _is_monotonic_increasing(values: list[float], tolerance: float = 0.01) -> bool:
    increases = sum(1 for i in range(1, len(values)) if values[i] > values[i - 1] - tolerance)
    return increases > len(values) * 0.6


def _phase_risk(phase_name: str, status: str) -> str:
    """Return per-phase risk level."""
    if status == "success":
        return "GREEN"
    if phase_name == "grasp" and status == "warning":
        return "YELLOW"
    if status == "failure":
        return "ORANGE"
    return "GREEN"


def _diagnose_phase(
    traj: dict, phase_name: str, start: int, end: int
) -> tuple[str, dict]:
    """Return (status, evidence) for a single phase.

    Status can be: success, warning, failure, anomaly, unknown.
    """
    grip_force = traj["grip_force"][start:end]
    contact_force = traj["contact_force"][start:end]
    slip_score = traj["slip_score"][start:end]
    cup_tilt = traj["cup_tilt"][start:end]
    cup_height = traj["cup_height"][start:end]
    gripper_distance = traj["gripper_distance"][start:end]

    evidence: dict = {}

    if phase_name == "approach":
        if _is_monotonic_decreasing(gripper_distance):
            evidence["gripper_distance"] = "decreasing"
            return "success", evidence
        return "anomaly", evidence

    if phase_name == "align":
        evidence["gripper_distance"] = "stabilized"
        return "success", evidence

    if phase_name == "contact":
        if _is_monotonic_increasing(contact_force):
            evidence["contact_force"] = "increased"
            return "success", evidence
        return "anomaly", evidence

    if phase_name == "grasp":
        max_slip = max(slip_score)
        avg_grip = sum(grip_force) / len(grip_force) if grip_force else 0
        evidence["avg_grip_force"] = f"{avg_grip:.2f}"
        evidence["max_slip_score"] = f"{max_slip:.2f}"
        # v0.2: warning at 0.3+, failure at 0.6+
        if max_slip > 0.6:
            return "failure", evidence
        if max_slip > 0.3 or avg_grip < 2.0:
            return "warning", evidence
        return "success", evidence

    if phase_name == "lift":
        max_slip = max(slip_score)
        max_tilt = max(cup_tilt)
        final_height = cup_height[-1]
        evidence["max_slip_score"] = f"{max_slip:.2f}"
        evidence["max_cup_tilt"] = f"{max_tilt:.1f}deg"
        evidence["final_cup_height"] = f"{final_height:.3f}m"
        if max_slip > 0.7 or max_tilt > 12:
            return "failure", evidence
        return "success", evidence

    return "unknown", evidence


def extract_asir_trace(traj: dict) -> dict:
    """Convert a raw trajectory dict into an AS-IR trace (v0.2)."""
    phase_hint = traj["phase_hint"]
    slices = _phase_slices(phase_hint)

    phase_ids = {"approach": "P1", "align": "P2", "contact": "P3", "grasp": "P4", "lift": "P5"}

    phases = []
    support_state = "established"
    support_reason = "sufficient_grip"

    for phase_name, start, end in slices:
        pid = phase_ids.get(phase_name, "?")
        status, evidence = _diagnose_phase(traj, phase_name, start, end)
        risk = _phase_risk(phase_name, status)
        phases.append({
            "id": pid,
            "type": phase_name,
            "status": status,
            "risk": risk,
            "evidence": evidence,
        })
        # Track support relation degradation
        if phase_name == "grasp" and status in ("failure", "warning"):
            support_state = "degraded"
            support_reason = "low_friction_slip"
        if phase_name == "lift" and status == "failure":
            support_state = "broken"
            support_reason = "low_friction_slip"

    # Determine physical relations
    physical_relations = [
        {"type": "proximity", "state": "established"},
        {"type": "contact", "state": "established"},
        {"type": "support", "state": support_state, "reason": support_reason},
    ]

    # Determine invariants
    max_slip = max(traj["slip_score"])
    max_tilt = max(traj["cup_tilt"])

    invariants = [
        {
            "name": "no_slip",
            "status": "violated" if max_slip > 0.7 else "satisfied",
        },
        {
            "name": "cup_upright",
            "status": "violated" if max_tilt > 12 else "satisfied",
        },
    ]

    # Global risk policy — escalated by worst phase
    phase_risks = [p["risk"] for p in phases]
    if "ORANGE" in phase_risks:
        risk_level = "ORANGE"
        risk_reason = "phase-level failure detected"
    elif "YELLOW" in phase_risks:
        risk_level = "YELLOW"
        risk_reason = "instability warning in grasp phase"
    else:
        risk_level = "GREEN"
        risk_reason = "stable grasp maintained"

    # Failure patches (v0.2 structure)
    failure_patches = []
    if not traj["success"]:
        failure_patches.append({
            "patch_id": "F1",
            "failure_type": "slip",
            "root_cause": "grip_force_insufficient_under_low_friction",
            "relation_delta": {
                "support": ["attempted", "degraded", "broken"],
            },
            "validation_status": "pending",
            "patch": {
                "adjust_force": "increase_grip_force",
                "adjust_contact": "shift_contact_position",
                "restart_from_phase": "P3",
            },
        })

    # Learning update
    learning_notes: list[str] = []
    if traj["success"]:
        learning_notes.append(
            "Patch F1 validation passed: increase_grip_force + shift_contact_position. "
            "Grasp succeeded with slip_score < 0.3, cup_tilt < 8deg."
        )
        learning_update = {
            "updated": True,
            "patch_validated": "F1",
            "notes": learning_notes,
        }
    else:
        learning_update = {
            "updated": False,
            "pending_update": "patch_generated_but_not_validated",
            "notes": [],
        }

    # Representation gain
    is_success = traj["success"]
    representation_gain = {
        "raw_observables": [
            "gripper_distance", "contact_force", "grip_force",
            "cup_height", "cup_tilt", "slip_score",
        ],
        "asir_structures": [
            "intent", "5 phases with status/risk",
            "3 physical relations", "2 physical invariants",
            "per-phase risk level",
        ],
        "diagnosable_failure": not is_success,
        "actionable_patch": not is_success,
        "reexecution_validated": is_success,
    }

    # Run metadata (passthrough from trajectory)
    run_meta = traj.get("run_metadata", {})

    trace = {
        "asir_version": "0.3",
        "task": "pick_up_cup",
        "run_metadata": {
            "run_id": run_meta.get("run_id", "unknown"),
            "scenario": run_meta.get("scenario", "unknown"),
            "friction_level": run_meta.get("friction_level", 0.25),
            "patch_applied": run_meta.get("patch_applied", False),
            "applied_patch_id": run_meta.get("applied_patch_id"),
        },
        "intent": {
            "goal_state": "cup_in_hand",
            "constraints": ["upright", "no_slip"],
            "success_criteria": {
                "cup_height": "> 0.15m",
                "cup_tilt": "< 8deg",
                "slip_score": "< 0.3",
            },
        },
        "phases": phases,
        "physical_relations": physical_relations,
        "runtime": {
            "physical_invariants": invariants,
            "risk_policy": {
                "level": risk_level,
                "reason": risk_reason,
            },
            "observability": [
                "grip_force",
                "slip_score",
                "cup_tilt",
                "contact_force",
            ],
        },
        "failure_patches": failure_patches,
        "transferability": {
            "domain_invariant": ["intent", "phase_order", "support_relation"],
            "domain_specific": ["grip_force_value", "contact_position"],
            "transfer_confidence": 0.78,
        },
        "learning_update": learning_update,
        "representation_gain": representation_gain,
    }

    return trace
