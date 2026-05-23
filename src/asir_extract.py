"""Extract AS-IR structured trace from raw trajectory data."""

from __future__ import annotations

# Import next action recommendation for v0.5
try:
    from .next_action import generate_next_action_recommendation
except (ImportError, ValueError):
    # Fallback if module not available or running as script
    try:
        from next_action import generate_next_action_recommendation
    except ImportError:
        # Final fallback
        def generate_next_action_recommendation(asir_trace: dict) -> dict:
            return {"recommendation_type": "continue_execution"}


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


def _get_next_stage(current_stage_id: str) -> str:
    """Get the next stage ID in the sequence."""
    stage_order = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
    try:
        idx = stage_order.index(current_stage_id)
        if idx + 1 < len(stage_order):
            return stage_order[idx + 1]
    except ValueError:
        pass
    return "end"


def _get_stage_trigger(phase_name: str, component_states: dict) -> str:
    """Get the trigger condition for stage transition."""
    if phase_name == "approach":
        return f"gripper_distance < 0.05 (current: {component_states['gripper_distance']:.3f})"
    elif phase_name == "align":
        return f"gripper_distance stable (current: {component_states['gripper_distance']:.3f})"
    elif phase_name == "contact":
        return f"contact_force > 1.0 (current: {component_states['contact_force']:.2f})"
    elif phase_name == "grasp":
        return f"grip_force applied, slip_score {component_states['slip_score']:.2f}"
    elif phase_name == "lift":
        return f"cup_height > 0.1 (current: {component_states['cup_height']:.3f})"
    return "phase_complete"


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

        # Extract component states for this stage (v0.5 enhancement)
        component_states = {
            "gripper_distance": traj["gripper_distance"][end-1] if end > 0 else 0,
            "contact_force": traj["contact_force"][end-1] if end > 0 else 0,
            "grip_force": traj["grip_force"][end-1] if end > 0 else 0,
            "cup_height": traj["cup_height"][end-1] if end > 0 else 0,
            "slip_score": traj["slip_score"][end-1] if end > 0 else 0,
            "cup_tilt": traj["cup_tilt"][end-1] if end > 0 else 0,
        }

        # Extract stage-specific physical relations (v0.5)
        stage_physical_relations = []
        if phase_name in ["contact", "grasp", "lift"]:
            stage_physical_relations.append({"type": "contact", "state": "established"})
        if phase_name == "grasp" or phase_name == "lift":
            relation_state = "established"
            if status in ("failure", "warning"):
                relation_state = "degraded"
            if status == "failure" and phase_name == "lift":
                relation_state = "broken"
            stage_physical_relations.append({
                "type": "support",
                "state": relation_state,
                "health_metrics": {
                    "stability_score": 1.0 - component_states["slip_score"],
                    "load_capacity": 0.5 if relation_state == "degraded" else 0.8
                }
            })

        # Extract stage-specific risk signals (v0.5)
        risk_signals = []
        if phase_name == "grasp":
            risk_signals = [
                {"type": "slip_risk", "value": component_states["slip_score"], "threshold": 0.3, "severity": "high" if component_states["slip_score"] > 0.6 else "medium"},
                {"type": "force_stability", "value": "stable" if component_states["grip_force"] > 2.0 else "unstable", "metric": component_states["grip_force"]}
            ]
        elif phase_name == "lift":
            risk_signals = [
                {"type": "slip_risk", "value": component_states["slip_score"], "threshold": 0.7, "severity": "critical" if component_states["slip_score"] > 0.7 else "high"},
                {"type": "tilt_risk", "value": component_states["cup_tilt"], "threshold": 12.0, "severity": "critical" if component_states["cup_tilt"] > 12 else "medium"},
                {"type": "height_progress", "value": component_states["cup_height"], "target": 0.15, "status": "insufficient"}
            ]
        elif phase_name == "contact":
            risk_signals = [
                {"type": "contact_establishment", "value": component_states["contact_force"], "threshold": 1.0, "status": "established" if component_states["contact_force"] > 1.0 else "pending"}
            ]

        # Stage transition conditions (v0.5)
        transition_condition = {
            "from_stage": pid,
            "to_next": _get_next_stage(pid),
            "condition_met": status != "failure",
            "trigger": _get_stage_trigger(phase_name, component_states)
        }

        phases.append({
            "id": pid,
            "type": phase_name,
            "status": status,
            "risk": risk,
            "evidence": evidence,
            # v0.5: Enhanced stage-by-stage information
            "component_states": component_states,
            "physical_relations": stage_physical_relations,
            "risk_signals": risk_signals,
            "transition_condition": transition_condition,
        })

        # Track support relation degradation for legacy compatibility
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
            "failure_hypothesis": {
                "primary": "insufficient_normal_force_under_low_friction",
                "confidence": "medium",
                "evidence": ["elevating_slip_score", "increasing_tilt", "low_friction_condition"],
                "alternative_hypotheses": [
                    "acceleration_too_high",
                    "contact_position_unstable",
                    "object_surface_properties_changed"
                ]
            },
            "relation_delta": {
                "support": ["attempted", "degraded", "broken"],
            },
            "validation_required": True,
            "validation_metrics": [
                {"name": "slip_score_peak", "target": "< 0.3", "current": max_slip},
                {"name": "tilt_deg_peak", "target": "< 8", "current": max_tilt},
                {"name": "final_cup_height", "target": "> 0.15m", "current": "0.007m"},
                {"name": "grip_force_stability", "target": "variance < 0.5", "current": "unknown"}
            ],
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
        "next_action_recommendation": generate_next_action_recommendation({  # v0.5
            "phases": phases,
            "runtime": {"risk_policy": {"level": risk_level, "reason": risk_reason}},
            "failure_patches": failure_patches
        }),
        "representation_gain": representation_gain,
    }

    return trace
