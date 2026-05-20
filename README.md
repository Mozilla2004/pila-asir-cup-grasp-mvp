# PILa / AS-IR Cup-Grasp MVP

A minimal research prototype for Physical Interaction Language (PILa)
and Action-State Intermediate Representation (AS-IR).

This demo illustrates how raw robot trajectory data can be transformed
into structured physical interaction traces, including phases,
physical relations, failure patches, learning updates, and
cross-embodiment meaning transfer.

**这是一个面向具身智能的最小概念样机，用于演示：**
**原始轨迹数据不仅可以记录"机器人做了什么"，还可以被转化为**
**"物理交互中发生了什么"的结构化表示。**

## Architecture Overview

### Why Embodied Intelligence Needs Physical Interaction Language
![AS-IR Overview](assets/figures/AS-IR-overview-why-physical-interaction-language.png)

### Three-Layer, 18-Module Architecture
![AS-IR Architecture](assets/figures/AS-IR-architecture-3-layers-18-modules.png)

### Closed-Loop Runtime System
![AS-IR Runtime](assets/figures/AS-IR-closed-loop-runtime.png)

## What This Demo Tests

**Version**: v0.4.0

This demo tests the starting hypothesis of PILa:

> Raw robot trajectories record **what the robot did**, while PILa uses AS-IR to represent **what happened in the physical interaction**.

It does **not** prove PILa solves embodied intelligence. It only tests whether a physical interaction language, implemented through AS-IR, can make failure diagnosis, repair, and learning update more explicit than raw trajectory alone.

**v0.3 adds cross-embodiment meaning transfer:**
the same AS-IR failure trace is interpreted by different robot morphologies (two-finger, three-finger, suction) and re-instantiated into robot-specific patches.

**v0.3.2 adds interactive animations:**
three lightweight CSS/JS animations in the HTML report illustrating the physical interaction timeline, the raw-to-ASIR meaning extraction process, and the cross-embodiment transfer flow.

**v0.3.3 adds bilingual HTML report support:**
- English / 中文 toggle button (top-right)
- Local language preference via localStorage
- Bilingual section headings, explanations, tables and animation labels

The report defaults to English. Use the top-right language switcher to view the Chinese version.

报告默认英文显示，可通过右上角按钮切换为中文。

**v0.4.0 terminology upgrade + animation fix + improved explanations:**

- Renamed the public-facing language to PILa (Physical Interaction Language / 物理交互语言)
- Kept AS-IR as the underlying intermediate representation layer
- Added a glossary explaining PILa, AS-IR, AS-IR Core, Runtime, Engineering Adapter and cross-embodiment meaning transfer
- Fixed physical interaction animation: Patched Lift visually lifts cup, Cup slips shows rotation
- **Improved explanation for Raw Trajectory: Failure vs Patched Run**, clarifying the difference between signal-level changes and AS-IR/PILa structural interpretation with bilingual insight cards

## How to Run

```bash
pip install -r requirements.txt
python run_demo.py
```

Then open:

```
outputs/asir_mvp_report.html
```

## Outputs

| File | Description |
|------|-------------|
| `raw_trajectory_failure.json` | Simulated trajectory — cup slips and falls |
| `raw_trajectory_success.json` | Simulated trajectory — patched, successful grasp |
| `asir_trace_failure.json` | AS-IR structured trace for the failure run |
| `asir_trace_success.json` | AS-IR structured trace for the patched run |
| `patch_report.md` | Markdown report of failure diagnosis and repair |
| `cross_embodiment_transfer.json` | Cross-embodiment meaning transfer output |
| `asir_mvp_report.html` | Full bilingual HTML report with plots, animations, and trace comparison |
| `assets/trajectory_plot.png` | Trajectory comparison plot (embedded in HTML) |

## What to Look For

1. **Raw trajectory** shows low-level signals (forces, distances, scores).
2. **AS-IR trace** explains phases, physical relations, and failure cause explicitly.
3. **Failure patch** identifies the root cause and proposes a repair strategy.
4. **Patched run** succeeds — demonstrating the patch is actionable.
5. **Learning update** records what was learned in structured metadata.
6. **Cross-embodiment transfer** shows the same failure meaning generates different patches for different robots.
7. **Interactive animations** illustrate the interaction timeline, meaning extraction, and cross-embodiment flow with Replay buttons.
8. **Bilingual toggle** switches the report between English and 中文 (Chinese).

## Project Structure

```
asir-cup-grasp-mvp/
├── run_demo.py              # Single-command runner
├── requirements.txt
├── README.md
├── robot_profiles.json      # Robot morphology definitions
├── assets/
│   └── figures/             # Architecture diagrams
│       ├── AS-IR-overview-why-physical-interaction-language.png
│       ├── AS-IR-architecture-3-layers-18-modules.png
│       └── AS-IR-closed-loop-runtime.png
├── src/
│   ├── simulate.py          # Trajectory generation (failure + success)
│   ├── asir_extract.py      # Raw trajectory → AS-IR trace
│   ├── patch_policy.py      # Failure patch extraction and report
│   ├── cross_embodiment.py  # Cross-embodiment meaning transfer
│   └── report.py            # HTML report + matplotlib plots + animations + bilingual
└── outputs/                 # Generated by run_demo.py
    ├── raw_trajectory_failure.json
    ├── raw_trajectory_success.json
    ├── asir_trace_failure.json
    ├── asir_trace_success.json
    ├── cross_embodiment_transfer.json
    ├── patch_report.md
    ├── asir_mvp_report.html
    └── assets/
        └── trajectory_plot.png
```

## Design Principles

- **No real robot needed** — pure Python simulation with fixed random seed
- **No training** — AS-IR extraction is rule-based, not learned
- **No external CDN** — HTML is self-contained, opens locally (animations use vanilla CSS/JS)
- **Reproducible** — `numpy.random.default_rng(42)` ensures same output every run
- **Minimal dependencies** — numpy, matplotlib, jinja2 only

## Roadmap

- Add 3-5 primitive manipulation tasks (pour, place, stack, flip, insert)
- Add AS-IR annotation quality score
- Compare raw trajectory training vs AS-IR-assisted training
- Connect to MuJoCo or Isaac Sim for real physics
- Export AS-IR traces as metadata for LeRobot-style datasets

## License

MIT
