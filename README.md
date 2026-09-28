<div align="center">

# 电商智能客服后端

**LLM 负责「读懂意图 + 生成话术」，YAML 规则引擎负责「跑业务流程」**

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.4-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)

</div>

---

## 项目简介

一个**面向电商场景的智能客服后端**。用户用自然语言描述诉求（"我要退款"、"这单到哪了"），系统能识别意图、驱动多轮业务流程（收集订单号、询问退款原因）、并在流程结束后给出自然语言回复。

设计的核心取舍是**把"理解"和"执行"分开**：

| | 交给谁 | 为什么 |
|---|---|---|
| **理解**用户的意图 | 大模型 | 自然语言的表达千变万化，规则写不完 |
| **执行**业务流程 | YAML 规则引擎 | 流程必须**可控、可预期、可配置**，不能靠模型自由发挥 |

所以对话状态机是**显式**的：每一步走到哪里、收集了哪些数据、下一步该问什么，全部记录在 `DialogueState` 里并持久化到 MySQL，模型只负责在关键节点做出"选择"。

> **本仓库为个人独立实现**：从领域模型、YAML 规则引擎、多轮槽位收集到状态持久化，均按分层架构自行编码完成。
> 配套的前端与电商 Mock 服务用于本地联调。

---

## 核心设计

### 三轨道意图路由

一次用户消息会先被判定为三条**互斥**轨道之一：

| 轨道 | 触发场景 | 处理方式 |
|---|---|---|
| **task** | 用户要办业务（查订单、退款、查物流） | 走 YAML 规则引擎，多轮推进 |
| **knowledge** | 用户在咨询信息（商品参数、售后政策） | 检索知识源 → 交给 LLM 组织回答 |
| **chitchat** | 闲聊、寒暄、超出范围的话 | 直接交给 LLM 兜底 |

### 业务任务 vs 系统任务

这是本项目的关键区分 —— **两套流程各司其职**：

```mermaid
flowchart LR
    subgraph BIZ["业务任务 · user_flows.yml"]
        B1["查订单状态"] 
        B2["退款申请"]
        B3["物流追踪"]
        B4["相似商品推荐"]
    end

    subgraph SYS["系统任务 · system_flows.yml"]
        S1["开工播报"]
        S2["追问槽位"]
        S3["任务打断/恢复"]
        S4["任务取消"]
        S5["无法处理兜底"]
    end

    B1 -. "需要用户提供订单号" .-> S2
    B2 -. "启动时播报一句" .-> S1
    B3 -. "需要用户提供单号" .-> S2
    B4 -. "打断当前任务" .-> S3

    style BIZ fill:#EEEDFE,stroke:#7F77DD,color:#26215C
    style SYS fill:#E1F5EE,stroke:#1D9E75,color:#04342C
```

- **业务任务**：真正"帮用户办事"的流程，带 `slots`（数据槽位），跨多轮
- **系统任务**：维持对话本身运转的"小动作"，比如追问缺失的槽位、播报"任务已取消"

**为什么这样分？** 因为"追问订单号"这件事，退款流程要问、查物流也要问、查订单还要问 —— 与其在每个业务流里各写一遍，不如抽成一个**共用的系统流程**：业务流只负责提供"问什么"（`slot_name`）和"怎么说"（`response`），系统流程负责"怎么问、何时停、问完怎么回到原处"。

### YAML 规则引擎

业务流程不是硬编码在 Python 里的，而是写在 `flow_config/*.yml` 中：

```yaml
refund_request:
  name: 退款申请
  steps:
    - id: start
      type: start
      next: ask_order_number

    - id: ask_order_number
      type: collect                    # 收集类步骤：槽位为空就追问
      slot_name: order_number
      response:
        mode: static
        text: "请告诉我你的订单号。"
      next: ask_refund_reason

    - id: ask_refund_reason
      type: collect
      slot_name: refund_reason
      response:
        mode: static
        text: "请简单说一下退款原因。"
      next: refund_submitted

    - id: refund_submitted
      type: action                     # 动作类步骤：执行一个 Action
      action: action_response
      args:
        mode: static
        text: "好的，订单{{ slots.order_number }}的退款申请已提交，原因是：{{ slots.refund_reason }}。"
      next: end

    - id: end
      type: end
      next: []
```

