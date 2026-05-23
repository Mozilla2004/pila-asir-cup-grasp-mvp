# PILa 与 AS-IR 的关系 (PILa / AS-IR Relationship)

**版本**: v0.5-stage-by-stage-trace
**创建日期**: 2025-05-20

## 核心原则

> **PILa is the language layer.**
> **AS-IR is the runtime intermediate representation.**
> **PILa defines the meaning.**
> **AS-IR carries the meaning during execution.**

---

## PILa: Physical Interaction Language

### 职责
定义物理交互的**语义层**，描述"物理交互中有什么样的意义结构"。

### 核心语义元素

| 语义元素 | 英文 | 中文 | 说明 |
|---------|------|------|------|
| **意图** | `intent` | 意图 | 人类想要达成的物理交互目标 |
| **阶段** | `phase` | 阶段 | 交互过程的结构化分段 (approach / contact / support / lift) |
| **部件状态** | `component_state` | 部件状态 | 机器人各部件的物理状态 (gripper_open/closed, cup_height) |
| **物理关系** | `physical_relation` | 物理关系 | 部件间的物理交互关系 (support / contact / proximity) |
| **约束** | `constraint` | 约束 | 物理约束 (upright / no_slip / safe_force) |
| **风险** | `risk` | 风险 | 约束违反的概率或信号 (slip_risk / tilt_risk) |
| **失败假设** | `failure_hypothesis` | 失败假设 | 基于证据的候选失败解释 |
| **补丁语义** | `patch_semantics` | 补丁语义 | 修复建议的结构化表达 |
| **可迁移性** | `transferability` | 可迁移性 | 哪些知识可以跨任务/机器人迁移 |

### PILa 不涉及
- ❌ 具体的数据格式 (JSON / YAML / Protocol Buffers)
- ❌ 具体的编程语言 (Python / C++ / Rust)
- ❌ 具体的机器人接口 (ROS / XYZ)

---

## AS-IR: Action-State Intermediate Representation

### 职责
把 PILa 语义**编译**为机器人运行时可用的结构化状态轨迹。

### 核心结构

```
AS-IR Trace = [
  Stage 0: Intent Initialization
  Stage 1: Approach
  Stage 2: Contact Establishment
  Stage 3: Support Transfer
  Stage 4: Lift
  Stage 5: Failure / Risk Escalation
  Stage 6: Patch Suggestion
  Stage 7: Validation
  Stage 8: Learning Update
]
```

### 每个阶段的 AS-IR 结构

| 字段 | 类型 | 说明 | 对应 PILa 语义 |
|------|------|------|----------------|
| `phase_id` | string | 阶段标识 (P1-P8) | phase |
| `human_intent` | dict | 人类意图 | intent |
| `robot_body_capability` | dict | 机器人本体能力 | embodiment_constraint |
| `active_components` | list | 激活的部件 | component |
| `component_states` | dict | 部件状态 | component_state |
| `physical_relations` | list | 物理关系 | physical_relation |
| `invariants` | list | 不变量约束 | constraint |
| `risk_signals` | dict | 风险信号 | risk |
| `transition_condition` | dict | 阶段转换条件 | phase_transition |
| `next_action_options` | list | 下一步行动选项 | action_semantic |
| `patch_suggestion` | dict | 补丁建议 | patch_semantics |
| `validation_metrics` | list | 验证指标 | validation_semantic |
| `learning_update` | dict | 学习回写 | transferability |

---

## PILa → AS-IR 的映射关系

### 类比：编程语言 vs 字节码

| 层级 | PILa | AS-IR |
|------|------|-------|
| **高级** | "我想要抓起杯子" | `{intent: "pick_up_cup", phases: [...]}` |
| **中级** | "建立支撑关系" | `{relation: "support", state: "established"}` |
| **低级** | "检测滑移风险" | `{risk: "slip", probability: 0.8}` |
| **执行** | 机器人运行时轨迹 | 时间序列的状态机 |

### 编译过程

```
PILa Semantic Definition
    ↓ (semantic parsing)
AS-IR Schema Initialization
    ↓ (runtime execution)
Stage-by-Stage Interaction Trace
    ↓ (embodiment adaptation)
Robot-Specific Execution
    ↓ (feedback loop)
AS-IR State Update
```

---

## 实际例子：Cup-Grasp Failure

### PILa 语义表达

```
失败场景：低摩擦条件下，支撑关系退化

语义结构：
- phase: grasp → lift
- relation: support (established → degraded → broken)
- constraint: no_slip (violated)
- risk: slip_score (elevating)
- hypothesis: insufficient_normal_force + lift_acceleration
```

### AS-IR 运行时表达

```json
{
  "stage_id": "P5",
  "phase": "lift",
  "component_states": {
    "gripper_force": 3.2,
    "cup_height": 0.08,
    "slip_score": 0.76
  },
  "physical_relations": [
    {"type": "support", "state": "degraded"}
  ],
  "risk_signals": {
    "slip_risk": "high",
    "tilt_risk": "medium"
  },
  "failure_hypothesis": {
    "primary": "insufficient_normal_force_under_low_friction",
    "confidence": "medium",
    "evidence": ["elevating_slip_score", "increasing_tilt"]
  },
  "patch_suggestion": {
    "action": "increase_normal_force_and_reduce_lift_acceleration",
    "validation_required": true
  }
}
```

---

## 关键区别总结

| 维度 | PILa | AS-IR |
|------|------|-------|
| **性质** | 语言层 | 运行时表示层 |
| **职责** | 定义语义 | 承载语义 |
| **输出** | 语义规范 | 结构化轨迹 |
| **时间** | 设计时 | 运行时 |
| **抽象度** | 高 | 中 |
| **具体性** | 跨任务通用 | 任务/机器人实例化 |

---

**本文档版本**: v0.5
**下一步**: 阅读 `02_asir_pipeline_flow.md`
