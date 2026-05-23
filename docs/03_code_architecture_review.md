# 当前代码架构审计 (Current Code Architecture Review)

**版本**: v0.5-stage-by-stage-trace
**创建日期**: 2025-05-20

## 当前项目代码模块

### 主要源文件

| 文件 | 行数 | 输入 | 输出 | 当前作用 | 对应 AS-IR 层级 |
|------|------|------|------|----------|-----------------|
| `simulate.py` | ~200 | seed, friction, patch | trajectory JSON | 生成模拟轨迹 | External → AS-IR Core |
| `asir_extract.py` | ~300 | trajectory JSON | AS-IR trace JSON | 提取 AS-IR 结构 | AS-IR Core |
| `patch_policy.py` | ~150 | AS-IR failure | patch suggestion | 生成修复建议 | AS-IR Runtime |
| `cross_embodiment.py` | ~200 | AS-IR failure | robot-specific patches | 跨机器人映射 | Engineering Adapter |
| `report.py` | ~1000+ | all JSON | HTML report | 生成可视化报告 | Output Layer |

---

## 诚实审计：当前实现的不足

### 1. `simulate.py` - 模拟器

**当前实现**:
- ✅ 生成低层信号 (force, distance, slip, tilt)
- ✅ 支持失败/成功两种场景
- ❌ **硬编码阶段转换逻辑**

**问题**:
```python
# 当前代码中的问题示例
if step < 15:
    phase = "approach"
elif step < 25:
    phase = "align"
elif step < 35:
    phase = "contact"
# ...
```

**应该有的**:
- 阶段转换应该由 `transition_condition` 驱动
- 应该支持动态阶段发现
- 应该有 `stage_transition_validation`

**对应层级**: AS-IR Core (Stage Transition Logic)

---

### 2. `asir_extract.py` - AS-IR 提取器

**当前实现**:
- ✅ 提取 intent, phases, physical_relations
- ✅ 生成 runtime 风险评估
- ❌ **缺少 component state 细节**
- ❌ **缺少 phase transition map**
- ❌ **使用 root_cause 而非 failure_hypothesis**

**问题**:
```python
# 当前代码中的问题示例
"root_cause": "grip_force_insufficient_under_low_friction"  # ❌ 绝对化
```

**应该有的**:
```python
# 应该是这样的
"failure_hypothesis": {
    "primary": "insufficient_normal_force_under_low_friction",
    "confidence": "medium",
    "evidence": [...],
    "alternative_hypotheses": [...]
}  # ✅ 假设化
```

**对应层级**: AS-IR Core → AS-IR Runtime

---

### 3. `patch_policy.py` - 补丁策略

**当前实现**:
- ✅ 生成结构化修复建议
- ✅ 支持 restart_from_phase
- ❌ **缺少 validation_required**
- ❌ **缺少 validation_metrics**
- ❌ **缺少 next_action_options**

**问题**:
```python
# 当前代码中的问题示例
"repair_decision": "increase_grip_force"  # ❌ 决策式语言
```

**应该有的**:
```python
# 应该是这样的
"patch_suggestion": {
    "action": "increase_normal_force_within_safe_limit",
    "validation_required": true,
    "validation_metrics": ["slip_score_peak", "tilt_deg_peak"]
}  # ✅ 建议式语言
```

**对应层级**: AS-IR Runtime

---

### 4. `cross_embodiment.py` - 跨机器人映射

**当前实现**:
- ✅ 支持三种机器人类型
- ✅ 生成机器人特定补丁
- ❌ **只有文字描述，缺少结构化映射**
- ❌ **缺少 conceptual vs realized 区分**

**问题**:
```python
# 当前代码中的问题示例
{
    "two_finger_gripper": {
        "patch": "increase_grip_force + shift_contact_position"  # ❌ 纯文字
    }
}
```

**应该有的**:
```python
# 应该是这样的
{
    "abstract_failure_structure": "low_friction_support_degradation",
    "abstract_patch": "increase_support_constraint",
    "embodiment_mappings": [
        {
            "robot_type": "two_finger_gripper",
            "mapping_type": "conceptual",  # ✅ 标注是概念性映射
            "concrete_action": "increase_normal_force_within_safe_limit",
            "requires_validation": true
        }
    ]
}
```

**对应层级**: Engineering Adapter

---

### 5. `report.py` - HTML 报告生成器

**当前实现**:
- ✅ 生成漂亮的双语 HTML 报告
- ✅ 包含动画和交互
- ❌ **主要聚焦"事后解释"**
- ❌ **缺少 stage-by-stage 运行时展示**
- ❌ **缺少 component state table**
- ❌ **缺少 phase transition map**
- ❌ **缺少 next_action_recommendation 展示**

**问题**:
- 报告**不是** AS-IR 运行时本身，只是事后可视化
- 缺少"实时追踪"的感觉
- 缺少"每一阶段的状态变化"展示

