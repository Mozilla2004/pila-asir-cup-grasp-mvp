# Semantic-Control Adapter Spec v0.1
## From PILa / AS-IR Semantic Patches to Controller Constraints

---

> **This document is a conceptual adapter specification.**
> It does not claim that the current v0.5.2-RC2 demo controls a real robot.
> It does not replace VLA, World Model, Motion Planner, MPC, PID, or low-level Controller.
> It only describes how a semantic patch may be translated into controller-facing constraints in a future implementation.

中文补充：
本文档是概念性适配规范，不是已经完成的控制器集成。它用于说明语义补丁如何可能映射到控制约束，而不是声称当前 demo 已经具备真实控制能力。

---

## 1. Problem Statement

PILa / AS-IR can express semantic patches such as `increase_support_constraint`.
Controllers require concrete constraints such as force margin, acceleration limit, impedance parameter, MPC cost term, or gripper command.
Therefore, an adapter layer is needed between semantic patch and controller action.

中文解释：
PILa / AS-IR 能表达"增加支撑约束"这类语义补丁；
控制器需要的是力、速度、加速度、阻抗、MPC cost、夹爪命令等控制空间对象；
因此需要语义—控制适配层。

---

## 2. Non-Goals

This spec does **not**:
- Define a universal controller
- Replace existing controllers
- Directly tune PID / MPC / impedance parameters without validation
- Claim real-robot execution
- Claim safe deployment without hardware-side safety constraints
- Convert `failure_hypothesis` into `root_cause`

---

## 3. Minimal Adapter Chain

```
semantic_patch                 # 语义补丁
  → control_intent             # 控制意图
  → controller_constraint      # 控制约束
  → controller_action_candidate # 控制动作候选
  → validation_metric          # 验证指标
  → writeback_policy           # 回写策略
```

Each field:

| Field | Description | 中文说明 |
|-------|-------------|----------|
| `semantic_patch` | High-level interaction meaning from AS-IR trace | 语义补丁：来自 AS-IR trace 的高层交互含义 |
| `control_intent` | What the controller should achieve | 控制意图：控制器应达成的目标 |
| `controller_constraint` | Concrete parameters for the controller | 控制约束：控制器的具体参数 |
| `controller_action_candidate` | Possible low-level actions | 控制动作候选：可能的底层动作 |
| `validation_metric` | How to verify the patch worked | 验证指标：如何验证补丁有效 |
| `writeback_policy` | When and how to record the result | 回写策略：何时以及如何记录结果 |

---

## 4. Example: support_degraded_under_low_friction

Using the current cup-grasp failure as an example:

```yaml
failure_hypothesis: "support_degraded_under_low_friction"   # 失败假设：低摩擦条件下支撑退化
semantic_patch: "increase_support_constraint"                # 语义补丁：增加支撑约束
control_intent:                                              # 控制意图
  - "increase_normal_force_margin"                           # 增加法向力裕度
  - "reduce_lift_acceleration"                               # 降低提起加速度
  - "maintain_cup_tilt_within_safe_range"                    # 将杯体倾斜保持在安全范围内
controller_constraint:                                       # 控制约束
  - name: "normal_force_margin"                              # 法向力裕度
    target: "increase"                                       # 目标：增加
    requires_validation: true                                # 需要验证
  - name: "lift_acceleration_limit"                          # 提起加速度限制
    target: "decrease"                                       # 目标：降低
    requires_validation: true                                # 需要验证
  - name: "slip_score_threshold"                             # 滑移分数阈值
    target: "keep_below_threshold"                           # 目标：保持低于阈值
    requires_validation: true                                # 需要验证
validation_metric:                                           # 验证指标
  - "slip_score_peak"                                        # 滑移峰值
  - "cup_tilt_max"                                           # 最大杯体倾斜
  - "grip_force_stability"                                   # 夹持力稳定性
  - "lift_success"                                           # 提起成功
```

