# AS-IR 重构计划 (Refactor Plan)

**版本**: v0.5-stage-by-stage-trace
**创建日期**: 2025-05-20

## 重构目标

从 **"失败诊断报告型 demo"** 升级为 **"Stage-by-Stage Physical Interaction Runtime Trace"**

---

## 第一阶段：文档和定位 (Phase 1: Documentation & Positioning)

### 1.1 README 重定位
**当前**:
```markdown
# AS-IR Cup-Grasp MVP v0.4.0
```

**重构后**:
```markdown
# PILa / AS-IR Cup-Grasp MVP v0.5

PILa is a Physical Interaction Language.
AS-IR is an Action-State Intermediate Representation.

This project demonstrates how a robot cup-grasp interaction can be
represented as a stage-by-stage physical interaction runtime trace...
```

### 1.2 新增核心概念说明
- PILa 不是 JSON
- AS-IR 不是失败报告生成器
- AS-IR 不替代 VLA / World Model / RL / Controller
- AS-IR 让上述组件更可观测、可验证、可修复

---

## 第二阶段：数据结构重构 (Phase 2: Data Structure Refactoring)

### 2.1 全局字段重命名

| 旧字段名 | 新字段名 | 原因 |
|---------|---------|------|
| `root_cause` | `failure_hypothesis` | 避免绝对化因果 |
| `repair_decision` | `patch_suggestion` | 强调建议而非决策 |
| `true_cause` | `evidence_backed_hypothesis` | 强调证据支持 |
| `guaranteed_repair` | `validation_required` | 避免过度承诺 |
| `causal_proof` | `validation_result` | 准确表达验证结果 |

### 2.2 新增核心数据结构

#### Stage-by-Stage Trace
```json
{
  "stage_id": "P0-P8",
  "phase": "intent_initialization → lift → failure",
  "timestamp": "...",
  "component_states": {...},
  "physical_relations": [...],
  "risk_signals": {...},
  "transition_condition": {...},
  "next_action_options": [...],
  "validation_metrics": [...],
  "learning_update": {...}
}
```

#### Component State Table
```json
{
  "component_id": "gripper_left_finger",
  "state_type": "continuous",
  "current_value": 3.2,
  "unit": "N",
  "valid_range": [0, 10],
  "safety_limit": 8,
  "change_rate": 0.1,
  "timestamp": "..."
}
```

#### Physical Relation State Machine
```json
{
  "relation_id": "gripper_cup_support",
  "relation_type": "support",
  "current_state": "degraded",
  "state_history": ["null", "establishing", "established", "degrading", "degraded"],
  "participants": ["gripper", "cup"],
  "health_metrics": {
    "stability_score": 0.3,
    "load_capacity": 0.5
  }
}
```

#### Next Action Recommendation
```json
{
  "current_interaction_state": "support_degrading",
  "risk_level": "high",
  "candidate_failure_hypotheses": [
    "insufficient_normal_force",
    "lift_acceleration_too_high",
    "contact_position_unstable"
  ],
  "next_action_recommendation": {
    "type": "validation_patch",
    "action": "reduce_lift_acceleration_and_retry_from_contact_phase",
    "reason": "low-risk patch; helps distinguish acceleration-induced slip from pure grip-force failure",
    "requires_validation": true,
    "validation_metrics": ["slip_score_peak", "tilt_deg_peak", "final_cup_height"]
  }
}
```

#### Learning Update
```json
{
  "learning_update": {
    "new_failure_structure": "low_friction_object + insufficient_normal_force + lift_acceleration -> slip -> support_degradation",
    "patch_validation": "reduce_lift_acceleration + increase_safe_grip_force improved stability",
    "dataset_action": "add before/after pair to failure-aware training set",
    "adapter_update": "for suction gripper, map normal_force increase to vacuum_pressure increase",
    "next_sampling_policy": "collect more low_friction lift cases with varied acceleration"
  }
}
```

**MVP 边界说明**：
> This shows structured experience retention, not automatic model weight updates.
>
> 这展示了结构化经验保留，不代表自动模型权重更新。

#### Embodiment Adapter Mapping
```json
{
  "abstract_failure_structure": "low_friction_support_degradation",
  "abstract_patch": "increase_support_constraint",
  "embodiment_mappings": [
    {
      "robot_type": "two_finger_gripper",
      "mapping_type": "conceptual",
      "concrete_action": "increase_normal_force_within_safe_limit",
      "parameter_mapping": {
        "normal_force_increase": "grip_force_delta"
      },
      "requires_validation": true
    },
    {
      "robot_type": "suction_gripper",
      "mapping_type": "conceptual",
      "concrete_action": "increase_vacuum_pressure_and_reduce_lift_acceleration",
      "parameter_mapping": {
        "support_constraint": "vacuum_pressure",
        "acceleration_limit": "lift_jerk_limit"
      },
      "requires_validation": true
    }
  ]
}
```

---

## 第三阶段：代码重构 (Phase 3: Code Refactoring)

### 3.1 `simulate.py` 重构

**新增**:
```python
class StageTransitionManager:
    def evaluate_transition_conditions(self, current_stage, state):
        # 基于条件而非硬编码步骤数
        conditions = {
            "P1_P2": lambda s: s["gripper_distance"] < 0.05,
            "P2_P3": lambda s: s["contact_force"] > 1.0,
            # ...
        }
        return conditions.get(f"{current_stage}_next")
```

### 3.2 `asir_extract.py` 重构