四种步骤类型：

| 类型 | 作用 | 关键字段 |
|---|---|---|
| `start` | 流程入口（本身不做任何事，只提供 `next`） | `next` |
| `action` | 执行一个 Action（渲染话术 / 调接口） | `action`、`args` |
| `collect` | 收集一个槽位值，空了就转系统流程追问 | `slot_name`、`response`、`validation` |
| `end` | 流程出口 | — |

**改流程只改 YAML，不用动一行 Python。** 这是这套设计最大的收益。

---

## 架构分层

```mermaid
flowchart TB
    subgraph API["API 层 · oldhan/api"]
        direction LR
        A1["app.py<br/>应用生命周期"]
        A2["routers.py<br/>路由"]
        A3["schemas.py<br/>接口契约"]
        A4["deps.py<br/>依赖注入"]
    end

    subgraph APP["应用层"]
        direction LR
        S1["service/dialogue_service.py<br/>流程编排"]
        S2["repository/<br/>状态持久化"]
    end

    subgraph CORE["核心引擎"]
        direction LR
        E1["engine/<br/>对话引擎"]
        E2["plan/<br/>计划模型"]
        E3["task/commands/<br/>命令对象与处理"]
        E4["task/flows/<br/>YAML 规则引擎"]
    end

    subgraph DOMAIN["领域层 · oldhan/domain"]
        direction LR
        D1["messages.py<br/>消息模型"]
        D2["state.py<br/>对话状态"]
        D3["contexts.py<br/>流程上下文"]
    end

    subgraph INFRA["基础设施"]
        direction LR
        I1["database.py<br/>异步引擎"]
        I2["ai_clients.py<br/>LLM 客户端"]
        I3["http_util.py<br/>HTTP 客户端"]
    end

    API --> APP --> CORE --> DOMAIN
    CORE --> INFRA
    APP --> INFRA

    style API fill:#E6F1FB,stroke:#378ADD,color:#042C53
    style APP fill:#FAEEDA,stroke:#BA7517,color:#412402
    style CORE fill:#EEEDFE,stroke:#7F77DD,color:#26215C
    style DOMAIN fill:#E1F5EE,stroke:#1D9E75,color:#04342C
    style INFRA fill:#F1EFE8,stroke:#888780,color:#2C2C2A
```

**依赖方向是单向的**：上层依赖下层，`domain/` 是纯数据结构，不依赖任何东西。这样领域模型可以被所有层自由引用而不会产生循环依赖。

---

## 一次消息的完整旅程

```mermaid
sequenceDiagram
    autonumber
    participant C as 客户端
    participant R as routers
    participant S as DialogueService
    participant Repo as Repository
    participant E as DialogueEngine
    participant DB as MySQL

    C->>R: POST /api/chat
    R->>R: ChatRequest → UserMessage
    R->>S: process_message(user_message)
    S->>Repo: load(sender_id)
    Repo->>DB: SELECT state_json
    DB-->>Repo: JSON 字符串
    Repo-->>S: DialogueState 对象
    S->>E: process(user_message, state)
    Note over E: 准备会话 → 开启本轮 → 轨道分派
    E-->>S: ProcessResult
    S->>Repo: save(state)
    Repo->>DB: INSERT / UPDATE
    S-->>R: ProcessResult
    R->>R: ProcessResult → ChatResponse
    R-->>C: 200 JSON
```

**几个值得注意的点**：

