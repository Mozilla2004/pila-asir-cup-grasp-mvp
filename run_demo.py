"""AS-IR Cup-Grasp MVP v0.3 — single-command demo runner."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.simulate import generate_failure_trajectory, generate_success_trajectory
from src.asir_extract import extract_asir_trace
from src.patch_policy import extract_patch, validate_patch, generate_patch_report
from src.cross_embodiment import load_robot_profiles, run_cross_embodiment_transfer
from src.report import plot_trajectories, generate_html_report

OUTPUTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
ASSETS = os.path.join(OUTPUTS, "assets")


def save_json(data: dict, filename: str) -> str:
    path = os.path.join(OUTPUTS, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def main() -> None:
    os.makedirs(ASSETS, exist_ok=True)

    print("[1/9] Generating failure trajectory...")
    failure_traj = generate_failure_trajectory(
        run_id="R001",
        scenario="cup_grasp_low_friction",
        friction_level=0.25,
    )
    save_json(failure_traj, "raw_trajectory_failure.json")

    print("[2/9] Extracting AS-IR trace (failure)...")
    failure_trace = extract_asir_trace(failure_traj)
    save_json(failure_trace, "asir_trace_failure.json")

    print("[3/9] Extracting failure patch...")
    patch = extract_patch(failure_trace)

    print("[4/9] Generating patched success trajectory...")
    success_traj = generate_success_trajectory(
        patch=patch,
        run_id="R002",
        scenario="cup_grasp_low_friction",
        friction_level=0.25,
    )
    save_json(success_traj, "raw_trajectory_success.json")

    print("[5/9] Extracting AS-IR trace (success)...")
    success_trace = extract_asir_trace(success_traj)
    validated_patch = validate_patch(patch, success_trace) if patch else {}
    save_json(success_trace, "asir_trace_success.json")

    # Generate patch report
    patch_md = generate_patch_report(failure_trace, success_trace, validated_patch)
    with open(os.path.join(OUTPUTS, "patch_report.md"), "w", encoding="utf-8") as f:
        f.write(patch_md)

    print("[6/9] Running cross-embodiment transfer...")
    robot_profiles = load_robot_profiles()
    ce_transfer = run_cross_embodiment_transfer(failure_trace, robot_profiles)
    save_json(ce_transfer, "cross_embodiment_transfer.json")

    print("[7/9] Generating trajectory plot...")
    plot_path = os.path.join(ASSETS, "trajectory_plot.png")
    plot_trajectories(failure_traj, success_traj, plot_path)

    print("[8/9] Generating HTML report...")
    generate_html_report(
        failure_traj=failure_traj,
        success_traj=success_traj,
        failure_trace=failure_trace,
        success_trace=success_trace,
        patch=validated_patch,
        plot_rel_path="assets/trajectory_plot.png",
        output_path=os.path.join(OUTPUTS, "asir_mvp_report.html"),
        cross_embodiment_transfer=ce_transfer,
    )

    print("[9/9] Done.")
    print()
    print("Outputs:")
    for f in sorted(os.listdir(OUTPUTS)):
        if f == "assets":
            for af in sorted(os.listdir(os.path.join(OUTPUTS, "assets"))):
                print(f"  outputs/assets/{af}")
        else:
            print(f"  outputs/{f}")
    print()
    print("Open this file in a browser:")
    print(f"  {os.path.join(OUTPUTS, 'asir_mvp_report.html')}")


if __name__ == "__main__":
    main()
