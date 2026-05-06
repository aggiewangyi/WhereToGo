# 旅行智能体与 LangGraph 编排 — 技术说明

本文档整理「去哪玩」后端中与 **多智能体对话、TripBot 技能注入、用户长期记忆、交互模式、LangGraph 检查点与中断** 相关的实现，便于深度阅读代码与二次扩展。

---

## 1. 总览：请求从进入到 SSE 出去

```
客户端 POST /api/v1/agent/chat（工具服务；可选请求头 `X-Agent-API-Key`）
    → resolve_session_and_prior_messages（会话 + 历史消息）
    →（可选）写入 interaction_mode 到 chat_sessions + 用户 travel_memory 默认模式
    → chat_service.stream_chat_events
    → multi_agent_completion（仅当 CHAT_MULTI_AGENT=true 且传入 db）
        → 组装 SystemMessage（跨会话记忆 + verbose/quiet 说明）
        → 清空 legacy pending_prep_payload（与 LangGraph 中断并存时避免双轨）
        → 组装 intent / planner / prep 工具列表（含超时包装）
        → stream_langgraph_travel_chat（LangGraph 单图 + 检查点）
    → SSE：event: session | text | phase | tool_start | tool_end | interrupt | error | done
    → persist_user_and_assistant
    →（可选）merge_feedback_after_turn → users.travel_memory
```

**单智能体回退**：`CHAT_MULTI_AGENT=false` 时仍走 `app/ai/agent.py` 的单个 `create_react_agent`，不经过本文所述 LangGraph 路径。

---

## 2. TripBot 技能与系统提示（行为层，非独立进程）

**目的**：把 Cursor 侧 TripBot skills（framework / research / itinerary / booking / prep / export）的**工作流约束**写进固定系统提示，使三个 LLM 角色（意图 / 行程 / 行前）在**同一套产品话术**下工作。

| 文件 | 作用 |
|------|------|
| `app/ai/prompts/tripbot_skills.py` | 定义三段可拼接字符串：`TRIPBOT_INTENT_APPEND`、`TRIPBOT_PLANNER_APPEND`、`TRIPBOT_PREP_APPEND` |
| `app/ai/prompts/multi_agent.py` | `INTENT_AGENT_SYSTEM` / `PLANNER_AGENT_SYSTEM` / `PREP_AGENT_SYSTEM` 末尾拼接上述片段 |
| `app/ai/prompts/planner.py` | 单智能体 `SYSTEM_PROMPT_01` 拼接 `TRIPBOT_INTENT_APPEND`，并与多智能体一致的「目的地锁定」移交句式对齐 |

**行程智能体工具名修正**：`PLANNER_AGENT_SYSTEM` 中工具说明与真实实现一致——`get_location`、`plan_route`、`search_nearby`（不再使用不存在的 `search_poi` / `get_distance` / `get_direction`）。

**意图移交**：下游仍依赖 `profile_merge.extract_locked_destination` 所匹配的 **`目的地锁定为【地名】`** 句式；TripBot 片段要求在同一前提下补齐框架信息。

---

## 3. 跨会话用户记忆与交互模式

### 3.1 数据模型

| 存储 | 字段 | 含义 |
|------|------|------|
| `users` | `travel_memory` | JSON，对应 `PersistentTravelMemory`（满意/不满短句、隐含需求摘要、默认交互模式、近期目的地、标签等） |
| `chat_sessions` | `interaction_mode` | `verbose` / `quiet`，会话级覆盖 |
| `chat_sessions` | `langgraph_thread_id` | LangGraph 检查点 `thread_id`（UUID 字符串） |
| `chat_sessions` | `pending_prep_payload` | **遗留字段**；多智能体主路径在每次编排前会 **清空**，行前「待确认」由 **LangGraph interrupt** 接管 |

迁移：`alembic/versions/f3a4b5c6d7e8_*`（travel_memory + interaction_mode）、`g5h6i7j8k9l0_*`（langgraph_thread_id）。

### 3.2 交互模式优先级

实现于 `orchestrator._effective_interaction_mode`：

1. 本次请求 `ChatRequest.interaction_mode`
2. 否则 `chat_sessions.interaction_mode`
3. 否则 `PersistentTravelMemory.default_interaction_mode`
4. 默认 **`quiet`**

### 3.3 与 LangGraph 编排的关系