1. **引擎完全无 I/O** —— `DialogueEngine` 只操作传进来的 `DialogueState` 对象，不碰数据库。状态的读写全部由 `DialogueService` 负责，这样引擎可以脱离数据库独立测试。
2. **一进一出两个领域模型** —— 入参 `UserMessage`、出参 `ProcessResult`，都是普通的 `dataclass`（不是 Pydantic），属于领域层。
3. **状态整体序列化** —— `DialogueState` 被序列化成一个 JSON 字符串存进 MySQL 的 `dialogue_states` 表，不拆表。好处是状态结构可以自由演进，无需改 DDL。

---

## 目录结构

```
customer-service-backend/
├── main.py                       # 启动入口（uvicorn）
├── pyproject.toml                # 依赖声明
├── .env                          # 环境变量（LLM / 数据库 / 商城 API）
├── flow_config/                  # ⭐ 流程定义（YAML 规则引擎的"剧本"）
│   ├── user_flows.yml            #   业务任务流程 + 全局槽位声明
│   └── system_flows.yml          #   系统任务流程
└── oldhan/                       # 源码包
    ├── api/                      # 接口层
    │   ├── app.py                #   FastAPI 实例 + lifespan
    │   ├── routers.py            #   /api/chat、/api/chat/history
    │   ├── schemas.py            #   Pydantic 请求/响应模型
    │   └── deps.py               #   依赖注入声明
    ├── conf/
    │   └── config.py             # pydantic-settings 配置加载
    ├── domain/                   # ⭐ 领域层（纯数据结构）
    │   ├── messages.py           #   消息模型
    │   ├── state.py              #   对话状态（含会话/轮次/聚焦对象）
    │   └── contexts.py           #   流程上下文（业务 1 个 + 系统 6 个）
    ├── engine/
    │   ├── dialogue_engine.py    #   对话引擎主流程
    │   └── builder.py            #   引擎装配
    ├── infrastructure/           # 基础设施
    │   ├── database.py           #   异步引擎 + 会话工厂
    │   ├── ai_clients.py         #   LLM 客户端
    │   └── http_util.py          #   HTTP 客户端（调电商后端）
    ├── plan/
    │   └── models.py             # TurnPlan（本轮计划：走哪条轨道）
    ├── repository/
    │   ├── models/dialogue_state.py   # ORM 表映射
    │   └── dialogue_state_repository.py  # load / save
    ├── service/
    │   └── dialogue_service.py   # 状态加载 → 引擎处理 → 状态保存
    ├── task/                     # ⭐ 任务引擎核心
    │   ├── commands/
    │   │   ├── models.py         #   命令对象（4 种）+ 注册表 + from_dict
    │   │   └── processor.py      #   命令处理器（分派 + 应用）
    │   └── flows/
    │       ├── models.py         #   流程/步骤/链路的领域模型
    │       └── loader.py         #   YAML → 对象树
    └── test/                     # 各层独立测试脚本
```

---

## 实现进度

### 已完成

| 模块 | 内容 | 状态 |
|---|---|---|
| **配置层** | `pydantic-settings` 加载 `.env`，LLM/数据库/商城 API 三类配置 | ✅ |
| **基础设施** | 异步数据库引擎与会话工厂、LLM 客户端、HTTP 客户端 | ✅ |
| **领域模型** | 消息模型、对话状态（Session/Turn/FocusedObject）、9 个流程上下文 | ✅ |
| **序列化** | 全链路 `to_dict` / `from_dict`（支持嵌套还原） | ✅ |
| **持久化** | MySQL 表映射 + `load`（空状态兜底）+ `save`（upsert） | ✅ |
| **服务层** | 状态加载 → 引擎处理 → 状态保存 | ✅ |
| **API 层** | 生命周期管理、依赖注入链、对话接口、历史接口 | ✅ |
| **YAML 加载** | 15 个流程领域模型 + 加载器（含槽位定义解析） | ✅ |
| **命令体系** | 4 种命令对象 + 类型注册表 + JSON 转对象 | ✅ |
| **命令处理** | 分派器 + 启动/填槽/取消/恢复 四个处理器 | ✅ |
| **流程配置** | 业务流 6 个 + 系统流 6 个（约 400 行 YAML） | ✅ |