---

## 5. Cross-Embodiment Adapter Examples

The same semantic patch maps to different controller constraints depending on robot morphology.

```yaml
semantic_patch: "increase_support_constraint"  # 语义补丁：增加支撑约束

two_finger_gripper:                            # 二指夹爪
  possible_mapping:
    - "increase_normal_force_margin"           # 增加法向力裕度
    - "reduce_lift_acceleration"               # 降低提起加速度
  validation:
    - "slip_score_peak"                        # 滑移峰值
    - "cup_tilt_max"                           # 最大杯体倾斜

three_finger_gripper:                          # 三指夹爪
  possible_mapping:
    - "add_or_rebalance_contact_point"         # 增加或重平衡接触点
    - "redistribute_grip_force"                # 重新分配夹持力
  validation:
    - "contact_stability"                      # 接触稳定性
    - "slip_score_peak"                        # 滑移峰值

suction_gripper:                               # 吸盘
  possible_mapping:
    - "increase_vacuum_margin"                 # 增加负压裕度
    - "reduce_vertical_acceleration"           # 降低垂直加速度
  validation:
    - "vacuum_pressure_stability"              # 负压稳定性
    - "object_detachment_risk"                 # 物体脱落风险
```

> **These mappings are adapter candidates, not validated controller commands.**
> 这些映射是适配候选，不是已验证控制命令。

---

## 6. Adapter Output Schema v0.1

```yaml
adapter_output:                    # 适配器输出
  source_trace_id: ""              # 来源 trace ID
  failure_hypothesis: ""           # 失败假设
  semantic_patch: ""               # 语义补丁
  embodiment_target: ""            # 目标本体
  control_intent: []               # 控制意图
  controller_constraints: []       # 控制器约束
  action_candidates: []            # 动作候选
  validation_metrics: []           # 验证指标
  safety_boundary: []              # 安全边界
  writeback_policy: ""             # 回写策略
  status: "conceptual_candidate"   # 状态：概念候选
```

---

## 7. Validation Gate

No semantic-control mapping should be written back as a reusable control pattern unless it has passed validation.

A mapping may have one of the following statuses:

| Status | Meaning | 中文说明 |
|--------|---------|----------|
| `conceptual_candidate` | Hypothesis only, no validation | 只是概念候选 |
| `simulation_tested` | Tested in simulation | 已经仿真验证 |
| `hardware_tested` | Tested on real hardware | 已经硬件验证 |
| `rejected` | Validation failed | 验证失败 |
| `requires_human_review` | Needs human assessment | 需要人工确认 |

In the current v0.5.2-RC2 release, **all mappings remain `conceptual_candidate`**.

---

## 8. Relationship to the Five Embodied Intelligence Questions

| # | Question | Status |
|---|----------|--------|
| 1 | **failure_localization** — 失败怎么定位？ | Addressed by AS-IR stage-by-stage trace |
| 2 | **experience_reuse** — 经验怎么复用？ | Addressed by structured learning_update |
| 3 | **cross_embodiment_transfer** — 跨本体怎么迁移？ | Addressed by cross_embodiment module (conceptual) |
| 4 | **semantic_to_control** — 语义如何落到控制器？ | **This spec (conceptual)** |
| 5 | **real_failure_learning** — 如何从真实失败中学习？ | Not yet addressed — requires real robot / sim-to-real data |

This spec primarily addresses **Question 4: semantic_to_control**.

Question 5 (real_failure_learning) still requires real robot or ROS / sim-to-real data validation.

---

## 9. Writeback Boundary

Adapter candidates may be written to audit notes or adapter specs.
They must **not** be written as validated controller patterns unless validation evidence exists.

In the current v0.5.2-RC2 release, all mappings in this document remain **conceptual candidates**.

---

*Part of the PILa / AS-IR Cup-Grasp MVP v0.5.2-RC2 "TraceForge / 迹铸" project.*