**新增**:
```python
def extract_failure_hypothesis(not_anomalies, physical_relations):
    # 生成候选失败假设，而非绝对根因
    return {
        "primary": select_most_likely_hypothesis(anomalies),
        "confidence": calculate_confidence(anomalies),
        "evidence": collect_evidence(anomalies, relations),
        "alternative_hypotheses": generate_alternatives(anomalies)
    }
```

### 3.3 新增 `next_action.py`

```python
class NextActionRecommender:
    def generate_recommendations(self, asir_state):
        if asir_state["risk_level"] < "medium":
            return continue_execution()
        else:
            return generate_validation_patches(asir_state)
```

### 3.4 新增 `learning_updater.py`

```python
class LearningUpdater:
    def update_from_validation(self, patch_result, validation_metrics):
        # MVP边界说明：这里指结构化经验保留与数据/策略建议
        #不代表已完成模型权重更新
        return {
            "new_failure_structure": ...,
            "patch_validation": ...,
            "dataset_action": ...,
            "adapter_update": ...,
            "next_sampling_policy": ...
        }
```

**MVP 边界说明**：
> In this MVP, `learning_update` means **structured experience retention and dataset/action-policy recommendation**, not automatic model weight update.
>
> 在本 MVP 中，`learning_update` 指**结构化经验保留与数据/策略建议**，不代表已完成模型权重更新。

---

## 第四阶段：HTML 报告重构 (Phase 4: HTML Report Refactoring)

### 4.1 新增核心章节

#### Stage-by-Stage AS-IR Runtime Trace
展示 8 个阶段的完整状态变化：
- P0: Intent Initialization
- P1: Approach
- P2: Contact Establishment
- P3: Support Transfer
- P4: Lift
- P5: Failure/Risk Escalation
- P6: Patch Suggestion
- P7: Validation
- P8: Learning Update

#### Component State Transition Table
表格展示每个阶段的关键部件状态

#### Physical Relation State Machine
可视化物理关系状态转换

#### Next Action Recommendation Cards
展示候选行动建议和理由

### 4.2 字段命名修正
- 全局 `root_cause` → `failure_hypothesis`
- 全局 `repair_decision` → `patch_suggestion`
- 全局 `guaranteed` → `validation_required`

---

## 第五阶段：边界说明 (Phase 5: Boundary Clarification)

### 5.1 MVP Proves / Does Not Prove

**This MVP demonstrates**:
- ✅ 结构化物理交互表示的可行性
- ✅ 阶段化状态追踪的概念
- ✅ 失败假设生成和验证流程
- ✅ 跨机器人的概念性映射

**This MVP does not yet prove**:
- ❌ 完全自动的阶段发现
- ❌ 真实跨机器人迁移
- ❌ 通用具身智能
- ❌ 替代 VLA / World Model / RL / Controller
- ❌ 真实世界的因果证明

### 5.2 "PILa is not JSON" 说明

在 README 和报告中明确：

```
PILa is a semantic language for physical interaction.
JSON is just one possible serialization format.
AS-IR traces could be stored in Protocol Buffers, ROS messages,
or any other data format.
```

---

## 第六阶段：向后兼容 (Phase 6: Backward Compatibility)

### 6.1 保留 v0.4 作为切片

创建 `outputs/v0.4_failure_report_slice.html`:
- 保留原有的失败报告功能
- 作为 AS-IR 的一个"应用切片"
- 不删除，但不再重点维护

### 6.2 升级说明

在 README 中说明 v0.5 的升级意义：

```markdown
## Version History

### v0.5 (Current)
- Focus: Stage-by-Stage Physical Interaction Runtime Trace
- Addition: Real-time semantic tracking, hypothesis-based reasoning

### v0.4 (Preserved)
- Focus: Failure Diagnosis Report
- Use Case: Post-hoc analysis and visualization
```

---

## 实施顺序

### Phase A: 文档和审计
1. ✅ 完成 5 个文档（当前阶段）
2. ⏳ 文档修订和人工审计
3. ⏳ 架构设计确认

### Phase B: 最小代码重构
4. ⏳ README 重定位 + 字段重命名
5. ⏳ 核心数据结构重构
6. ⏳ 新增基础模块 (next_action, learning_updater)

### Phase C: 报告/UI 升级
7. ⏳ HTML 报告重构 + 新增章节
8. ⏳ Stage-by-Stage Trace 可视化
9. ⏳ 边界说明完善

### Phase D: 边界和向后兼容
10. ⏳ 向后兼容处理 (v0.4 failure report slice)
11. ⏳ MVP proves / does not prove 说明完善
12. ⏳ 最终验证和文档更新

---

## 成功标准

### 必须达成 (Must Have)
- [ ] 5 个文档完成并通过人工审计
- [ ] README 定位更新
- [ ] 全局字段重命名完成
- [ ] Stage-by-Stage Trace 数据结构实现
- [ ] Next Action Recommendation 模块实现
- [ ] HTML 报告新增核心章节
- [ ] MVP 边界说明明确

### 应该达成 (Should Have)
- [ ] Component State Tracker 实现
- [ ] Physical Relation State Machine 实现
- [ ] Learning Updater 真实逻辑实现
- [ ] Embodiment Adapter Mapping 结构化

### 可以延后 (Nice to Have)
- [ ] 动态阶段发现
- [ ] 多假设并行生成
- [ ] 真实机器人集成

---

**本文档版本**: v0.5
**下一步**: 等待人工审计后执行重构