### 进行中

| 模块 | 内容 | 状态 |
|---|---|---|
| **对话引擎** | 主流程骨架（会话准备 → 开启轮次 → 分派 → 提交）已完成 | 🔄 |
| **消息处理** | `_handle_text_message` / `_handle_object_message` 待接入轨道 | 🔄 |

### 待实现

| 模块 | 内容 |
|---|---|
| **意图识别** | Prompt 模板 + LLM 调用 + `TurnPlan` 解析器（字符串 → 对象） |
| **流程执行器** | `FlowExecutor`：读 `step_id` 定位步骤、按 `next` 推进、处理条件分支 |
| **Action 体系** | `action_response`（话术渲染）、`action_listen`（等待用户）等 |
| **任务处理器** | `TaskHandler`：串联命令处理器与流程执行器 |
| **计划校验** | `TurnPlanValidator`：三轨道互斥校验 + 澄清兜底 |
| **知识轨道** | 知识源检索 + 回答生成 |
| **闲聊轨道** | 闲聊兜底回复 |

---

## 设计图与实现对照

本项目的完整设计图存档在 [`docs/images/`](docs/images)，按模块顺序列在下面。每张图下方标注**当前代码的实现状态**，方便对照"设计要做什么"和"已经做到哪"。

> **状态图例**：✅ 已实现 ｜ 🔄 部分实现（骨架就绪，逻辑待补） ｜ ⬜ 尚未开始

---

### 01 · 项目设计理念与系统整体架构

![项目设计理念与系统整体架构](docs/images/01-overview.png)

| 设计要素 | 状态 | 对应实现 |
|---|:---:|---|
| 三轨道并行设计（task / knowledge / chitchat） | ✅ | `plan/models.py` 的三轨道模型 |
| 召回用户状态（会话 / 任务 / 历史） | ✅ | `domain/state.py` + `repository/` |
| 意图识别（调用 LLM） | ⬜ | 待实现 `TurnPlanner` + Prompt 模板 |
| 规则引擎（YAML）与 `TaskHandler` | 🔄 | `task/flows/`、`task/commands/` 已完成，执行器待补 |
| MySQL 用户对话状态 | ✅ | `dialogue_states` 表 + `load` / `save` |
| 外部知识源（业务后端 / RAG / FAQ） | ⬜ | `infrastructure/http_util.py` 已就绪，Provider 待实现 |

---

### 02 · 分层设计与消息处理流程

![分层设计与消息处理流程](docs/images/02-layers.png)

| 层 | 状态 | 对应实现 |
|---|:---:|---|
| API 层（对话接口 / 历史接口） | ✅ | `api/routers.py`、`api/schemas.py` |
| Service 层（状态加载 → 引擎处理 → 状态保存） | ✅ | `service/dialogue_service.py` |
| Repository 层（持久化访问） | ✅ | `repository/dialogue_state_repository.py` |
| Engine 层（意图识别 → 校验 → 分派） | 🔄 | `engine/dialogue_engine.py` 六步主流程骨架已完成 |
| Handler 层（`TaskHandler` / `KnowledgeHandler` / `ChitchatHandler` / `ClarifyResponder`） | ⬜ | 待实现 |
| `TurnPlanner` / `TurnPlanValidator` | ⬜ | 待实现 |

---

### 03 · API 接口定义

![API 接口定义](docs/images/03-api.png)

| 接口 / 模型 | 状态 | 对应实现 |
|---|:---:|---|
| `POST /api/chat`（对话接口） | ✅ | `api/routers.py` |
| `GET /api/chat/history`（历史记录接口） | 🔄 | 路由与响应模型已完成，数据来源暂为固定示例 |
| 交互模型（`ChatRequest` / `ChatResponse` / `ChatObjectPayload`） | ✅ | `api/schemas.py`（Pydantic） |
| 领域模型（`UserMessage` / `ProcessResult`） | ✅ | `domain/messages.py`（dataclass） |
| 消息类型 TEXT / OBJECT 双形态 | ✅ | `MessageType` 枚举 + 路由内转换 |

