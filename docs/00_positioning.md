# PILa / AS-IR 项目定位 (Project Positioning)

**版本**: v0.5-stage-by-stage-trace
**创建日期**: 2025-05-20

## 核心定位

### PILa 是什么？

**PILa = Physical Interaction Language (物理交互语言层)**

PILa **不是**：
- ❌ JSON schema
- ❌ 数据格式标准
- ❌ 报告生成器
- ❌ 失败诊断工具

PILa **是**：
- ✅ 定义物理交互的**语义层**
- ✅ 描述"物理交互中发生了什么"的**语言**
- ✅ 连接人类意图与机器人运行时行为的**意义桥梁**

### AS-IR 是什么？

**AS-IR = Action-State Intermediate Representation (行动—状态中间表示层)**

AS-IR **不是**：
- ❌ 失败报告生成器
- ❌ 日志记录系统
- ❌ 数据可视化工具
- ❌ 事后分析器

AS-IR **是**：
- ✅ 运行时**结构化状态轨迹**
- ✅ 可审计、可学习、可执行的**交互过程表达**
- ✅ 从人类意图到物理反馈的**完整语义链路**

### JSON / HTML Report 的角色

JSON 和 HTML 报告**只是输出载体**，不是 PILa / AS-IR 本身。

**类比**：
- PILa ≈ 编程语言 (如 Python)
- AS-IR ≈ 编译后的字节码
- JSON/HTML ≈ 执行结果输出

### 与其他组件的关系

| 组件 | 解决的问题 | 与 AS-IR 的关系 |
|------|------------|-----------------|
| **VLA** (Vision-Language-Action models) | "怎么行动？" | AS-IR 让 VLA 的行动过程更可观测、可验证 |
| **World Model** | "行动后会怎样？" | AS-IR 让 World Model 的预测更可审计、可修复 |
| **RL / Controller** | "如何执行控制？" | AS-IR 让控制过程更可解释、可迁移 |
| **AS-IR** | "物理交互过程如何表达？" | 为上述组件提供运行时语义层 |

### 当前 Demo 的边界

**当前 cup-grasp MVP 是什么**：
- ✅ AS-IR 在**单个任务**上的**最小切片**
- ✅ 验证"结构化物理交互表示"的概念可行性
- ✅ 展示 stage-by-stage trace 的核心思想

**当前 cup-grasp MVP 不是什么**：
- ❌ 完整的 PILa / AS-IR 体系
- ❌ 通用的具身智能解决方案
- ❌ 真实机器人的生产级实现
- ❌ 替代 VLA / World Model / RL / Controller

### 核心价值主张

> **AS-IR 让机器人物理交互从"黑盒执行"变为"可审计的语义过程"。**

**传统范式**：
```
人类意图 → [黑盒机器人] → 成功/失败
```

**AS-IR 范式**：
```
人类意图 → PILa语义解析 → AS-IR运行轨迹 → 结构化反馈 → 学习回写
```

---

**本文档版本**: v0.5
**下一步**: 阅读 `01_pila_asir_relationship.md`
