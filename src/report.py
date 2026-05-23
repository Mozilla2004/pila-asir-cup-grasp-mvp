"""Generate HTML report and trajectory plot for the AS-IR MVP demo."""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def format_failure_hypothesis(patch: dict) -> str:
    """Format failure hypothesis for HTML display, handling both old and new formats."""
    hypothesis = patch.get('failure_hypothesis', patch.get('root_cause', 'unknown'))

    if isinstance(hypothesis, dict):
        # New format: structured failure hypothesis
        primary = hypothesis.get('primary', 'unknown')
        confidence = hypothesis.get('confidence', 'unknown')
        evidence = hypothesis.get('evidence', [])

        parts = [f"<strong>{primary}</strong>"]
        if confidence != 'unknown':
            parts.append(f"(confidence: {confidence})")
        if evidence:
            evidence_str = ", ".join(evidence[:2])  # Show first 2 evidence items
            if len(evidence) > 2:
                evidence_str += f" +{len(evidence)-2} more"
            parts.append(f"<br><small>Evidence: {evidence_str}</small>")

        return " ".join(parts)
    else:
        # Old format: simple string
        return str(hypothesis)


def plot_trajectories(
    failure: dict, success: dict, output_path: str
) -> None:
    """Plot failure vs success trajectories and save as PNG."""
    fig, axes = plt.subplots(3, 2, figsize=(12, 10), sharex=True)
    fig.suptitle("Raw Trajectory: Failure vs Patched Run", fontsize=14, fontweight="bold")

    fields = [
        ("gripper_distance", "Gripper Distance (m)"),
        ("grip_force", "Grip Force (N)"),
        ("slip_score", "Slip Score"),
        ("cup_tilt", "Cup Tilt (deg)"),
        ("cup_height", "Cup Height (m)"),
        ("contact_force", "Contact Force (N)"),
    ]

    for ax, (key, label) in zip(axes.flat, fields):
        ax.plot(failure["time"], failure[key], color="#e74c3c", label="Failure", linewidth=1.5)
        ax.plot(success["time"], success[key], color="#27ae60", label="Patched", linewidth=1.5)
        ax.set_ylabel(label, fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Phase boundary lines
        for boundary in [15, 25, 35, 45]:
            ax.axvline(x=boundary, color="gray", linestyle=":", alpha=0.4)

    # Add phase labels on top
    phase_labels = [("P1\nApproach", 7), ("P2\nAlign", 20), ("P3\nContact", 30),
                    ("P4\nGrasp", 40), ("P5\nLift", 52)]
    for label, x in phase_labels:
        axes[0, 0].text(x, max(failure["gripper_distance"]) * 1.05, label,
                        ha="center", fontsize=7, color="gray")

    axes[-1, 0].set_xlabel("Time Step")
    axes[-1, 1].set_xlabel("Time Step")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _render_phases(phases: list[dict]) -> str:
    """Render phases as HTML cards."""
    status_colors = {
        "success": "#27ae60",
        "warning": "#f39c12",
        "failure": "#e74c3c",
        "anomaly": "#e67e22",
        "unknown": "#95a5a6",
    }
    risk_badges = {
        "GREEN": ("#d4edda", "#27ae60"),
        "YELLOW": ("#fff3cd", "#f39c12"),
        "ORANGE": ("#f8d7da", "#e74c3c"),
    }
    rows = []
    for p in phases:
        color = status_colors.get(p["status"], "#95a5a6")
        risk = p.get("risk", "GREEN")
        bg, fg = risk_badges.get(risk, ("#eee", "#333"))
        evidence_items = "".join(
            f"<li>{k}: <code>{v}</code></li>"
            for k, v in p.get("evidence", {}).items()
        )
        rows.append(
            f'<div style="border-left:4px solid {color};padding:8px 12px;margin:4px 0;'
            f'background:#fafafa;border-radius:4px;">'
            f"<strong>{p['id']}</strong> &mdash; {p['type']} "
            f'<span style="color:{color};font-weight:bold;">[{p["status"].upper()}]</span> '
            f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:3px;font-size:0.8em;">{risk}</span>'
            f"<ul style='margin:4px 0 0 0;font-size:0.9em;'>{evidence_items}</ul>"
            f"</div>"
        )
    return "".join(rows)


def _render_relations(relations: list[dict]) -> str:
    rows = []
    for r in relations:
        reason = f" ({r['reason']})" if "reason" in r else ""
        color = "#27ae60" if r["state"] in ("established", "stable") else "#e74c3c"
        rows.append(
            f"<li><strong>{r['type']}</strong>: "
            f'<span style="color:{color};">{r["state"]}</span>{reason}</li>'
        )
    return "<ul>" + "".join(rows) + "</ul>"


def _render_invariants(invariants: list[dict]) -> str:
    rows = []
    for inv in invariants:
        color = "#27ae60" if inv["status"] == "satisfied" else "#e74c3c"
        rows.append(
            f"<li><code>{inv['name']}</code>: "
            f'<span style="color:{color};">{inv["status"]}</span></li>'
        )
    return "<ul>" + "".join(rows) + "</ul>"


def _build_interaction_flow(failure_trace: dict, success_trace: dict, patch: dict) -> str:
    """Build the AS-IR interaction flow card: Intent -> P1 -> ... -> Patch -> Success."""
    status_colors = {
        "success": "#27ae60",
        "warning": "#f39c12",
        "failure": "#e74c3c",
    }
    risk_badges = {
        "GREEN": ("#d4edda", "#27ae60"),
        "YELLOW": ("#fff3cd", "#f39c12"),
        "ORANGE": ("#f8d7da", "#e74c3c"),
    }

    nodes = [
        '<span style="background:#e7f5ff;padding:4px 10px;border-radius:4px;font-weight:bold;">Intent</span>',
    ]

    for p in failure_trace["phases"]:
        color = status_colors.get(p["status"], "#95a5a6")
        risk = p.get("risk", "GREEN")
        bg, fg = risk_badges.get(risk, ("#eee", "#333"))
        nodes.append(
            f'<span style="border:2px solid {color};padding:4px 10px;border-radius:4px;">'
            f'{p["id"]} {p["type"]} '
            f'<span style="color:{color};font-weight:bold;">{p["status"]}</span> '
            f'<span style="background:{bg};color:{fg};padding:1px 5px;border-radius:2px;font-size:0.75em;">{risk}</span>'
            f'</span>'
        )

    # Patch node
    if patch:
        pid = patch.get("patch_id", "?")
        nodes.append(
            f'<span style="background:#fff3cd;border:2px solid #ffc107;padding:4px 10px;'
            f'border-radius:4px;font-weight:bold;">Patch {pid}</span>'
        )

    # Success node
    nodes.append(
        '<span style="background:#d4edda;border:2px solid #27ae60;padding:4px 10px;'
        'border-radius:4px;font-weight:bold;">Patched Success</span>'
    )

    arrows = " &rarr; ".join(nodes)
    return (
        f'<div style="padding:20px;background:#f8f9fa;border-radius:8px;'
        f'border:1px solid #dee2e6;line-height:2.5;">'
        f'{arrows}</div>'
    )


def _build_raw_vs_asir_table() -> str:
    """Build the Raw vs AS-IR comparison table with bilingual support."""
    rows = [
        ("What is recorded?", "记录了什么？",
         "Joint angles, force values, distances", "关节角度、力值、距离",
         "Intent, phases, relations, invariants", "意图、阶段、关系、不变量"),
        ("Can identify phase?", "能否识别阶段？",
         "No — must be inferred from signal changes", "不能——需要从信号变化中推断",
         "Yes — explicit phase labels with status", "能——显式阶段标签与状态"),
        ("Can diagnose failure?", "能否诊断失败？",
         "Partially — high slip_score visible", "部分——能看到高滑移分数",
         "Yes — root cause, relation delta, violated invariant", "能——根因、关系退化、违反的不变量"),
        ("Can generate repair?", "能否生成修复？",
         "No — only data, no structure", "不能——只有数据没有结构",
         "Yes — actionable patch with restart point", "能——可操作补丁与重启点"),
        ("Can track learning?", "能否追踪学习？",
         "No — each run is isolated", "不能——每次执行是孤立的",
         "Yes — learning_update records validated patches", "能——learning_update 记录已验证补丁"),
        ("Per-phase risk?", "逐阶段风险？",
         "No — single global view", "不能——只有全局视角",
         "Yes — GREEN / YELLOW / ORANGE per phase", "能——每阶段 GREEN / YELLOW / ORANGE"),
        ("Transferable?", "可迁移？",
         "No — raw values are embodiment-specific", "不能——原始值绑定具体本体",
         "Partially — domain-invariant vs domain-specific split", "部分——域不变与域特定分离"),
    ]
    table_rows = ""
    for q_en, q_zh, raw_en, raw_zh, asir_en, asir_zh in rows:
        table_rows += (
            f'<tr><td><strong><span data-en="{q_en}" data-zh="{q_zh}">{q_en}</span></strong></td>'
            f'<td><span data-en="{raw_en}" data-zh="{raw_zh}">{raw_en}</span></td>'
            f'<td><span data-en="{asir_en}" data-zh="{asir_zh}">{asir_en}</span></td></tr>'
        )
    return table_rows


def _build_representation_gain(rg: dict) -> str:
    """Render representation_gain as a bilingual table."""
    items = [
        ("Raw observables", "原始可观测量", ", ".join(f"<code>{x}</code>" for x in rg.get("raw_observables", []))),
        ("AS-IR structures", "AS-IR 结构", ", ".join(f"<code>{x}</code>" for x in rg.get("asir_structures", []))),
        ("Diagnosable failure", "可诊断失败", str(rg.get("diagnosable_failure", False))),
        ("Actionable patch", "可操作补丁", str(rg.get("actionable_patch", False))),
        ("Re-execution validated", "重执行已验证", str(rg.get("reexecution_validated", False))),
    ]
    rows = ""
    for label_en, label_zh, value in items:
        rows += (
            f'<tr><td><strong><span data-en="{label_en}" data-zh="{label_zh}">'
            f'{label_en}</span></strong></td><td>{value}</td></tr>'
        )
    return rows


def _build_cross_embodiment_section(ce_transfer: dict) -> str:
    """Build the cross-embodiment meaning transfer section with bilingual support."""
    robot_colors = {
        "two_finger_gripper": "#3498db",
        "three_finger_gripper": "#9b59b6",
        "suction_gripper": "#e67e22",
    }
    robot_names_zh = {
        "two_finger_gripper": "二指夹爪",
        "three_finger_gripper": "三指夹爪",
        "suction_gripper": "吸盘夹具",
    }
    cards = []
    for robot_id, robot_data in ce_transfer.get("robots", {}).items():
        color = robot_colors.get(robot_id, "#333")
        name_zh = robot_names_zh.get(robot_id, robot_id)
        actions = "".join(f"<li><code>{a}</code></li>" for a in robot_data.get("adapted_actions", []))
        interp = robot_data.get("meaning_interpretation", {})
        interp_html = ""
        if interp:
            interp_html = (
                f'<p><strong><span data-en="Shared meaning:" data-zh="共享意义：">Shared meaning:</span></strong> {interp.get("shared_meaning", "")}<br>'
                f'<strong><span data-en="Robot-specific reading:" data-zh="本体特有解读：">Robot-specific reading:</span></strong> <em>{interp.get("robot_specific_reading", "")}</em></p>'
            )
        cards.append(
            f'<div style="border:2px solid {color};padding:16px;border-radius:8px;margin:8px 0;'
            f'background:#fafafa;">'
            f'<h3 style="margin-top:0;color:{color};"><span data-en="{robot_id.replace("_", " ").title()}" data-zh="{name_zh}">{robot_id.replace("_", " ").title()}</span></h3>'
            f'<p><strong><span data-en="Morphology:" data-zh="本体形态：">Morphology:</span></strong> <code>{robot_data["morphology_type"]}</code><br>'
            f'<strong><span data-en="Contact model:" data-zh="接触模型：">Contact model:</span></strong> <code>{robot_data["contact_model"]}</code><br>'
            f'<strong><span data-en="Force control:" data-zh="力控制：">Force control:</span></strong> <code>{robot_data["force_control_mode"]}</code></p>'
            f'{interp_html}'
            f'<p><strong><span data-en="Adapted actions:" data-zh="适配动作：">Adapted actions:</span></strong></p><ul>{actions}</ul>'
            f'<p><strong><span data-en="Restart from:" data-zh="重启阶段：">Restart from:</span></strong> <code>{robot_data["restart_from_phase"]}</code></p>'
            f'</div>'
        )
    cards_html = "\n".join(cards)

    source = ce_transfer.get("source_root_cause", "unknown")
    # Handle both old (string) and new (failure_hypothesis object) formats
    if isinstance(source, dict):
        source = source.get('primary', str(source))
    domain_inv = ", ".join(
        f"<code>{x}</code>" for x in ce_transfer.get("domain_invariant_meaning", [])
    )
    not_transferred = ce_transfer.get("not_transferred", [])
    not_transferred_html = ", ".join(f"<code>{x}</code>" for x in not_transferred)
    transfer_claim = ce_transfer.get("transfer_claim", "")

    return f"""
<div class="card" style="border-left:4px solid #339af0;">
<p style="font-size:1.05em;">
<strong><span data-en="Raw trajectory is embodiment-specific; PILa expresses interaction meaning; AS-IR Core carries transferable structure; Engineering Adapter performs re-instantiation." data-zh="原始轨迹绑定具体本体；PILa 表达交互意义；AS-IR Core 承载可迁移结构；Engineering Adapter 负责重新实例化。">Raw trajectory is embodiment-specific; PILa expresses interaction meaning; AS-IR Core carries transferable structure; Engineering Adapter performs re-instantiation.</span></strong>
</p>
<p>{transfer_claim}</p>
</div>

<div class="card">
<p><strong><span data-en="Source failure meaning:" data-zh="源头失败意义：">Source failure meaning:</span></strong> <code>{source}</code><br>
<strong><span data-en="Domain-invariant meaning:" data-zh="域不变意义：">Domain-invariant meaning:</span></strong> {domain_inv}<br>
<strong><span data-en="Not transferred:" data-zh="未迁移：">Not transferred:</span></strong> {not_transferred_html}</p>
</div>

{cards_html}

<div class="card">
<p><strong><span data-en="What this shows:" data-zh="这说明了什么：">What this shows:</span></strong>
<span data-en="PILa captures a single interaction meaning via AS-IR (support relation degraded due to insufficient grip under low friction). Each robot&#39;s morphology adapter translates this meaning into its own executable actions. A two-finger gripper increases force; a three-finger gripper adds a contact point; a suction gripper increases vacuum pressure." data-zh="PILa 通过 AS-IR 捕获了单一交互意义（低摩擦下支撑关系因夹持力不足而退化）。每个机器人的本体适配器将此意义翻译为各自的执行动作。二指夹爪增加力；三指夹爪增加接触点；吸盘夹具增加真空度。">PILa captures a single interaction meaning via AS-IR (support relation degraded due to insufficient grip under low friction). Each robot's morphology adapter translates this meaning into its own executable actions. A two-finger gripper increases force; a three-finger gripper adds a contact point; a suction gripper increases vacuum pressure.</span></p>
<p class="note" style="background:#e7f5ff;border-left-color:#339af0;">
<span data-en="This is a minimal representation test for cross-embodiment meaning transfer. It does not prove real robot-to-robot transfer works." data-zh="这是一个跨本体意义迁移的最小表示测试，并不证明真实的机器人间迁移已经可行。">This is a minimal representation test for cross-embodiment meaning transfer. It does not prove real robot-to-robot transfer works.</span>
</p>
</div>
"""


def _render_interaction_animation() -> str:
    """Animation 1: Cup-Grasp Timeline — 2D CSS/JS showing the physical interaction."""
    return """
<div style="margin:16px 0;">
<button onclick="window.__asirTimelineRun()" style="padding:6px 16px;border-radius:4px;
border:1px solid #339af0;background:#fff;color:#339af0;cursor:pointer;font-size:0.9em;">
&#9654; Replay</button>
<div id="anim-timeline" style="position:relative;height:180px;background:#f8f9fa;
border-radius:8px;overflow:hidden;margin-top:8px;border:1px solid #dee2e6;">
  <!-- Table -->
  <div style="position:absolute;bottom:0;left:50%;transform:translateX(-50%);
  width:70%;height:12px;background:#868e96;border-radius:3px 3px 0 0;"></div>
  <!-- Cup -->
  <div id="anim-cup" style="position:absolute;bottom:12px;left:50%;
  transform:translateX(-50%);width:30px;height:40px;background:#dee2e6;
  border:2px solid #495057;border-radius:2px 2px 6px 6px;transition:transform 0.3s,opacity 0.3s;"></div>
  <!-- Gripper -->
  <div id="anim-gripper" style="position:absolute;top:20px;left:50%;
  transform:translateX(-50%);transition:top 0.5s;">
    <div style="width:4px;height:16px;background:#495057;position:absolute;left:-12px;top:0;"></div>
    <div style="width:4px;height:16px;background:#495057;position:absolute;right:-12px;top:0;"></div>
    <div style="width:32px;height:4px;background:#495057;position:absolute;top:0;left:-16px;"></div>
  </div>
  <!-- Phase label -->
  <div id="anim-phase-label" style="position:absolute;top:8px;left:12px;font-weight:bold;
  font-size:0.95em;color:#495057;">&mdash;</div>
  <!-- Risk badge -->
  <div id="anim-risk-badge" style="position:absolute;top:8px;right:12px;padding:2px 10px;
  border-radius:3px;font-size:0.85em;font-weight:bold;opacity:0;transition:opacity 0.3s;"></div>
  <!-- Slip indicator -->
  <div id="anim-slip-bar" style="position:absolute;bottom:16px;right:12px;width:8px;
  height:0px;background:#e74c3c;border-radius:4px;transition:height 0.4s;"></div>
  <div style="position:absolute;bottom:4px;right:8px;font-size:0.7em;color:#868e96;">slip</div>
</div>
<script>
(function(){
  var L={
    "P1 Approach":"P1 接近","P2 Align":"P2 对齐","P3 Contact":"P3 接触",
    "P4 Grasp":"P4 抓取","P5 Lift":"P5 提起","Cup slips!":"杯子滑落！",
    "Patch F1":"补丁 F1","Patched Lift":"补丁后提起",
    "YELLOW":"黄色 / 预警","ORANGE":"橙色 / 失败风险","GREEN":"绿色 / 稳定","FAILURE":"失败"
  };
  function t(s){var l=window.__asirLang||"en";return l==="zh"&&L[s]?L[s]:s;}
  var steps=[
    {label:"P1 Approach",risk:"",gripTop:20,cupY:0,cupRot:0,slip:0,dur:800},
    {label:"P2 Align",risk:"",gripTop:60,cupY:0,cupRot:0,slip:0,dur:600},
    {label:"P3 Contact",risk:"",gripTop:80,cupY:0,cupRot:0,slip:5,dur:600},
    {label:"P4 Grasp",risk:"YELLOW",riskBg:"#fff3cd",riskFg:"#f39c12",
     gripTop:95,cupY:0,cupRot:0,slip:30,dur:800},
    {label:"P5 Lift",risk:"ORANGE",riskBg:"#f8d7da",riskFg:"#e74c3c",
     gripTop:40,cupY:35,cupRot:10,slip:70,dur:800},
    {label:"Cup slips!",risk:"FAILURE",riskBg:"#e74c3c",riskFg:"#fff",
     gripTop:40,cupY:0,cupRot:22,slip:90,dur:1000},
    {label:"Patch F1",risk:"",gripTop:95,cupY:0,cupRot:0,slip:0,dur:600},
    {label:"Patched Lift",risk:"GREEN",riskBg:"#d4edda",riskFg:"#27ae60",
     gripTop:40,cupY:70,cupRot:0,slip:8,dur:1000}
  ];
  var running=false;
  function run(){
    if(running)return;running=true;
    var el=document.getElementById("anim-timeline");if(!el)return;
    var cup=document.getElementById("anim-cup");
    var grip=document.getElementById("anim-gripper");
    var pl=document.getElementById("anim-phase-label");
    var rb=document.getElementById("anim-risk-badge");
    var sb=document.getElementById("anim-slip-bar");
    cup.style.transform="translateX(-50%) translateY(0px)";
    cup.style.opacity="1";
    rb.style.opacity="0";sb.style.height="0px";
    var i=0;
    function next(){
      if(i>=steps.length){running=false;return;}
      var s=steps[i];
      pl.textContent=t(s.label);
      grip.style.top=s.gripTop+"px";
      cup.style.transform="translateX(-50%) translateY(-"+(s.cupY||0)+"px) rotate("+(s.cupRot||0)+"deg)";
      sb.style.height=s.slip+"px";
      if(s.risk){
        rb.textContent=t(s.risk);rb.style.background=s.riskBg;
        rb.style.color=s.riskFg;rb.style.opacity="1";
      }else{rb.style.opacity="0";}
      i++;
      setTimeout(next,s.dur);
    }
    next();
  }
  window.__asirTimelineRun=run;
  setTimeout(run,800);
})();
</script>
</div>"""


def _render_meaning_extraction_animation() -> str:
    """Animation 2: From Raw Signals to AS-IR Structure — sequential lighting."""
    return """
<div style="margin:16px 0;">
<button onclick="window.__asirExtractRun()" style="padding:6px 16px;border-radius:4px;
border:1px solid #339af0;background:#fff;color:#339af0;cursor:pointer;font-size:0.9em;">
&#9654; Replay</button>
<div id="anim-extract" style="display:flex;align-items:flex-start;gap:12px;margin-top:8px;
flex-wrap:wrap;">
  <!-- Left: Raw signals -->
  <div style="flex:0 0 160px;">
    <div style="font-weight:bold;margin-bottom:6px;color:#868e96;font-size:0.9em;"><span data-en="Raw Signals" data-zh="原始信号">Raw Signals</span></div>
    <div class="anim-raw-item" style="padding:6px 10px;margin:3px 0;background:#f1f3f5;
    border-radius:4px;font-size:0.85em;opacity:0.3;transition:opacity 0.4s;">grip_force</div>
    <div class="anim-raw-item" style="padding:6px 10px;margin:3px 0;background:#f1f3f5;
    border-radius:4px;font-size:0.85em;opacity:0.3;transition:opacity 0.4s;">slip_score</div>
    <div class="anim-raw-item" style="padding:6px 10px;margin:3px 0;background:#f1f3f5;
    border-radius:4px;font-size:0.85em;opacity:0.3;transition:opacity 0.4s;">cup_tilt</div>
    <div class="anim-raw-item" style="padding:6px 10px;margin:3px 0;background:#f1f3f5;
    border-radius:4px;font-size:0.85em;opacity:0.3;transition:opacity 0.4s;">contact_force</div>
    <div class="anim-raw-item" style="padding:6px 10px;margin:3px 0;background:#f1f3f5;
    border-radius:4px;font-size:0.85em;opacity:0.3;transition:opacity 0.4s;">cup_height</div>
  </div>
  <!-- Arrow -->
  <div id="anim-extract-arrow" style="flex:0 0 60px;text-align:center;padding-top:40px;
  font-size:2em;color:#dee2e6;transition:color 0.4s;">&#10132;</div>
  <!-- Right: AS-IR structures -->
  <div style="flex:1;min-width:180px;">
    <div style="font-weight:bold;margin-bottom:6px;color:#868e96;font-size:0.9em;"><span data-en="AS-IR Structures" data-zh="AS-IR 结构">AS-IR Structures</span></div>
    <div class="anim-asir-item" style="padding:6px 10px;margin:3px 0;background:#f1f3f5;
    border-left:3px solid transparent;border-radius:4px;font-size:0.85em;
    opacity:0.3;transition:all 0.5s;">
      <strong><span data-en="Intent" data-zh="意图">Intent</span></strong> &mdash; <span data-en="goal + constraints" data-zh="目标 + 约束">goal + constraints</span></div>
    <div class="anim-asir-item" style="padding:6px 10px;margin:3px 0;background:#f1f3f5;
    border-left:3px solid transparent;border-radius:4px;font-size:0.85em;
    opacity:0.3;transition:all 0.5s;">
      <strong><span data-en="5 Phases" data-zh="5 个阶段">5 Phases</span></strong> &mdash; <span data-en="status + risk per phase" data-zh="每阶段状态 + 风险">status + risk per phase</span></div>
    <div class="anim-asir-item" style="padding:6px 10px;margin:3px 0;background:#f1f3f5;
    border-left:3px solid transparent;border-radius:4px;font-size:0.85em;
    opacity:0.3;transition:all 0.5s;">
      <strong><span data-en="Relations" data-zh="物理关系">Relations</span></strong> &mdash; <span data-en="proximity, contact, support" data-zh="接近、接触、支撑">proximity, contact, support</span></div>
    <div class="anim-asir-item" style="padding:6px 10px;margin:3px 0;background:#f1f3f5;
    border-left:3px solid transparent;border-radius:4px;font-size:0.85em;
    opacity:0.3;transition:all 0.5s;">
      <strong><span data-en="Risk Policy" data-zh="风险策略">Risk Policy</span></strong> &mdash; <span data-en="GREEN / YELLOW / ORANGE" data-zh="绿色 / 黄色 / 橙色">GREEN / YELLOW / ORANGE</span></div>
    <div class="anim-asir-item" style="padding:6px 10px;margin:3px 0;background:#f1f3f5;
    border-left:3px solid transparent;border-radius:4px;font-size:0.85em;
    opacity:0.3;transition:all 0.5s;">
      <strong><span data-en="Failure Patch" data-zh="失败补丁">Failure Patch</span></strong> &mdash; <span data-en="root cause + repair" data-zh="根因 + 修复">root cause + repair</span></div>
  </div>
</div>
<script>
(function(){
  var colors=["#339af0","#27ae60","#e67e22","#f39c12","#e74c3c"];
  function run(){
    var container=document.getElementById("anim-extract");if(!container)return;
    var raws=container.querySelectorAll(".anim-raw-item");
    var asirs=container.querySelectorAll(".anim-asir-item");
    var arrow=document.getElementById("anim-extract-arrow");
    for(var i=0;i<raws.length;i++){raws[i].style.opacity="0.3";}
    for(var i=0;i<asirs.length;i++){
      asirs[i].style.opacity="0.3";asirs[i].style.borderLeftColor="transparent";
    }
    arrow.style.color="#dee2e6";
    /* Light raw signals */
    var delay=0;
    for(var i=0;i<raws.length;i++){
      (function(el,d){setTimeout(function(){el.style.opacity="1";},d);})(raws[i],delay);
      delay+=200;
    }
    /* Light arrow */
    setTimeout(function(){arrow.style.color="#339af0";},delay);
    delay+=400;
    /* Light AS-IR items */
    for(var i=0;i<asirs.length;i++){
      (function(el,c,d){
        setTimeout(function(){
          el.style.opacity="1";el.style.borderLeftColor=c;
          el.style.background="#f8f9fa";
        },d);
      })(asirs[i],colors[i],delay);
      delay+=800;
    }
  }
  window.__asirExtractRun=run;
  setTimeout(run,1200);
})();
</script>
</div>"""


def _render_cross_embodiment_animation() -> str:
    """Animation 3: Cross-embodiment transfer — central meaning flows to 3 robots."""
    return """
<div style="margin:16px 0;">
<button onclick="window.__asirCrossRun()" style="padding:6px 16px;border-radius:4px;
border:1px solid #339af0;background:#fff;color:#339af0;cursor:pointer;font-size:0.9em;">
&#9654; Replay</button>
<div id="anim-cross" style="text-align:center;margin-top:12px;">
  <!-- Central meaning card -->
  <div id="anim-meaning-card" style="display:inline-block;padding:14px 24px;
  background:#e7f5ff;border:2px solid #339af0;border-radius:8px;font-weight:bold;
  font-size:0.95em;opacity:0.3;transition:opacity 0.6s;">
    AS-IR Meaning<br><span style="font-size:0.8em;font-weight:normal;color:#495057;">
    support_degraded / low_friction_slip</span>
  </div>
  <!-- SVG arrows + robot cards -->
  <svg id="anim-cross-svg" width="100%" height="120" style="display:block;margin:0 auto;
  max-width:600px;overflow:visible;">
    <line id="anim-line-2f" x1="50%" y1="0" x2="17%" y2="80" stroke="#3498db"
    stroke-width="2" stroke-dasharray="5,5" opacity="0" style="transition:opacity 0.5s;"/>
    <line id="anim-line-3f" x1="50%" y1="0" x2="50%" y2="80" stroke="#9b59b6"
    stroke-width="2" stroke-dasharray="5,5" opacity="0" style="transition:opacity 0.5s;"/>
    <line id="anim-line-su" x1="50%" y1="0" x2="83%" y2="80" stroke="#e67e22"
    stroke-width="2" stroke-dasharray="5,5" opacity="0" style="transition:opacity 0.5s;"/>
  </svg>
  <div style="display:flex;justify-content:center;gap:16px;flex-wrap:wrap;">
    <div class="anim-robot-card" style="flex:0 0 160px;padding:12px;border:2px solid #3498db;
    border-radius:8px;background:#f8f9fa;opacity:0.2;transition:opacity 0.5s;text-align:left;">
      <div style="font-weight:bold;color:#3498db;margin-bottom:4px;"><span data-en="Two-Finger" data-zh="二指夹爪">Two-Finger</span></div>
      <div style="font-size:0.8em;"><span data-en="increase normal force, shift contact region" data-zh="增加法向力，调整接触区域">increase normal force<br>shift contact region</span></div>
    </div>
    <div class="anim-robot-card" style="flex:0 0 160px;padding:12px;border:2px solid #9b59b6;
    border-radius:8px;background:#f8f9fa;opacity:0.2;transition:opacity 0.5s;text-align:left;">
      <div style="font-weight:bold;color:#9b59b6;margin-bottom:4px;"><span data-en="Three-Finger" data-zh="三指夹爪">Three-Finger</span></div>
      <div style="font-size:0.8em;"><span data-en="activate 3rd finger, redistribute forces" data-zh="激活第三指，重新分配力">activate 3rd finger<br>redistribute forces</span></div>
    </div>
    <div class="anim-robot-card" style="flex:0 0 160px;padding:12px;border:2px solid #e67e22;
    border-radius:8px;background:#f8f9fa;opacity:0.2;transition:opacity 0.5s;text-align:left;">
      <div style="font-weight:bold;color:#e67e22;margin-bottom:4px;"><span data-en="Suction" data-zh="吸盘夹具">Suction</span></div>
      <div style="font-size:0.8em;"><span data-en="increase vacuum, reduce acceleration" data-zh="增加真空度，降低加速度">increase vacuum<br>reduce acceleration</span></div>
    </div>
  </div>
</div>
<script>
(function(){
  function run(){
    var card=document.getElementById("anim-meaning-card");if(!card)return;
    var cards=document.querySelectorAll(".anim-robot-card");
    var lines=["anim-line-2f","anim-line-3f","anim-line-su"];
    card.style.opacity="0.3";
    for(var i=0;i<cards.length;i++)cards[i].style.opacity="0.2";
    for(var i=0;i<lines.length;i++)
      document.getElementById(lines[i]).setAttribute("opacity","0");
    /* Step 1: light central card */
    setTimeout(function(){card.style.opacity="1";},200);
    /* Step 2: draw lines + light robots */
    setTimeout(function(){
      for(var i=0;i<lines.length;i++){
        (function(lid,cid,delay){
          setTimeout(function(){
            document.getElementById(lid).setAttribute("opacity","0.7");
            cid.style.opacity="1";
          },delay);
        })(lines[i],cards[i],i*600);
      }
    },800);
  }
  window.__asirCrossRun=run;
  setTimeout(run,1600);
})();
</script>
</div>"""


def generate_html_report(
    failure_traj: dict,
    success_traj: dict,
    failure_trace: dict,
    success_trace: dict,
    patch: dict,
    plot_rel_path: str,
    output_path: str,
    cross_embodiment_transfer: dict | None = None,
) -> None:
    """Generate the full HTML report (v0.4.0)."""

    # Comparison table (bilingual)
    f_max_slip = max(failure_traj["slip_score"])
    s_max_slip = max(success_traj["slip_score"])
    f_max_tilt = max(failure_traj["cup_tilt"])
    s_max_tilt = max(success_traj["cup_tilt"])
    f_final_height = failure_traj["cup_height"][-1]
    s_final_height = success_traj["cup_height"][-1]

    comparison_rows = [
        ("max slip_score", "最大滑移风险", f"{f_max_slip:.3f}", f"{s_max_slip:.3f}"),
        ("max cup_tilt (deg)", "最大杯子倾角", f"{f_max_tilt:.1f}", f"{s_max_tilt:.1f}"),
        ("final cup_height (m)", "最终杯子高度", f"{f_final_height:.3f}", f"{s_final_height:.3f}"),
        ("result", "结果", "FAILURE", "SUCCESS"),
    ]
    _val_zh = {"FAILURE": "失败", "SUCCESS": "成功"}
    comparison_html = ""
    for m_en, m_zh, fv, sv in comparison_rows:
        f_color = "#e74c3c" if "FAIL" in fv else ("#27ae60" if "SUCC" in fv else "#333")
        s_color = "#27ae60" if "SUCC" in sv else ("#e74c3c" if "FAIL" in sv else "#333")
        fv_s = f'<span data-en="{fv}" data-zh="{_val_zh.get(fv, fv)}">{fv}</span>' if fv in _val_zh else fv
        sv_s = f'<span data-en="{sv}" data-zh="{_val_zh.get(sv, sv)}">{sv}</span>' if sv in _val_zh else sv
        comparison_html += (
            f'<tr><td><strong><span data-en="{m_en}" data-zh="{m_zh}">{m_en}</span></strong></td>'
            f'<td style="color:{f_color};">{fv_s}</td>'
            f'<td style="color:{s_color};">{sv_s}</td></tr>'
        )

    # Patch card (v0.2)
    patch_html = ""
    if patch:
        relation_delta = patch.get("relation_delta", {})
        relation_str = (
            " &rarr; ".join(relation_delta["support"])
            if isinstance(relation_delta, dict) and "support" in relation_delta
            else str(relation_delta)
        )
        patch_html = f"""
        <div style="background:#fff3cd;padding:16px;border-radius:8px;border:1px solid #ffc107;">
            <h3 style="margin-top:0;"><span data-en="Failure Patch" data-zh="失败补丁">Failure Patch</span> <code>{patch.get('patch_id', '?')}</code></h3>
            <p><strong><span data-en="Type:" data-zh="类型：">Type:</span></strong> {patch['failure_type']}<br>
            <strong><span data-en="Failure hypothesis:" data-zh="失败假设：">Failure hypothesis:</span></strong> {format_failure_hypothesis(patch)}<br>
            <strong><span data-en="Relation delta:" data-zh="关系退化：">Relation delta:</span></strong> support: {relation_str}<br>
            <strong><span data-en="Validation:" data-zh="验证：">Validation:</span></strong> <code>{patch.get('validation_status', 'pending')}</code></p>
            <p><strong><span data-en="Repair actions:" data-zh="修复动作：">Repair actions:</span></strong></p>
            <ul>
                <li><span data-en="Force:" data-zh="力：">Force:</span> <code>{patch['patch']['adjust_force']}</code></li>
                <li><span data-en="Contact:" data-zh="接触：">Contact:</span> <code>{patch['patch']['adjust_contact']}</code></li>
                <li><span data-en="Restart from:" data-zh="重启阶段：">Restart from:</span> <code>{patch['patch']['restart_from_phase']}</code></li>
            </ul>
        </div>
        """

    # Learning notes
    learning_notes = success_trace.get("learning_update", {}).get("notes", [])
    learning_html = "".join(f"<li>{n}</li>" for n in learning_notes)

    # Run metadata
    f_meta = failure_traj.get("run_metadata", {})
    s_meta = success_traj.get("run_metadata", {})

    # Interaction flow
    flow_html = _build_interaction_flow(failure_trace, success_trace, patch)

    # Raw vs AS-IR table
    raw_vs_asir_rows = _build_raw_vs_asir_table()

    # Representation gain
    rg = failure_trace.get("representation_gain", {})
    rg_rows = _build_representation_gain(rg)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PILa Cup-Grasp MVP v0.4.0</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
           max-width: 940px; margin: 0 auto; padding: 60px 20px 40px; color: #333; line-height: 1.6; }}
    h1 {{ font-size: 2em; border-bottom: 2px solid #333; padding-bottom: 10px; }}
    h2 {{ color: #2c3e50; margin-top: 2em; }}
    .subtitle {{ color: #666; font-size: 1.1em; margin-bottom: 30px; }}
    .card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 16px 0;
             border: 1px solid #e9ecef; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #dee2e6; }}
    th {{ background: #f1f3f5; font-weight: 600; }}
    code {{ background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
    pre {{ background: #f1f3f5; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 0.85em; }}
    img {{ max-width: 100%; border-radius: 8px; border: 1px solid #dee2e6; }}
    .footer {{ margin-top: 3em; padding-top: 20px; border-top: 1px solid #dee2e6;
               color: #868e96; font-size: 0.9em; }}
    .hypothesis {{ background: #e7f5ff; padding: 20px; border-radius: 8px;
                   border-left: 4px solid #339af0; margin: 20px 0; }}
    .note {{ background: #fff9db; padding: 12px; border-radius: 6px; font-size: 0.95em;
             border-left: 4px solid #fcc419; margin: 12px 0; }}
    .meta {{ color: #868e96; font-size: 0.85em; }}
    .lang-toggle {{ position: fixed; top: 16px; right: 16px; z-index: 1000;
                    background: white; border: 1px solid #e5e7eb; border-radius: 999px;
                    padding: 6px; box-shadow: 0 8px 24px rgba(15,23,42,0.12); }}
    .lang-toggle button {{ border: none; border-radius: 999px; padding: 7px 12px;
                            background: transparent; cursor: pointer; font-size: 0.9em; }}
    .lang-toggle button.active {{ background: #111827; color: white; }}
</style>
</head>
<body>

<div class="lang-toggle">
  <button id="btn-en" class="active" onclick="setLanguage('en')">English</button>
  <button id="btn-zh" onclick="setLanguage('zh')">中文</button>
</div>

<h1><span data-en="PILa Cup-Grasp MVP v0.4.0" data-zh="PILa 物理交互语言杯子抓取最小样机 v0.4.0">PILa Cup-Grasp MVP v0.4.0</span></h1>
<p class="subtitle">
    <span data-en="From Raw Trajectory to Physical Interaction Language" data-zh="从原始轨迹到物理交互语言">From Raw Trajectory to Physical Interaction Language</span><br>
    <em><span data-en='Validating whether PILa can turn "what the robot did" into "what happened in the physical interaction."' data-zh='验证 PILa 是否能把"机器人做了什么"升级为"物理交互中发生了什么"。'>Validating whether PILa can turn "what the robot did" into "what happened in the physical interaction."</span></em>
</p>
<div class="card" style="border-left:4px solid #339af0;background:#e7f5ff;">
    <p><span data-en="PILa (Physical Interaction Language) is the public-facing language name." data-zh="PILa（Physical Interaction Language，物理交互语言）是对外语言名。">PILa (Physical Interaction Language) is the public-facing language name.</span><br>
    <span data-en="AS-IR (Action-State Intermediate Representation) is the underlying intermediate representation layer." data-zh="AS-IR（Action-State Intermediate Representation，行动状态表示层）是底层中间表示层。">AS-IR (Action-State Intermediate Representation) is the underlying intermediate representation layer.</span></p>
    <p style="font-weight:bold;"><span data-en="PILa is the language; AS-IR is the IR substrate." data-zh="PILa 是语言，AS-IR 是底座。">PILa is the language; AS-IR is the IR substrate.</span></p>
</div>

<p class="meta">
    <span data-en="Failure run:" data-zh="失败执行：">Failure run:</span> <code>{f_meta.get('run_id', '?')}</code> &middot;
    <span data-en="Patched run:" data-zh="补丁执行：">Patched run:</span> <code>{s_meta.get('run_id', '?')}</code> &middot;
    <span data-en="Scenario:" data-zh="场景：">Scenario:</span> <code>{f_meta.get('scenario', '?')}</code> &middot;
    <span data-en="Friction:" data-zh="摩擦：">Friction:</span> <code>{f_meta.get('friction_level', '?')}</code>
</p>

<!-- Section 1: Problem -->
<h2>1. <span data-en="Why PILa?" data-zh="为什么需要 PILa？">Why PILa?</span></h2>
<div class="card">
<p>
<span data-en="Raw robot trajectories record joint angles, forces, and poses as low-level time series. They tell us what changed, but not why the interaction failed:" data-zh="原始机器人轨迹记录的是关节角度、力、位姿等低层信号。它们能告诉我们哪些信号发生了变化，但不能直接说明交互为什么失败：">Raw robot trajectories record joint angles, forces, and poses as low-level time series.
They tell us <strong>what changed</strong>, but not <strong>why the interaction failed</strong>:</span>
</p>
<ul>
    <li><span data-en="Which phase broke down?" data-zh="哪个阶段出现了问题？">Which phase broke down?</span></li>
    <li><span data-en="What physical relation degraded?" data-zh="哪个物理关系退化了？">What physical relation degraded?</span></li>
    <li><span data-en="What invariant was violated?" data-zh="哪个不变量被违反了？">What invariant was violated?</span></li>
    <li><span data-en="How should the robot repair and retry?" data-zh="机器人应该如何修复并重试？">How should the robot repair and retry?</span></li>
</ul>
<p>
<span data-en="PILa is a Physical Interaction Language for embodied intelligence. It describes what happens in physical interaction, not merely what the robot did. AS-IR is the intermediate representation layer underneath PILa — it structures intent, phases, physical relations, failure patches, transferability, runtime risks and engineering adapters." data-zh="PILa 是一种面向具身智能的物理交互语言。它描述的是物理交互中发生了什么，而不只是机器人做了什么。AS-IR 是 PILa 底层的中间表示层——它结构化描述意图、阶段、物理关系、失败补丁、迁移边界、运行风险和工程适配。"><strong>PILa</strong> is a Physical Interaction Language for embodied intelligence.
It describes <strong>what happens in physical interaction</strong>, not merely what the robot did.
<strong>AS-IR</strong> is the intermediate representation layer underneath PILa &mdash;
it structures intent, phases, physical relations, failure patches, transferability,
runtime risks and engineering adapters.</span>
</p>
</div>

<!-- Section 2: Raw vs AS-IR -->
<h2>2. <span data-en="Raw Trajectory vs PILa / AS-IR Trace" data-zh="原始轨迹 vs PILa / AS-IR 追踪">Raw Trajectory vs PILa / AS-IR Trace</span></h2>
<p><span data-en="Raw trajectory is signal-level. PILa uses AS-IR to provide structure-level." data-zh="原始轨迹是信号层，PILa 通过 AS-IR 提供结构层。">Raw trajectory is signal-level. PILa uses AS-IR to provide structure-level.</span></p>
<table>
    <thead><tr><th><span data-en="Question" data-zh="视角">Question</span></th><th><span data-en="Raw Trajectory" data-zh="原始轨迹">Raw Trajectory</span></th><th><span data-en="AS-IR" data-zh="AS-IR">AS-IR</span></th></tr></thead>
    <tbody>{raw_vs_asir_rows}</tbody>
</table>

<!-- Section 3: Raw Trajectory View -->
<h2>3. <span data-en="Raw Trajectory View" data-zh="原始轨迹视角">Raw Trajectory View</span></h2>
<img src="{plot_rel_path}" alt="Trajectory comparison plot">
<p class="note">
    <span data-en="This chart compares the failed run and the patched run of the cup-grasp task. In the failed run, the grip force remains too low, the slip score rises sharply, the cup tilt increases, the contact force drops, and the cup only lifts briefly before falling. In the patched run, the grip force is increased, the contact force remains stable, the slip score stays close to zero, and the cup height continues to rise. This indicates that the patch improves support stability during grasping and lifting." data-zh="这组图对比了抓杯任务的失败运行与补丁后运行。失败运行中，抓取力不足，滑移分数升高，杯子倾斜增大，接触力下降，杯子只短暂离开桌面后又掉落。补丁后运行中，抓取力提高，接触力保持稳定，滑移风险接近零，杯子高度持续上升，说明补丁增强了抓取过程中的支撑稳定性。">This chart compares the failed run and the patched run of the cup-grasp task. In the failed run, the grip force remains too low, the slip score rises sharply, the cup tilt increases, the contact force drops, and the cup only lifts briefly before falling. In the patched run, the grip force is increased, the contact force remains stable, the slip score stays close to zero, and the cup height continues to rise. This indicates that the patch improves support stability during grasping and lifting.</span>
    <span data-en="However, raw trajectory data only shows which signals changed. It does not directly explain why the physical interaction failed. AS-IR / PILa adds this missing structural layer: during the grasp → lift phase, the support relation between the gripper and the cup degrades from stable support to unstable support and eventually breaks. The root cause is not a single abnormal signal, but the failure to maintain support stability under low-friction conditions." data-zh="但原始轨迹只能显示"哪些信号发生了变化"，不能直接表达"为什么交互失败"。AS-IR / PILa 要补上的正是这一层结构意义：在 grasp → lift 阶段，杯子与夹爪之间的 support relation 从稳定支撑退化为不稳定支撑，最终断裂。失败的本质不是某一个数值异常，而是低摩擦条件下支撑关系无法维持。">However, raw trajectory data only shows which signals changed. It does not directly explain why the physical interaction failed. AS-IR / PILa adds this missing structural layer: during the grasp → lift phase, the support relation between the gripper and the cup degrades from stable support to unstable support and eventually breaks. The root cause is not a single abnormal signal, but the failure to maintain support stability under low-friction conditions.</span>
</p>

<style>
.insight-cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}}

.insight-card {{
    background: #f8fafc;
    border-left: 4px solid #3b82f6;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}}

.insight-card h4 {{
    margin: 0 0 0.5rem 0;
    color: #1e40af;
    font-size: 1rem;
    font-weight: 600;
}}

.insight-card p {{
    margin: 0;
    color: #475569;
    font-size: 0.9rem;
    line-height: 1.4;
}}
</style>

<div class="insight-cards">
    <div class="insight-card">
        <h4>
            <span data-en="📊 Raw Trajectory" data-zh="📊 原始轨迹">📊 Raw Trajectory</span>
        </h4>
        <p>
            <span data-en="Which signals changed?" data-zh="发生了什么信号变化？">Which signals changed?</span>
        </p>
    </div>

    <div class="insight-card">
        <h4>
            <span data-en="🧠 AS-IR / PILa" data-zh="🧠 AS-IR / PILa">🧠 AS-IR / PILa</span>
        </h4>
        <p>
            <span data-en="What structural change happened in the physical interaction?" data-zh="物理交互结构发生了什么变化？">What structural change happened in the physical interaction?</span>
        </p>
    </div>

    <div class="insight-card">
        <h4>
            <span data-en="🔧 Failure Patch" data-zh="🔧 Failure Patch">🔧 Failure Patch</span>
        </h4>
        <p>
            <span data-en="Which part of the interaction structure should be repaired?" data-zh="应该修复哪一段结构？">Which part of the interaction structure should be repaired?</span>
        </p>
    </div>
</div>

<p class="note" style="margin-top: 1.5rem;">
    <span data-en="This chart compares the failed run and the patched run of the cup-grasp task. In the failed run, the grip force remains too low, the slip score rises sharply, the cup tilt increases, the contact force drops, and the cup only lifts briefly before falling. In the patched run, the grip force is increased, the contact force remains stable, the slip score stays close to zero, and the cup height continues to rise. This indicates that the patch improves support stability during grasping and lifting." data-zh="这组图对比了抓杯任务的失败运行与补丁后运行。失败运行中，抓取力不足，滑移分数升高，杯子倾斜增大，接触力下降，杯子只短暂离开桌面后又掉落。补丁后运行中，抓取力提高，接触力保持稳定，滑移风险接近零，杯子高度持续上升，说明补丁增强了抓取过程中的支撑稳定性。">This chart compares the failed run and the patched run of the cup-grasp task. In the failed run, the grip force remains too low, the slip score rises sharply, the cup tilt increases, the contact force drops, and the cup only lifts briefly before falling. In the patched run, the grip force is increased, the contact force remains stable, the slip score stays close to zero, and the cup height continues to rise. This indicates that the patch improves support stability during grasping and lifting.</span>
    <span data-en="However, raw trajectory data only shows which signals changed. It does not directly explain why the physical interaction failed. AS-IR / PILa adds this missing structural layer: during the grasp → lift phase, the support relation between the gripper and the cup degrades from stable support to unstable support and eventually breaks. The root cause is not a single abnormal signal, but the failure to maintain support stability under low-friction conditions." data-zh="但原始轨迹只能显示"哪些信号发生了变化"，不能直接表达"为什么交互失败"。AS-IR / PILa 要补上的正是这一层结构意义：在 grasp → lift 阶段，杯子与夹爪之间的 support relation 从稳定支撑退化为不稳定支撑，最终断裂。失败的本质不是某一个数值异常，而是低摩擦条件下支撑关系无法维持。">However, raw trajectory data only shows which signals changed. It does not directly explain why the physical interaction failed. AS-IR / PILa adds this missing structural layer: during the grasp → lift phase, the support relation between the gripper and the cup degrades from stable support to unstable support and eventually breaks. The root cause is not a single abnormal signal, but the failure to maintain support stability under low-friction conditions.</span>
</p>

<!-- Section 3.5: Physical Interaction Animation -->
<h2>4. <span data-en="Physical Interaction Animation" data-zh="物理交互动画">Physical Interaction Animation</span></h2>
<p><span data-en="PILa makes the phase chain of physical interaction visible: approach, align, contact, unstable grasp, lift failure, patch and re-execution." data-zh="PILa 让物理交互的阶段链变得可见：接近、对齐、接触、抓取不稳定、提起失败、补丁修复和再次执行。">PILa makes the phase chain of physical interaction visible: approach, align, contact, unstable grasp, lift failure, patch and re-execution.</span></p>
{_render_interaction_animation()}

<!-- Section 4: AS-IR Interaction Flow -->
<h2>5. <span data-en="PILa / AS-IR Interaction Flow" data-zh="PILa / AS-IR 交互流">PILa / AS-IR Interaction Flow</span></h2>
<p><span data-en="The full lifecycle: intent → phases → failure detection → patch → patched success." data-zh="完整生命周期：意图 → 阶段 → 失败检测 → 补丁 → 补丁后成功。">The full lifecycle: intent &rarr; phases &rarr; failure detection &rarr; patch &rarr; patched success.</span></p>
{flow_html}

<!-- Section 5: AS-IR Structure View (Failure) -->
<h2>6. <span data-en="PILa / AS-IR Structure View (Failure Run)" data-zh="PILa / AS-IR 结构视角（失败执行）">PILa / AS-IR Structure View (Failure Run)</span></h2>
<p><span data-en="PILa uses AS-IR to reveal phases, physical relations, runtime risks, failure patches and transfer boundaries." data-zh="PILa 通过 AS-IR 显影出阶段、物理关系、运行风险、失败补丁和迁移边界。">PILa uses AS-IR to reveal phases, physical relations, runtime risks, failure patches and transfer boundaries.</span></p>

<h3><span data-en="Intent" data-zh="意图">Intent</span></h3>
<div class="card">
    <p><strong><span data-en="Goal:" data-zh="目标：">Goal:</span></strong> <code>{failure_trace['intent']['goal_state']}</code><br>
    <strong><span data-en="Constraints:" data-zh="约束：">Constraints:</span></strong> {', '.join(f'<code>{c}</code>' for c in failure_trace['intent']['constraints'])}<br>
    <strong><span data-en="Success criteria:" data-zh="成功标准：">Success criteria:</span></strong></p>
    <ul>
        <li>cup_height > 0.15m</li>
        <li>cup_tilt &lt; 8deg</li>
        <li>slip_score &lt; 0.3</li>
    </ul>
</div>

<h3><span data-en="Phases (with per-phase risk)" data-zh="阶段（含逐阶段风险）">Phases (with per-phase risk)</span></h3>
<div class="card">
    {_render_phases(failure_trace['phases'])}
</div>

<h3><span data-en="Physical Relations" data-zh="物理关系">Physical Relations</span></h3>
<div class="card">
    {_render_relations(failure_trace['physical_relations'])}
</div>

<h3><span data-en="Physical Invariants" data-zh="物理不变量">Physical Invariants</span></h3>
<div class="card">
    {_render_invariants(failure_trace['runtime']['physical_invariants'])}
</div>

<h3><span data-en="Risk Policy" data-zh="风险策略">Risk Policy</span></h3>
<div class="card">
    <p><strong><span data-en="Level:" data-zh="等级：">Level:</span></strong>
    <span style="color:{"#e74c3c" if failure_trace['runtime']['risk_policy']['level']=="ORANGE" else ("#f39c12" if failure_trace['runtime']['risk_policy']['level']=="YELLOW" else "#27ae60")};">
    {failure_trace['runtime']['risk_policy']['level']}</span><br>
    <strong><span data-en="Reason:" data-zh="原因：">Reason:</span></strong> {failure_trace['runtime']['risk_policy']['reason']}</p>
</div>

<h3><span data-en="Failure Patch" data-zh="失败补丁">Failure Patch</span></h3>
{patch_html}

<!-- Section 6.5: Meaning Extraction Animation -->
<h2>7. <span data-en="From Raw Signals to PILa / AS-IR Structure" data-zh="从原始信号到 PILa / AS-IR 结构">From Raw Signals to PILa / AS-IR Structure</span></h2>
<p><span data-en="PILa uses AS-IR to reveal the interaction structure hidden in raw signals." data-zh="PILa 通过 AS-IR，把原始信号中隐藏的交互结构显影出来。">PILa uses AS-IR to reveal the interaction structure hidden in raw signals.</span></p>
{_render_meaning_extraction_animation()}

<!-- Section 6: Patch & Re-execution -->
<h2>8. <span data-en="Patch &amp; Re-execution" data-zh="补丁与重新执行">Patch &amp; Re-execution</span></h2>
<p><span data-en="Failure patch F1 changes the second run and validates the repair hypothesis." data-zh="失败补丁 F1 改变了第二次执行，并验证了修复假设。">Failure patch F1 changes the second run and validates the repair hypothesis.</span></p>

<table>
    <thead>
        <tr><th><span data-en="Metric" data-zh="指标">Metric</span></th><th><span data-en="Failure Run" data-zh="失败执行">Failure Run</span></th><th><span data-en="Patched Run" data-zh="补丁后执行">Patched Run</span></th></tr>
    </thead>
    <tbody>
        {comparison_html}
    </tbody>
</table>

<!-- Section 7: AS-IR Structure View (Success) -->
<h2>9. <span data-en="AS-IR Structure View (Patched Run)" data-zh="AS-IR 结构视图（补丁后执行）">AS-IR Structure View (Patched Run)</span></h2>

<div class="grid">
<div class="card">
    <h3><span data-en="Phases" data-zh="阶段">Phases</span></h3>
    {_render_phases(success_trace['phases'])}
</div>
<div class="card">
    <h3><span data-en="Physical Relations" data-zh="物理关系">Physical Relations</span></h3>
    {_render_relations(success_trace['physical_relations'])}
</div>
</div>

<div class="grid">
<div class="card">
    <h3><span data-en="Physical Invariants" data-zh="物理不变量">Physical Invariants</span></h3>
    {_render_invariants(success_trace['runtime']['physical_invariants'])}
</div>
<div class="card">
    <h3><span data-en="Risk Policy" data-zh="风险策略">Risk Policy</span></h3>
    <p><strong><span data-en="Level:" data-zh="等级：">Level:</span></strong>
    <span style="color:#27ae60;">
    {success_trace['runtime']['risk_policy']['level']}</span><br>
    <strong><span data-en="Reason:" data-zh="原因：">Reason:</span></strong> {success_trace['runtime']['risk_policy']['reason']}</p>
</div>
</div>

<h3><span data-en="Learning Update" data-zh="学习写回">Learning Update</span></h3>
<div class="card">
    <p><strong><span data-en="Updated:" data-zh="已更新：">Updated:</span></strong> <code>{success_trace['learning_update']['updated']}</code><br>
    <strong><span data-en="Patch validated:" data-zh="补丁已验证：">Patch validated:</span></strong> <code>{success_trace['learning_update'].get('patch_validated', 'N/A')}</code></p>
    <ul>{learning_html}</ul>
</div>

<h3><span data-en="Transferability" data-zh="可迁移性">Transferability</span></h3>
<div class="card">
    <p><strong><span data-en="Domain-invariant:" data-zh="域不变：">Domain-invariant:</span></strong>
    {', '.join(f'<code>{x}</code>' for x in success_trace['transferability']['domain_invariant'])}<br>
    <strong><span data-en="Domain-specific:" data-zh="域特定：">Domain-specific:</span></strong>
    {', '.join(f'<code>{x}</code>' for x in success_trace['transferability']['domain_specific'])}<br>
    <strong><span data-en="Transfer confidence:" data-zh="迁移置信度：">Transfer confidence:</span></strong>
    {success_trace['transferability']['transfer_confidence']}</p>
</div>

<!-- Section 8: Representation Gain -->
<h2>10. <span data-en="Representation Gain" data-zh="表示增益">Representation Gain</span></h2>
<div class="card">
<table>
    <thead><tr><th><span data-en="Dimension" data-zh="维度">Dimension</span></th><th><span data-en="Value" data-zh="值">Value</span></th></tr></thead>
    <tbody>{rg_rows}</tbody>
</table>
</div>

<!-- Section 9: Cross-Embodiment Meaning Transfer -->
<h2>11. <span data-en="Cross-Embodiment Meaning Transfer" data-zh="跨本体意义迁移">Cross-Embodiment Meaning Transfer</span></h2>
<p><span data-en="PILa shares the interaction meaning; each robot uses its own adapter to generate an embodiment-specific patch." data-zh="PILa 共享交互意义；每个机器人通过自己的适配层生成本体专属补丁。">PILa shares the interaction meaning; each robot uses its own adapter to generate an embodiment-specific patch.</span></p>
{_render_cross_embodiment_animation()}
{_build_cross_embodiment_section(cross_embodiment_transfer) if cross_embodiment_transfer else '<div class="card"><p>Cross-embodiment transfer data not available.</p></div>'}

<!-- Section 10: Key Hypothesis -->
<h2>12. <span data-en="Key Hypothesis" data-zh="核心假说">Key Hypothesis</span></h2>
<div class="hypothesis">
<p>
<strong><span data-en="This MVP does not prove PILa solves embodied intelligence." data-zh="这个 MVP 并不证明 PILa 已经解决具身智能问题。">This MVP does not prove PILa solves embodied intelligence.</span></strong><br>
<span data-en="It only tests a minimal hypothesis:" data-zh="它只是在验证一个最小假说：">It only tests a minimal hypothesis:</span>
</p>
<p style="font-size:1.1em;">
<em><span data-en="A physical interaction language, implemented through AS-IR, can make failure diagnosis, repair and learning update more explicit than raw trajectory alone." data-zh="一种通过 AS-IR 实现的物理交互语言，是否能比单纯原始轨迹更显式地表达失败诊断、修复策略和学习写回。">A physical interaction language, implemented through AS-IR,
can make failure diagnosis, repair and learning update more explicit than raw trajectory alone.</span></em>
</p>
<p><span data-en="What v0.3 adds:" data-zh="v0.3 新增：">What v0.3 adds:</span></p>
<ul>
    <li><span data-en="Per-phase risk levels (GREEN / YELLOW / ORANGE)" data-zh="逐阶段风险等级（GREEN / YELLOW / ORANGE）">Per-phase risk levels (GREEN / YELLOW / ORANGE)</span></li>
    <li><span data-en="Patch validation pipeline (pending → passed)" data-zh="补丁验证流水线（pending → passed）">Patch validation pipeline (pending &rarr; passed)</span></li>
    <li><span data-en="Representation gain quantification" data-zh="表示增益量化">Representation gain quantification</span></li>
    <li><span data-en="Run metadata for reproducibility tracking" data-zh="运行元数据用于可复现性追踪">Run metadata for reproducibility tracking</span></li>
    <li><span data-en="Cross-embodiment meaning transfer (same failure meaning, different robot patches)" data-zh="跨本体意义迁移（同一失败意义，不同机器人补丁）">Cross-embodiment meaning transfer (same failure meaning, different robot patches)</span></li>
    <li><span data-en="Interactive animations: physical interaction timeline, meaning extraction, cross-embodiment flow" data-zh="交互动画：物理交互时间线、意义提取、跨本体流转">Interactive animations: physical interaction timeline, meaning extraction, cross-embodiment flow</span></li>
    <li><span data-en="Bilingual report: English / 中文 toggle" data-zh="双语报告：English / 中文 切换">Bilingual report: English / 中文 toggle</span></li>
</ul>
</div>

<!-- Section 12.5: Glossary -->
<h2>13. <span data-en="Glossary" data-zh="术语表">Glossary</span></h2>
<p><span data-en="This demo uses PILa as the language name and AS-IR as the technical IR layer." data-zh="本 demo 使用 PILa 作为语言名，AS-IR 作为底层技术表示层。">This demo uses PILa as the language name and AS-IR as the technical IR layer.</span></p>
<table>
    <thead><tr>
        <th><span data-en="Term" data-zh="术语">Term</span></th>
        <th><span data-en="中文" data-zh="中文">中文</span></th>
        <th><span data-en="Explanation" data-zh="解释">Explanation</span></th>
    </tr></thead>
    <tbody>
        <tr><td><strong>PILa</strong></td>
            <td><span data-en="Physical Interaction Language" data-zh="物理交互语言">Physical Interaction Language</span></td>
            <td><span data-en="The public-facing language for describing what happens in physical interaction." data-zh="用来描述物理交互中发生了什么的对外语言名。">The public-facing language for describing what happens in physical interaction.</span></td></tr>
        <tr><td><strong>AS-IR</strong></td>
            <td><span data-en="Action-State Intermediate Representation" data-zh="行动状态表示层">Action-State Intermediate Representation</span></td>
            <td><span data-en="The underlying IR layer of PILa." data-zh="PILa 底层的中间表示层。">The underlying IR layer of PILa.</span></td></tr>
        <tr><td><strong>AS-IR Core</strong></td>
            <td><span data-en="AS-IR 核心层" data-zh="AS-IR 核心层">AS-IR Core</span></td>
            <td><span data-en="Carries transferable interaction structure such as intent, phases, relations and failure patches." data-zh="承载可迁移的交互结构，如意图、阶段、关系和失败补丁。">Carries transferable interaction structure such as intent, phases, relations and failure patches.</span></td></tr>
        <tr><td><strong>Runtime Layer</strong></td>
            <td><span data-en="运行层" data-zh="运行层">Runtime Layer</span></td>
            <td><span data-en="Handles invariants, observability, uncertainty, risk policy, validation and learning update." data-zh="处理不变量、可观测性、不确定性、风险策略、验证和学习写回。">Handles invariants, observability, uncertainty, risk policy, validation and learning update.</span></td></tr>
        <tr><td><strong>Engineering Adapter</strong></td>
            <td><span data-en="工程适配层" data-zh="工程适配层">Engineering Adapter</span></td>
            <td><span data-en="Re-instantiates AS-IR structure into embodiment-specific execution strategies." data-zh="将 AS-IR 结构重新实例化为不同机器人本体的执行策略。">Re-instantiates AS-IR structure into embodiment-specific execution strategies.</span></td></tr>
        <tr><td><strong>Failure Patch</strong></td>
            <td><span data-en="失败补丁" data-zh="失败补丁">Failure Patch</span></td>
            <td><span data-en="A structured repair strategy generated from a diagnosed physical interaction failure." data-zh="从物理交互失败诊断中生成的结构化修复策略。">A structured repair strategy generated from a diagnosed physical interaction failure.</span></td></tr>
        <tr><td><strong>Cross-Embodiment Transfer</strong></td>
            <td><span data-en="跨本体意义迁移" data-zh="跨本体意义迁移">Cross-Embodiment Transfer</span></td>
            <td><span data-en="The same interaction meaning can be interpreted by different robot embodiments and mapped to different patches." data-zh="同一个交互意义可被不同机器人本体读取，并映射为不同补丁。">The same interaction meaning can be interpreted by different robot embodiments and mapped to different patches.</span></td></tr>
        <tr><td><strong>Raw Trajectory</strong></td>
            <td><span data-en="原始轨迹" data-zh="原始轨迹">Raw Trajectory</span></td>
            <td><span data-en="Low-level signals such as force, motion, pose, tilt and height." data-zh="力、运动、位姿、倾角和高度等低层信号。">Low-level signals such as force, motion, pose, tilt and height.</span></td></tr>
    </tbody>
</table>

<!-- Section 14: AS-IR Trace JSON -->
<h2>14. <span data-en="Full AS-IR Trace JSON" data-zh="完整 AS-IR 追踪 JSON">Full AS-IR Trace JSON</span></h2>
<p><strong><span data-en="Failure trace:" data-zh="失败追踪：">Failure trace:</span></strong></p>
<pre>{json.dumps(failure_trace, indent=2)}</pre>

<p><strong><span data-en="Success trace:" data-zh="成功追踪：">Success trace:</span></strong></p>
<pre>{json.dumps(success_trace, indent=2)}</pre>

<!-- Footer -->
<div class="footer">
    <span data-en="PILa MVP v0.4.0 &middot; Physical Interaction Language &middot; powered by AS-IR" data-zh="PILa MVP v0.4.0 &middot; 物理交互语言 &middot; 基于 AS-IR 行动状态表示层">PILa MVP v0.4.0 &middot; Physical Interaction Language &middot; powered by AS-IR</span><br>
    <span data-en="Model-learnable &middot; Human-auditable &middot; Embodiment-executable" data-zh="模型可学习 &middot; 人类可审计 &middot; 本体可执行">Model-learnable &middot; Human-auditable &middot; Embodiment-executable</span>
</div>

<script>
function setLanguage(lang) {{
  document.querySelectorAll("[data-en][data-zh]").forEach(function(el) {{
    el.textContent = el.dataset[lang];
  }});
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  localStorage.setItem("asir_lang", lang);
  document.getElementById("btn-en").className = lang === "en" ? "active" : "";
  document.getElementById("btn-zh").className = lang === "zh" ? "active" : "";
  window.__asirLang = lang;
}}
(function(){{
  var saved = localStorage.getItem("asir_lang") || "en";
  window.__asirLang = saved;
  if(saved !== "en") setLanguage(saved);
}})();
</script>

</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