---

### 04 · Service 层与 Repository 层

![Service 层与 Repository 层](docs/images/04-service-repository.png)

| 设计要素 | 状态 | 对应实现 |
|---|:---:|---|
| 交互模型与领域模型的职责分离 | ✅ | `api/schemas.py`（Pydantic）↔ `domain/messages.py`（dataclass） |
| `DialogueService.process_message` 四步编排 | ✅ | `service/dialogue_service.py` |
| `load()`：查不到时返回**空状态**而非 `None` | ✅ | `DialogueStateRepository.load` |
| `save()`：存在则更新、不存在则插入（upsert） | ✅ | `DialogueStateRepository.save` |
| 状态整体存 JSON（不拆表） | ✅ | `dialogue_states(sender_id, state_json)` |

---

### 05 · DialogueState 数据结构

![DialogueState 数据结构](docs/images/05-dialogue-state.png)

| 设计要素 | 状态 | 对应实现 |
|---|:---:|---|
| `DialogueState` 顶层字段（任务 / 挂起 / 系统任务 / 聚焦对象 / 会话） | ✅ | `domain/state.py` |
| `TaskContext`（`flow_id` + `step_id` + `slots`） | ✅ | `domain/contexts.py` |
| `SystemContext` 抽象基类 + **6 个系统任务子类** | ✅ | `domain/contexts.py` |
| `FocusedObject`（用户聚焦的订单/商品） | ✅ | `domain/state.py` |
| `Session` / `Turn`（会话与轮次，2 小时超时） | ✅ | `domain/state.py` |
| `pending_turn`（本轮暂存，**不参与持久化**） | ✅ | `begin_turn` / `fill_pending_turn` / `commit_pending_turn` |
| 系统上下文的 `to_dict` / `from_dict` 与分发字典 | ✅ | `SYSTEM_CONTEXT_DICT` |

---

### 06 · DialogueEngine 业务逻辑流程

![DialogueEngine 业务逻辑流程](docs/images/06-engine-flow.png)

| 设计要素 | 状态 | 对应实现 |
|---|:---:|---|
| 六步主流程（准备会话 → 开启轮次 → 分派 → 回填 → 提交 → 返回） | ✅ | `engine/dialogue_engine.py::process` |
| 会话超时判断与自动新建会话 | ✅ | `_prepare_session` |
| 按消息类型分流 TEXT / OBJECT | ✅ | `process` 中的 `if user_message.type` |
| 文本轨道：`TurnPlanner` → `TurnPlanValidator` → 分派 | ⬜ | 待实现 |
| 对象轨道：存储聚焦对象 → 生成填充命令 | 🔄 | `domain/state.py` 已支持聚焦对象；命令生成待补 |
| 分派到 4 个 Handler | ⬜ | 待实现 |
| 回填本轮回复并提交到会话 | ✅ | `fill_pending_turn` / `commit_pending_turn` |

---

### 07 · TurnPlanner 组件输出结果的约束

![TurnPlanner 组件输出结果的约束](docs/images/07-turnplanner-output.png)

| 设计要素 | 状态 | 对应实现 |
|---|:---:|---|
| `TurnPlan` JSON 结构（task / knowledge / chitchat） | ✅ | `plan/models.py` |
| 四种 task 命令（启动 / 填槽 / 取消 / 恢复） | ✅ | `task/commands/models.py` + 类型注册表 |
| 命令 JSON → 对象转换 | ✅ | `Command.from_dict`（查注册表 + 展开构造） |
| 知识意图（`KnowledgeIntent` 定义表） | ⬜ | 待实现 |
| 知识来源路由（商品/订单/操作/政策 Provider） | ⬜ | 待实现 |

---

### 08 · TurnPlanner 制作流程与 TurnPlan 数据模型