- **`quiet` / `verbose` 均不改变图的边**：行程草案后始终在 `human_gate` 内 **`interrupt({...})`** 挂起，需用户下一轮明确确认或取消后，服务端以 **`Command(resume=...)`** 续跑至 `prep_context` → `prep` 或结束。
- **差异仅在「频率感」**：系统提示（`memory_prompt` 的 QUIET/VERBOSE 块）与 `human_gate` / SSE 里 **`hint`、等待提示** 的详略——`verbose` 长说明，`quiet` 短句；**不**存在 quiet 一轮内自动跳过确认进入行前。

### 3.4 反馈写回记忆

- 配置：`CHAT_FEEDBACK_MEMORY`（默认 `true`）。
- 流程：`app/services/travel_user_memory.py` 中 `merge_feedback_after_turn`，在 **助手全文落库之后** 调用；内部用 `feedback_extract.extract_feedback_delta` 结构化抽取满意/不满/隐含一句，再与 `PersistentTravelMemory.merge_delta` 合并写回 `users.travel_memory`。
- 用户显式传 `interaction_mode` 时：`persist_user_interaction_mode_default` 同步更新用户级默认模式（`chat.py` 在流式/非流式入口均调用）。

---

## 4. LangGraph：单图、状态、检查点、线程与恢复

### 4.1 图结构（`app/ai/multi_agent/langgraph_engine.py`）

```
START
  → intent          （create_react_agent + INTENT_AGENT_SYSTEM）
  → [条件边]        未锁定目的地 → END
  → inject_profile  （异步：结构化画像 + 桥接 HumanMessage + profile_dict/plan_days）
  → planner         （create_react_agent + PLANNER_AGENT_SYSTEM）
  → human_gate      （同步：interrupt 挂起，待用户确认后再 prep_context）
  → prep_context    （异步：追加行前任务 HumanMessage）
  → prep            （create_react_agent + PREP_AGENT_SYSTEM）
  → END
```

**状态 `TravelGraphState`**：

- `messages`：`Annotated[..., add_messages]`，主对话通道。
- `profile_dict` / `plan_days`：注入节点写入，供 `prep_context` 使用（带简单 merge reducer）。

三个「子图」本质都是 **`create_react_agent` 编译出的子图节点**；父图通过 `astream_events(..., subgraphs=True)` 把子图内 LLM/工具事件透出到 SSE。

### 4.2 检查点（Checkpointer）

- **`get_travel_checkpointer()`** 单例：
  - 若配置了非空 `LANGGRAPH_SQLITE_PATH`，尝试 `langgraph.checkpoint.sqlite.SqliteSaver.from_conn_string`（父目录自动创建）。
  - 失败或未配置则 **`MemorySaver`**（进程内，重启丢失）。
- 图编译：`graph.compile(checkpointer=get_travel_checkpointer())`。

生产环境建议固定 SQLite 路径，便于多 worker 共享同一检查点文件（需注意文件锁与备份策略）。

### 4.3 `thread_id` 与 `chat_sessions.langgraph_thread_id`

**绑定关系**：检查点配置为 `{"configurable": {"thread_id": <UUID>}}`，该 UUID 持久化在 **`chat_sessions.langgraph_thread_id`**（有会话且走 DB 时）。

**一轮新规划（无未决 interrupt）**：

1. 从 DB 读出旧 `langgraph_thread_id`（若有）。
2. `aget_state`：若无 `interrupts`，认为上一轮已结束，**尝试删除**该线程的检查点（`_try_delete_checkpoint_thread`，兼容不同 checkpointer API）。
3. 生成 **新 UUID**，`set_langgraph_thread_id`，再 `astream_events` 传入 `{"messages": messages_for_model}`。

**处于 interrupt 等待中**：

1. `aget_state` 存在 **`interrupts`**。
2. 用 `prep_handoff` 解析用户本轮输入：
   - 确认类 → `Command(resume=True)`
   - 取消类 → `Command(resume=False)`
   - 其它短句 → **不调用图**，直接文本提示仍等待确认（避免误 resume）。
3. 恢复时 **不再** 传整段 `messages`，只传 `Command(resume=...)`。

**图正常结束且无未决 interrupt**：`clear_langgraph_thread_id`，便于下一轮分配新线程。

**无 `session_id` 的调用**（兼容）：不读写 DB；每次使用 **临时 UUID** 作为 `thread_id`，无法在多次 HTTP 请求间恢复 interrupt（仅适合无状态测试）。

### 4.4 SSE 与 `interrupt` 事件

除原有 `text` / `phase` / `tool_*` / `error` / `done` 外，在 **流结束且 `aget_state` 仍带 `interrupts`** 时，会多一次：

