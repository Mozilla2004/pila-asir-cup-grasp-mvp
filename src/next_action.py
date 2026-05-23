"""Next Action Recommendation module for AS-IR runtime."""

from __future__ import annotations


def generate_next_action_recommendation(asir_trace: dict) -> dict:
    """Generate next action recommendation based on current AS-IR state.

    This analyzes the current interaction state and generates
    structured recommendations for next actions, including
    validation patches when risks are detected.

    Args:
        asir_trace: Current AS-IR trace with phases and runtime state

    Returns:
        Dictionary with next action recommendation structure
    """
    # Extract current state information
    runtime = asir_trace.get("runtime", {})
    risk_policy = runtime.get("risk_policy", {})
    risk_level = risk_policy.get("level", "GREEN")

    phases = asir_trace.get("phases", [])
    failure_patches = asir_trace.get("failure_patches", [])

    # Determine current interaction state
    current_interaction_state = _determine_interaction_state(phases, risk_level)

    # Generate recommendation based on state
    if risk_level == "GREEN":
        recommendation = {
            "current_interaction_state": current_interaction_state,
            "risk_level": risk_level.lower(),
            "recommendation_type": "continue_execution",
            "action": "continue_to_next_stage",
            "reason": "all constraints satisfied, risks within acceptable range",
            "requires_validation": False,
        }
    else:
        # Generate validation patch recommendation
        recommendation = {
            "current_interaction_state": current_interaction_state,
            "risk_level": risk_level.lower(),
            "candidate_failure_hypotheses": _generate_failure_hypotheses(phases, failure_patches),
            "next_action_recommendation": _generate_validation_patch(failure_patches),
        }

    return recommendation


def _determine_interaction_state(phases: list, risk_level: str) -> str:
    """Determine the current interaction state from phases and risk."""
    if not phases:
        return "initialization"

    last_phase = phases[-1]
    phase_type = last_phase.get("type", "unknown")
    status = last_phase.get("status", "unknown")

    if risk_level == "ORANGE":
        return f"{phase_type}_failure"
    elif risk_level == "YELLOW":
        return f"{phase_type}_warning"
    elif status == "failure":
        return f"{phase_type}_failed"
    elif status == "warning":
        return f"{phase_type}_unstable"
    else:
        return f"{phase_type}_stable"


def _generate_failure_hypotheses(phases: list, failure_patches: list) -> list:
    """Generate candidate failure hypotheses from current state."""
    hypotheses = []

    # Extract hypotheses from failure patches if available
    for patch in failure_patches:
        hypothesis = patch.get("failure_hypothesis", patch.get("root_cause"))
        if hypothesis:
            if isinstance(hypothesis, dict):
                hypotheses.append(hypothesis.get("primary", str(hypothesis)))
            else:
                hypotheses.append(str(hypothesis))

    # Add common failure patterns based on phase states
    for phase in phases:
        if phase.get("status") == "failure":
            phase_type = phase.get("type", "")
            if phase_type == "grasp":
                hypotheses.extend([
                    "insufficient_normal_force",
                    "contact_position_unstable",
                    "object_surface_properties_unexpected"
                ])
            elif phase_type == "lift":
                hypotheses.extend([
                    "insufficient_normal_force",
                    "lift_acceleration_too_high",
                    "support_degradation_during_motion"
                ])

    # Remove duplicates while preserving order
    seen = set()
    unique_hypotheses = []
    for h in hypotheses:
        if h not in seen:
            seen.add(h)
            unique_hypotheses.append(h)

    return unique_hypotheses[:4]  # Limit to top 4 candidates


def _generate_validation_patch(failure_patches: list) -> dict:
    """Generate validation patch recommendation."""
    if not failure_patches:
        return {
            "type": "investigation_required",
            "action": "collect_more_evidence",
            "reason": "no specific failure pattern identified",
            "requires_validation": True,
            "validation_metrics": []
        }

    # Use the first failure patch as basis
    patch = failure_patches[0]
    patch_actions = patch.get("patch", {})

    return {
        "type": "validation_patch",
        "action": {
            "force_adjustment": patch_actions.get("adjust_force", "unknown"),
            "contact_adjustment": patch_actions.get("adjust_contact", "unknown"),
            "restart_from_phase": patch_actions.get("restart_from_phase", "P3"),
        },
        "reason": "low-risk patch; helps distinguish between force and acceleration induced failures",
        "requires_validation": True,
        "validation_metrics": [
            "slip_score_peak",
            "tilt_deg_peak",
            "final_cup_height",
            "grip_force_stability"
        ],
        "validation_criteria": {
            "slip_score_peak": "< 0.3",
            "tilt_deg_peak": "< 8",
            "final_cup_height": "> 0.15",
            "grip_force_stability": "variance < 0.5"
        }
    }