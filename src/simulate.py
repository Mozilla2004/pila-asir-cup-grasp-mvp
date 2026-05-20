"""Generate simulated pick-up-cup trajectories (failure + success)."""

import numpy as np

# Fixed seed for reproducibility
SEED = 42
RNG = np.random.default_rng(SEED)

N_STEPS = 60


def _noise(rng: np.random.Generator, size: int, scale: float = 0.01) -> np.ndarray:
    return rng.normal(0, scale, size)


def generate_failure_trajectory(
    run_id: str = "R001",
    scenario: str = "cup_grasp_low_friction",
    friction_level: float = 0.25,
) -> dict:
    """Generate a trajectory where the cup slips due to low grip force."""
    rng = np.random.default_rng(SEED)
    t = np.arange(N_STEPS, dtype=float)

    # P1: approach (0-14) — gripper moves toward cup
    gripper_distance = np.empty(N_STEPS)
    gripper_distance[:15] = np.linspace(0.30, 0.05, 15) + _noise(rng, 15, 0.003)

    # P2: align (15-24)
    gripper_distance[15:25] = np.linspace(0.05, 0.02, 10) + _noise(rng, 10, 0.002)

    # P3: contact (25-34)
    gripper_distance[25:35] = np.linspace(0.02, 0.00, 10) + _noise(rng, 10, 0.001)

    # P4: grasp (35-44)
    gripper_distance[35:45] = 0.0

    # P5: lift (45-59)
    gripper_distance[45:] = 0.0

    # contact_force — rises at contact, stays during grasp, drops during slip
    contact_force = np.zeros(N_STEPS)
    contact_force[25:35] = np.linspace(0.0, 2.5, 10) + _noise(rng, 10, 0.05)
    contact_force[35:45] = 2.5 + _noise(rng, 10, 0.1)
    contact_force[45:52] = np.linspace(2.5, 1.2, 7) + _noise(rng, 7, 0.1)
    contact_force[52:] = np.linspace(1.2, 0.3, 8) + _noise(rng, 8, 0.05)

    # grip_force — insufficient
    grip_force = np.zeros(N_STEPS)
    grip_force[35:45] = np.linspace(0.0, 3.0, 10) + _noise(rng, 10, 0.05)
    grip_force[45:] = 3.0 + _noise(rng, 15, 0.05)  # too low to hold

    # slip_score — rises during grasp/lift
    slip_score = np.zeros(N_STEPS)
    slip_score[35:45] = np.linspace(0.0, 0.55, 10) + np.abs(_noise(rng, 10, 0.02))
    slip_score[45:52] = np.linspace(0.55, 0.78, 7) + np.abs(_noise(rng, 7, 0.02))
    slip_score[52:] = np.linspace(0.78, 0.88, 8) + np.abs(_noise(rng, 8, 0.02))
    slip_score = np.clip(slip_score, 0, 1)

    # cup_height — lifts a bit then drops
    cup_height = np.zeros(N_STEPS)
    cup_height[:45] = 0.0
    cup_height[45:52] = np.linspace(0.0, 0.06, 7) + _noise(rng, 7, 0.002)
    cup_height[52:] = np.linspace(0.06, 0.01, 8) + _noise(rng, 8, 0.002)

    # cup_tilt — increases as cup slips
    cup_tilt = np.zeros(N_STEPS)
    cup_tilt[45:52] = np.linspace(0.0, 8.0, 7) + np.abs(_noise(rng, 7, 0.3))
    cup_tilt[52:] = np.linspace(8.0, 15.0, 8) + np.abs(_noise(rng, 8, 0.5))

    # phase_hint
    phase_hint = (
        ["approach"] * 15
        + ["align"] * 10
        + ["contact"] * 10
        + ["grasp"] * 10
        + ["lift"] * 15
    )

    return {
        "run_metadata": {
            "run_id": run_id,
            "scenario": scenario,
            "friction_level": friction_level,
            "patch_applied": False,
            "applied_patch_id": None,
        },
        "time": t.tolist(),
        "gripper_distance": np.round(gripper_distance, 5).tolist(),
        "contact_force": np.round(contact_force, 4).tolist(),
        "grip_force": np.round(grip_force, 4).tolist(),
        "cup_height": np.round(cup_height, 5).tolist(),
        "cup_tilt": np.round(cup_tilt, 3).tolist(),
        "slip_score": np.round(slip_score, 4).tolist(),
        "phase_hint": phase_hint,
        "success": False,
    }