- `event: interrupt`
- `data`: `{"payload": {"kind": "confirm_prep", "hint": "<与 _after_planner_hint_for_mode(interaction_mode) 一致>"}}`

前端可据此展示「待确认行程」条，用户继续发普通文本即可（由服务端解析是否 resume）。

### 4.5 与旧 `pending_prep_payload` 的关系

- 编排入口在存在 `session_id` 时会 **`clear_pending_prep_payload`**，避免 MySQL 里旧 JSON 与 LangGraph 中断双轨并存导致逻辑混乱。
- 若业务仍需读取历史 `pending_prep_payload`（审计/迁移），需在别处显式处理；当前主路径不再依赖其驱动 Prep。

---

## 5. API 与请求体扩展

**`ChatRequest`**（`app/schemas/chat.py`）：

- `interaction_mode: "verbose" | "quiet" | null`：会话 + 用户默认记忆写入见上文。

**`chat_service`**：向 `multi_agent_completion` 透传 `user_id`、`interaction_mode`。

---

## 6. 配置项一览（`app/core/config.py` + `.env.example`）

| 变量 | 含义 |
|------|------|
| `CHAT_MULTI_AGENT` | 是否走多智能体（LangGraph）路径 |
| `CHAT_FEEDBACK_MEMORY` | 是否在每轮后合并反馈到 `travel_memory` |
| `LANGGRAPH_SQLITE_PATH` | LangGraph SqliteSaver 路径；空则 MemorySaver |
| 既有 | `AGENT_TOOL_TIMEOUT_SEC`、`CHAT_STREAM_LLM`、`AGENT_LLM_*` 等仍作用于各 ReAct 子图 |

---

## 7. 已删除 / 弱依赖模块

- **`app/ai/multi_agent/trip_stategraph.py`**：原「顺序 intent→planner + text_holder」已删除；逻辑由 **LangGraph 单图** 替代。
- **`docs/itinerary-malaysia-kl-langkawi-4d.md`**：示例行程导出（与编排无运行时耦合）。

---

## 8. 建议阅读顺序（源码）

1. `app/api/v1/agent.py` + `app/api/deps_agent.py` — 工具鉴权、SSE 与记忆后处理  
2. `app/services/chat_service.py` — 多智能体分支与参数传递  
3. `app/ai/multi_agent/orchestrator.py` — 系统前缀、工具、调用 LangGraph  
4. `app/ai/multi_agent/langgraph_engine.py` — 图、检查点、线程生命周期、流式映射  
5. `app/ai/prompts/multi_agent.py` + `tripbot_skills.py` — 三角色提示与 TripBot 对齐  
6. `app/ai/multi_agent/profile_merge.py` + `prep_handoff.py` — 目的地锁定与确认/取消解析  
7. `app/ai/schemas/persistent_travel_memory.py` + `app/services/travel_user_memory.py` + `app/crud/travel_memory.py` — 长期记忆  
8. `app/crud/chat.py` — `langgraph_thread_id` / `interaction_mode` / pending 清理  

---

## 9. 扩展与风险（供架构决策）

| 主题 | 说明 |
|------|------|
| **多 worker** | MemorySaver 不跨进程；生产务必配置 **SQLite 或远程 checkpointer**，并评估并发写 SQLite |
| **interrupt 与节点重入** | LangGraph 约定：resume 后 **含 `interrupt()` 的节点从头执行**；`interrupt()` 第二次应直接得到 resume 值（官方 HITL 模式）；若升级 LangGraph 行为变化需回归 |
| **子图与上下文长度** | `prep_context` 仅追加一条 `HumanMessage`，行前模型仍能看到完整 `messages` 历史；若 token 压力过大，可改为 `RemoveMessage` 裁剪（需核对当前 LangChain 版本 API） |
| **与 `trip_service.generate_trip_plan` 的关系** | 代码库内仍有该一次性生成函数，**当前无对外 HTTP**；与 Agent 对话未统一时可按需再接或删除死代码 |

---

## 10. 运维检查清单

- [ ] 执行 `alembic upgrade head`（含 `travel_memory`、`interaction_mode`、`langgraph_thread_id`）  
- [ ] 生产设置 `LANGGRAPH_SQLITE_PATH` 到可持久卷  
- [ ] 前端识别 `event: interrupt`（可选但推荐）  
- [ ] 按需关闭 `CHAT_FEEDBACK_MEMORY` 以降低延迟与模型成本  

---

*文档版本与仓库实现同步；若你后续改动图结构或 API，请同步更新本节与「建议阅读顺序」中的路径。*