![TurnPlanner 制作流程与 TurnPlan 数据模型](docs/images/08-turnplanner-flow.png)

| 设计要素 | 状态 | 对应实现 |
|---|:---:|---|
| 渲染提示词（`available_flows` / `knowledge_intents` / `active_task` / `interrupted_tasks` / `focused_object` / 对话历史） | ⬜ | 待实现 | 
| 调用 LLM 得到结构化命令 | ⬜ | 待实现 |
| 对 `json` 结果解析成 `TurnPlan` 对象 | 🔄 | `plan/models.py` 已有 `from_dict`，解析器（字符串 → 字典）待补 |
| `TurnPlan` / `TaskTurnPlan` / `KnowledgeTurnPlan` / `ChitChatTurnPlan` | ✅ | `plan/models.py` |
| `Command` 基类 + 四个子类 | ✅ | `task/commands/models.py` |

---

### 09 · TaskHandler 实现思路

![TaskHandler 实现思路](docs/images/09-taskhandler.png)

| 设计要素 | 状态 | 对应实现 |
|---|:---:|---|
| `TaskHandler`（串联命令处理与流程执行） | ⬜ | 待实现 |
| `CommandProcessor`：按命令类型分派并修改状态 | ✅ | `task/commands/processor.py` |
| `FlowExecutor`：双层循环推进流程步骤 | ⬜ | 待实现 |
| `ActionRunner`：执行 Action 并回收消息 | ⬜ | 待实现 |
| `FlowsList`（全局流程定义，启动时加载一次） | ✅ | `task/flows/models.py` + `loader.py` |

---

### 10 · Flow 数据模型

![Flow 数据模型](docs/images/10-flow-model.png)

| 设计要素 | 状态 | 对应实现 |
|---|:---:|---|
| `FlowsList` / `Flow` / `FlowSlot` | ✅ | `task/flows/models.py` |
| `FlowStep` 基类 + 四种步骤（start / end / action / collect） | ✅ | `task/flows/models.py` |
| `FlowStepLink` + 三种跳转（静态 / 条件 / 兜底） | ✅ | `task/flows/models.py` |
| `ResponseDefinition`（话术定义）/ `SlotValidation`（槽位校验） | ✅ | `task/flows/models.py` |
| YAML → 对象树加载 | ✅ | `task/flows/loader.py` |
| 全局槽位声明（`user_flows.yml` 顶部 8 个 slot） | ✅ | `flow_config/user_flows.yml` |

---

### 11 · CommandProcessor 组件

![CommandProcessor 组件](docs/images/11-command-processor.png)

| 设计要素 | 状态 | 对应实现 |
|---|:---:|---|
| 按命令类型 `isinstance` 分派 | ✅ | `CommandProcessor.process_command` |
| `start_flow`：有无活跃任务两条分支（新建 / 打断并播报） | ✅ | `_handle_start_flow` |
| `set_slots`：写入状态槽位 | ✅ | `_handle_set_slots` |
| `cancel_flow`：取消任务 + 播报系统任务 | ✅ | `_handle_cancel_flow` |
| `resume_flow`：有无活跃任务两条分支（挂起后恢复 / 直接恢复） | ✅ | `_handle_resume_flow` |

---

## 技术栈

| 类别 | 选型 | 用途 |
|---|---|---|
| 语言 | **Python 3.12+** | 使用 `dataclass(slots=True)`、`X \| None` 等新语法 |
| Web 框架 | **FastAPI** | 异步接口、依赖注入、生命周期管理 |
| ASGI 服务器 | **Uvicorn** | 开发热重载 |
| ORM | **SQLAlchemy 2.0**（async） | 异步 ORM + `async_sessionmaker` |
| 数据库驱动 | **aiomysql** | MySQL 异步驱动 |
| 数据库 | **MySQL 8.4** | 对话状态持久化 |
| LLM 编排 | **LangChain** + langchain-openai | Prompt 模板、模型调用、输出解析 |
| 配置管理 | **pydantic-settings** | `.env` → 类型化配置对象 |
| 流程规则 | **PyYAML** | YAML 流程定义解析 |
| 模板引擎 | **Jinja2** | 话术模板渲染（`{{ slots.xxx }}`） |
| 包管理 | **uv** | 依赖解析与虚拟环境 |