def generate_success_trajectory(
    patch: dict | None = None,
    run_id: str = "R002",
    scenario: str = "cup_grasp_low_friction",
    friction_level: float = 0.25,
) -> dict:
    """Generate a trajectory with patch applied — reads patch content."""
    rng = np.random.default_rng(SEED + 1)
    t = np.arange(N_STEPS, dtype=float)

    # Read patch content to determine trajectory parameters
    grip_force_target = 3.0  # default (insufficient)
    slip_score_scale = 1.0   # default
    patch_applied = False
    applied_patch_id = None

    if patch:
        patch_applied = True
        applied_patch_id = patch.get("patch_id", "unknown")
        actions = patch.get("patch", {})
        if actions.get("adjust_force") == "increase_grip_force":
            grip_force_target = 6.5
        if actions.get("adjust_contact") == "shift_contact_position":
            slip_score_scale = 0.3

    # Same approach, align, contact phases
    gripper_distance = np.empty(N_STEPS)
    gripper_distance[:15] = np.linspace(0.30, 0.05, 15) + _noise(rng, 15, 0.003)
    gripper_distance[15:25] = np.linspace(0.05, 0.02, 10) + _noise(rng, 10, 0.002)
    gripper_distance[25:35] = np.linspace(0.02, 0.00, 10) + _noise(rng, 10, 0.001)
    gripper_distance[35:] = 0.0

    # contact_force — stable
    contact_force = np.zeros(N_STEPS)
    contact_force[25:35] = np.linspace(0.0, 2.8, 10) + _noise(rng, 10, 0.05)
    contact_force[35:45] = 2.8 + _noise(rng, 10, 0.08)
    contact_force[45:] = 2.8 + _noise(rng, 15, 0.08)

    # grip_force — driven by patch
    grip_force = np.zeros(N_STEPS)
    grip_force[35:45] = np.linspace(0.0, grip_force_target, 10) + _noise(rng, 10, 0.05)
    grip_force[45:] = grip_force_target + _noise(rng, 15, 0.05)

    # slip_score — scaled by patch
    slip_score = np.zeros(N_STEPS)
    slip_score[35:45] = np.linspace(0.0, 0.08 * slip_score_scale, 10) + np.abs(_noise(rng, 10, 0.01))
    slip_score[45:] = np.linspace(0.08 * slip_score_scale, 0.15 * slip_score_scale, 15) + np.abs(_noise(rng, 15, 0.01))
    slip_score = np.clip(slip_score, 0, 1)

    # cup_height — stable rise
    cup_height = np.zeros(N_STEPS)
    cup_height[:45] = 0.0
    cup_height[45:] = np.linspace(0.0, 0.22, 15) + _noise(rng, 15, 0.002)

    # cup_tilt — stays small
    cup_tilt = np.zeros(N_STEPS)
    cup_tilt[45:] = np.linspace(0.0, 4.0, 15) + np.abs(_noise(rng, 15, 0.2))

    phase_hint = (
        ["approach"] * 15
        + ["align"] * 10
        + ["contact"] * 10
        + ["grasp"] * 10
        + ["lift"] * 15
    )

    # Determine success based on patch
    success = patch_applied and grip_force_target > 5.0

    return {
        "run_metadata": {
            "run_id": run_id,
            "scenario": scenario,
            "friction_level": friction_level,
            "patch_applied": patch_applied,
            "applied_patch_id": applied_patch_id,
        },
        "time": t.tolist(),
        "gripper_distance": np.round(gripper_distance, 5).tolist(),
        "contact_force": np.round(contact_force, 4).tolist(),
        "grip_force": np.round(grip_force, 4).tolist(),
        "cup_height": np.round(cup_height, 5).tolist(),
        "cup_tilt": np.round(cup_tilt, 3).tolist(),
        "slip_score": np.round(slip_score, 4).tolist(),
        "phase_hint": phase_hint,
        "success": success,
    }
