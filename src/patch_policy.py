"""Generate failure patches from AS-IR traces and produce patch reports."""

from __future__ import annotations


def extract_patch(asir_trace: dict) -> dict:
    """Extract the first failure patch from an AS-IR trace."""
    patches = asir_trace.get("failure_patches", [])
    if not patches:
        return {}
    return patches[0]


def validate_patch(patch: dict, success_trace: dict) -> dict:
    """Mark a patch as passed if the success trace confirms it worked."""
    result = dict(patch)
    result["validation_status"] = "passed" if success_trace.get("success", True) else "failed"
    return result


def generate_patch_report(
    failure_trace: dict, success_trace: dict, patch: dict
) -> str:
    """Generate a markdown patch report (v0.5)."""
    lines = [
        "# AS-IR Failure Hypothesis and Patch Suggestion Report (v0.5)",
        "",
        "## Failure Hypothesis",
        "",
    ]

    if patch:
        relation_delta = patch.get("relation_delta", {})
        relation_str = (
            " -> ".join(relation_delta["support"])
            if isinstance(relation_delta, dict) and "support" in relation_delta
            else str(relation_delta)
        )
        # Handle both old (root_cause string) and new (failure_hypothesis object) formats
        hypothesis = patch.get('failure_hypothesis', patch.get('root_cause', 'unknown'))
        if isinstance(hypothesis, dict):
            hypothesis_text = hypothesis.get('primary', 'unknown')
            confidence = hypothesis.get('confidence', 'unknown')
            hypothesis_display = f"{hypothesis_text} (confidence: {confidence})"
        else:
            hypothesis_text = hypothesis
            hypothesis_display = str(hypothesis)

        lines += [
            f"- **Patch ID**: {patch.get('patch_id', '?')}",
            f"- **Failure type**: {patch['failure_type']}",
            f"- **Failure hypothesis**: {hypothesis_display}",
            f"- **Relation delta**: {relation_str}",
            f"- **Validation status**: {patch.get('validation_status', 'pending')}",
            "",
            "## Patch Suggestion and Validation",
            "",
            f"- **Force adjustment**: {patch['patch']['adjust_force']}",
            f"- **Contact adjustment**: {patch['patch']['adjust_contact']}",
            f"- **Restart from phase**: {patch['patch']['restart_from_phase']}",
            "",
        ]

    # Compare phases
    lines += [
        "## Phase Comparison (Failure vs Patched)",
        "",
        "| Phase | Failure Status | Patched Status |",
        "|-------|---------------|----------------|",
    ]
    for fp, sp in zip(failure_trace["phases"], success_trace["phases"]):
        lines.append(f"| {fp['id']} ({fp['type']}) | {fp['status']} | {sp['status']} |")

    lines += [
        "",
        "## Physical Invariants",
        "",
    ]
    for fi, si in zip(
        failure_trace["runtime"]["physical_invariants"],
        success_trace["runtime"]["physical_invariants"],
    ):
        lines.append(
            f"- **{fi['name']}**: {fi['status']} -> {si['status']}"
        )

    lines += [
        "",
        "## Risk Policy",
        "",
        f"- Failure run: **{failure_trace['runtime']['risk_policy']['level']}** — {failure_trace['runtime']['risk_policy']['reason']}",
        f"- Patched run: **{success_trace['runtime']['risk_policy']['level']}** — {success_trace['runtime']['risk_policy']['reason']}",
        "",
    ]

    # Learning update
    lu = success_trace.get("learning_update", {})
    if lu.get("updated"):
        lines += [
            "## Learning Update",
            "",
            f"- Patch **{lu.get('patch_validated', '?')}** validated.",
            f"- {lu['notes'][0]}" if lu.get("notes") else "",
            "",
        ]

    return "\n".join(lines)