**应该有的**:
- `Stage-by-Stage AS-IR Runtime Trace` 章节
- `Component State Transition Table`
- `Physical Relation State Machine`
- `Next Action Recommendation` 展示

**对应层级**: Output Layer (应该展示所有层级)

---

## 缺失的核心模块

### 1. **Stage Transition Manager**
**作用**: 管理阶段转换的验证和执行

**应该包含**:
```python
class StageTransitionManager:
    def validate_transition(self, from_stage, to_stage, conditions):
        # 检查转换条件是否满足
        pass

    def execute_transition(self, stage, context):
        # 执行阶段转换
        pass
```

### 2. **Component State Tracker**
**作用**: 实时追踪所有部件状态

**应该包含**:
```python
class ComponentStateTracker:
    def update_state(self, component_id, state_delta):
        # 更新部件状态
        pass

    def get_state_snapshot(self, stage_id):
        # 获取阶段状态快照
        pass
```

### 3. **Physical Relation Manager**
**作用**: 维护物理关系状态机

**应该包含**:
```python
class PhysicalRelationManager:
    def update_relation(self, relation_id, new_state):
        # 更新关系状态
        pass

    def check_relation_health(self):
        # 检查关系健康度
        pass
```

### 4. **Next Action Recommender**
**作用**: 基于当前状态生成下一步行动建议

**应该包含**:
```python
class NextActionRecommender:
    def generate_options(self, current_state):
        # 生成候选行动
        pass

    def rank_actions(self, options, constraints):
        # 排序行动选项
        pass
```

### 5. **Learning Updater**
**作用**: 将验证结果写回知识库

**应该包含**:
```python
class LearningUpdater:
    def update_failure_library(self, hypothesis, validation_result):
        # 更新失败库
        pass

    def update_adapter_rules(self, embodiment, patch_result):
        # 更新适配器规则
        pass
```

---

## 当前实现的"事后解释"风险

### 风险 1: 绝对化因果
```python
# ❌ 当前实现
"root_cause": "grip_force_insufficient"  # 看起来像绝对真理

# ✅ 应该是
"failure_hypothesis": {
    "primary": "insufficient_normal_force",
    "confidence": "medium",
    "alternatives": ["acceleration_too_high", "contact_unstable"]
}
```

### 风险 2: 缺少实时感
```python
# ❌ 当前实现
# 只在最后生成一个失败报告

# ✅ 应该是
# 每个阶段都有状态更新和风险评估
for stage in stages:
    update_component_states()
    check_physical_relations()
    evaluate_risks()
    if risk_critical():
        generate_hypothesis()
        suggest_patch()
```

### 风险 3: 缺少可执行性
```python
# ❌ 当前实现
"repair_decision": "increase_grip_force"  # 怎么执行？

# ✅ 应该是
"next_action_recommendation": {
    "type": "validation_patch",
    "action": "increase_grip_force_by_20%",
    "from_stage": "P3",
    "validation_metrics": ["slip_score", "tilt_deg"]
}
```

---

## 硬编码检查清单

### 模拟器硬编码
- ❌ 阶段阈值硬编码 (step < 15, step < 25, ...)
- ❌ 摩擦系数固定值
- ❌ 失败条件固定

### AS-IR 提取硬编码
- ❌ 阶段识别逻辑固定
- ❌ 物理关系判断规则固定
- ❌ 风险阈值固定

### 补丁策略硬编码
- ❌ 补丁模板固定
- ❌ 修复参数固定 (force_multiplier = 2.0)

---

## 重构优先级

### P0 (必须修复)
1. **root_cause → failure_hypothesis** (全局重命名)
2. **repair_decision → patch_suggestion** (全局重命名)
3. 新增 `next_action_recommendation` 模块
4. 新增 `stage_by_stage_trace` 数据结构

### P1 (应该修复)
5. 拆分硬编码阶段转换逻辑
6. 新增 `component_state` 追踪
7. 新增 `physical_relation` 状态机
8. 新增 `validation_required` / `validation_metrics`

### P2 (可以延后)
9. 新增 `learning_update` 真实逻辑
10. 新增 `embodiment_adapter_mapping` 结构化
11. 新增动态阶段发现
12. 新增多假设并行生成

---

## 总结

**当前实现的优点**:
- ✅ 概念验证成功
- ✅ 数据结构清晰
- ✅ 可视化效果良好

**当前实现的局限**:
- ❌ 过于"事后报告化"
- ❌ 缺少"运行时追踪"感觉
- ❌ 硬编码较多
- ❌ 绝对化因果表达
- ❌ 缺少可执行性细节

**重构目标**:
- 🎯 从"失败诊断报告"升级为"运行时语义追踪"
- 🎯 从"绝对因果"改为"证据支持的假设"
- 🎯 从"硬编码阶段"改为"状态驱动转换"
- 🎯 从"事后解释"改为"实时可审计"

---

**本文档版本**: v0.5
**下一步**: 阅读 `04_refactor_plan.md`
