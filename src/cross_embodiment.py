"""Cross-embodiment meaning transfer: adapt AS-IR failure patches to different robots."""

from __future__ import annotations

import json
import os

# Per-robot meaning interpretation templates
_MEANING_INTERPRETATIONS = {
    "two_finger_gripper": {
        "shared_meaning": "support relation degraded due to insufficient grip under low friction",
        "robot_specific_reading": "two-point contact cannot generate enough friction; increase normal force or shift contact to higher-friction surface region",
    },
    "three_finger_gripper": {
        "shared_meaning": "support relation degraded due to insufficient grip under low friction",
        "robot_specific_reading": "two-contact grasp lacks form closure; activate third finger to create triangular support and redistribute contact forces",
    },
    "suction_gripper": {
        "shared_meaning": "support relation degraded due to insufficient grip under low friction",
        "robot_specific_reading": "vacuum seal is marginal on this surface; increase suction pressure, verify seal integrity, and reduce acceleration to avoid peel-off",
    },
}


def load_robot_profiles(path: str | None = None) -> dict:
    """Load robot profiles from JSON file."""
    if path is None:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "robot_profiles.json",
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _map_failure_to_rule(asir_trace: dict) -> str:
    """Map AS-IR failure to a generic adapter rule key.

    Returns meaningful failure meaning instead of None/unknown:
    - support_degraded: Support relation failure (common case)
    - no_failure_detected: Successful trajectory without failures
    - unmapped_failure_pattern: Failure pattern doesn't match known rules
    """
    patches = asir_trace.get("failure_patches", [])

    # Check for successful trajectory (no failure patches)
    if not patches:
        # Check physical relations to determine if truly successful
        relations = asir_trace.get("physical_relations", [])
        support_relation = next((r for r in relations if r.get("type") == "support"), None)

        if support_relation and support_relation.get("state") == "established":
            return "no_failure_detected"
        else:
            return "unmapped_failure_pattern_requires_review"

    # Map known failure patterns
    relations = asir_trace.get("physical_relations", [])
    for r in relations:
        if r.get("type") == "support" and r.get("state") in ("degraded", "broken"):
            return "support_degraded"

    # Failure exists but pattern doesn't match known rules
    return "unmapped_failure_pattern_requires_review"


def adapt_patch_for_robot(
    asir_trace: dict, robot_id: str, robot_profile: dict
) -> dict:
    """Adapt an AS-IR failure patch into a robot-specific execution patch."""
    rule_key = _map_failure_to_rule(asir_trace)
    adapter = robot_profile.get("adapter_rules", {}).get(rule_key, {})

    actions = []
    action_keys = ["primary_action", "secondary_action", "tertiary_action"]
    for key in action_keys:
        if key in adapter:
            actions.append(adapter[key])

    interp = _MEANING_INTERPRETATIONS.get(robot_id, {})

    return {
        "robot_id": robot_id,
        "morphology_type": robot_profile["morphology_type"],
        "contact_model": robot_profile["contact_model"],
        "source_failure_meaning": rule_key,
        "source_failure_hypothesis": (
            asir_trace["failure_patches"][0].get("failure_hypothesis", asir_trace["failure_patches"][0].get("root_cause", "unmapped_failure"))
            if asir_trace.get("failure_patches")
            else "no_failure_hypothesis_required"
        ),
        "meaning_interpretation": {
            "shared_meaning": interp.get("shared_meaning", ""),
            "robot_specific_reading": interp.get("robot_specific_reading", ""),
        },
        "adapted_actions": actions,
        "restart_from_phase": adapter.get("restart_from", "P3"),
        "force_control_mode": robot_profile["force_control_mode"],
    }


def run_cross_embodiment_transfer(
    asir_trace: dict, robot_profiles: dict
) -> dict:
    """Run cross-embodiment transfer for all robots against one AS-IR trace."""
    rule_key = _map_failure_to_rule(asir_trace)

    transfer_result = {
        "asir_version": "0.5",
        "source_trace_task": asir_trace.get("task", "unknown"),
        "source_failure_meaning": rule_key,
        "source_failure_hypothesis": (
            asir_trace["failure_patches"][0].get("failure_hypothesis", asir_trace["failure_patches"][0].get("root_cause", "unmapped_failure"))
            if asir_trace.get("failure_patches")
            else "no_failure_hypothesis_required"
        ),
        "transfer_claim": "AS-IR transfers interaction meaning, not raw trajectory parameters.",
        "not_transferred": [
            "joint_trajectory",
            "absolute_grip_force",
            "source_contact_position",
        ],
        "domain_invariant_meaning": asir_trace.get("transferability", {}).get(
            "domain_invariant", []
        ),
        "robots": {},
    }

    for robot_id, profile in robot_profiles.items():
        robot_patch = adapt_patch_for_robot(asir_trace, robot_id, profile)
        transfer_result["robots"][robot_id] = robot_patch

    return transfer_result