---

## 快速开始

### 1. 环境要求

- Python 3.12 或更高
- MySQL 8.x（或用 Docker 起一个）
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip

### 2. 安装依赖

```bash
cd customer-service-backend

# 用 uv（推荐）
uv sync

# 或者用 pip
python -m venv .venv
.venv/Scripts/activate      # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -e .
```

### 3. 配置环境变量

在 `customer-service-backend/` 下创建 `.env`：

```ini
# ── 大模型 ──────────────────────────────────
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# ── 数据库 ──────────────────────────────────
DATABASE_URL=mysql+aiomysql://user:password@127.0.0.1:3306/customer_service?charset=utf8mb4

# ── 电商业务服务（Mock） ─────────────────────
COMMERCE_API_BASE_URL=http://127.0.0.1:18081

# ── 服务端口 ────────────────────────────────
APP_HOST=0.0.0.0
APP_PORT=18082
```

### 4. 初始化数据库

只需要一张表，状态整体存 JSON：

```sql
CREATE DATABASE IF NOT EXISTS customer_service
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE customer_service;

CREATE TABLE IF NOT EXISTS dialogue_states (
  sender_id  VARCHAR(255) NOT NULL PRIMARY KEY COMMENT '用户标识',
  state_json TEXT         NOT NULL COMMENT '完整对话状态（JSON）'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5. 启动

```bash
# 方式一：直接跑入口文件
python main.py

# 方式二：用 uvicorn
uvicorn oldhan.api.app:app --host 0.0.0.0 --port 18082 --reload
```

启动后访问交互式文档：**http://127.0.0.1:18082/docs**

---

## API 接口

### `POST /api/chat` — 对话接口

请求：

```json
{
  "sender_id": "u1001",
  "message_id": "msg_001",
  "text": "我要退款",
  "object": null
}
```

也支持发送**业务对象**（用户在界面上点了一张订单卡片）：

```json
{
  "sender_id": "u1001",
  "message_id": "msg_002",
  "text": null,
  "object": {
    "type": "order",
    "id": "B20260409001",
    "title": "罗技 MX Master 3S 鼠标",
    "attributes": { "source": "order_list" }
  }
}
```

响应：

```json
{
  "sender_id": "u1001",
  "message_id": "msg_001",
  "messages": [
    { "text": "好的，我们先处理退款申请。", "object": null },
    { "text": "请告诉我你的订单号。", "object": null }
  ]
}
```

> 注意 `messages` 是**数组**：一轮对话可能产生多条回复（系统任务播报一条、业务任务追问一条）。

### `GET /api/chat/history` — 历史记录

| 参数 | 类型 | 说明 |
|---|---|---|
| `sender_id` | string | 用户标识 |

```json
{
  "sender_id": "u1001",
  "messages": [
    { "role": "user", "text": "我要退款", "object": null },
    { "role": "bot",  "text": "请告诉我你的订单号。", "object": null }
  ]
}
```

---

## 数据模型

对话状态是一棵**嵌套对象树**，整体序列化成 JSON 存库：

```mermaid
flowchart LR
    DS["DialogueState<br/>用户对话状态"]

    DS --> AT["active_task<br/>当前业务任务"]
    DS --> PT["paused_tasks<br/>被挂起的任务"]
    DS --> AS["active_system_task<br/>当前系统任务"]
    DS --> FO["focused_object<br/>聚焦对象"]
    DS --> SS["sessions<br/>历史会话"]

    AT --> SL["slots<br/>已收集的数据"]
    AS --> SC["上下文参数<br/>slot_name / reason / 流程名"]

    SS --> TU["turns<br/>每一轮"]
    TU --> IM["input_message<br/>用户消息"]
    TU --> AM["assistant_messages<br/>机器人回复"]

    style DS fill:#EEEDFE,stroke:#7F77DD,color:#26215C
    style AT fill:#E1F5EE,stroke:#1D9E75,color:#04342C
    style AS fill:#FAEEDA,stroke:#BA7517,color:#412402
    style SL fill:#EAF3DE,stroke:#639922,color:#173404
    style SS fill:#E6F1FB,stroke:#378ADD,color:#042C53
```

| 字段 | 作用 |
|---|---|
| `active_task` | 用户正在办的业务任务（含 `flow_id` / `step_id` / `slots`） |
| `paused_tasks` | 被临时打断的任务（用户问了个其它问题，办完再回来） |
| `active_system_task` | 引擎内部激活的系统任务（播报 / 追问），优先级高于业务任务 |
| `focused_object` | 用户最近一次交互的业务对象（订单/商品卡片） |
| `sessions` | 历史会话，**同一会话内 2 小时无交互即自动开启新会话** |
| `current_session_id` | 当前活跃会话的 ID |

### 两个容易混淆的概念

|  | `flows`（FlowsList） | `DialogueState` |
|---|---|---|
| 是什么 | **剧本** —— 有哪些流程、每步怎么走 | **进度** —— 谁演到哪了 |
| 生命周期 | 应用启动时加载一次，全局共享 | 每个用户一份，每轮读写 |
| 可变吗 | 只读 | 每轮都在变 |
| 存哪 | 内存 | MySQL |

---

## 设计要点

### 1. 状态是持久化的，不是靠模型"记住"

每轮对话结束，整个 `DialogueState` 被序列化写回 MySQL。下一轮开始时读回来。所以：

- **用户换个设备、隔天再来，业务还能接着办** —— 进度在 `slots` 里
- **模型完全无状态** —— 它每次只看到当前这一轮拼好的上下文（含历史 + 当前状态）

### 2. 命令对象化

模型输出的命令是 JSON：

```json
{ "command": "start_flow", "flow": "refund_request" }
```

但引擎内部流转的是**对象**：

```python
StartFlowCommand(command="start_flow", flow="refund_request")
```

转换在 `task/commands/models.py` 完成，靠一张"命令名 → 类"的注册表查表构造。这样做的好处：

- **字段名拼错当场报错**，而不是悄悄变成 `None`
- **类型化**：`StartFlowCommand` 有 `flow`、`SetSlotsCommand` 有 `slots`，各不相同
- **可多态分派**：一个 `List[Command]` 里混装各种命令，用 `isinstance` 找到对应处理器

### 3. 话术全部走配置

机器人说的每一句话都在 YAML 里，Python 只负责"渲染"：

```yaml
text: "好的，我们先处理{{ context.started_flow_name }}。"
text: "好的，订单{{ slots.order_number }}的退款申请已提交。"
```

两个命名空间是分开的：

| 变量 | 来源 |
|---|---|
| `{{ slots.xxx }}` | 业务任务收集到的数据槽位 |
| `{{ context.xxx }}` | 当前系统任务的上下文参数 |

### 4. 引擎无 I/O

`DialogueEngine.process()` 只接收 `DialogueState` 对象、返回 `ProcessResult`，**不碰数据库、不发网络请求**。所有 I/O 都在 `service/` 和 `infrastructure/` 层完成。

这让引擎可以脱离数据库跑单元测试 —— `oldhan/test/` 下的脚本就是这么做的。

---

## 相关文档

| 文档 | 内容 |
|---|---|
| `flow_config/user_flows.yml` | 业务流程定义 + 全局槽位声明 |
| `flow_config/system_flows.yml` | 系统流程定义 |

---

<div align="center">

<sub>本项目为个人学习实践作品，用于理解企业级对话系统的工程化实现</sub>

</div>
