# 去哪玩 (WhereToGo) — 产品设计文档

> 版本: v0.2.0 | 日期: 2026-03-30 | 状态: 迭代实现中

---

## 一、产品定位

**一句话定义**: 基于 AI 的一站式智能出行规划平台 —— 从灵感到落地，全链路解决"去哪玩、怎么玩、和谁玩"。

**核心价值主张**: 用户只需表达模糊的出行意愿（如"五一想去海边，预算 3000"），系统即可完成从目的地推荐、行程编排、预算拆分、票务预订到装备清单的全流程服务。

---

## 二、目标用户

| 用户画像 | 典型场景 | 核心痛点 |
|---------|---------|---------|
| 上班族（22-35岁） | 周末/小长假短途游 | 没时间做攻略，希望拿来即用 |
| 大学生/背包客 | 穷游/间隔年 | 预算敏感，需要性价比最优解 |
| 家庭用户 | 亲子游/长辈出行 | 行程需兼顾老幼，需了解当地注意事项 |
| 出境游用户 | 第一次去某国 | 签证材料、当地法律、文化禁忌不了解 |
| 自由行爱好者 | 深度游/小众目的地 | 找不到靠谱信息源 |

---

## 三、核心问题 → 功能模块映射

### 3.1 智能攻略生成（解决：做攻略麻烦）

**问题分析**: 传统攻略需要用户在小红书、马蜂窝、知乎等多平台搜集信息，耗时数小时甚至数天。

**解决方案**:

- **AI 攻略引擎**: 用户输入自然语言需求（目的地/时间/人数/偏好/预算），AI 自动生成结构化行程单
- **攻略模板库**: 提供经过验证的热门攻略模板，支持一键复制 + 自定义修改
- **实时信息增强**: 通过联网能力获取目的地实时天气、开放状态、门票价格等信息
- **多日行程编排**: 按天拆分、智能路线规划（最短路径 / 最优时间分配），支持拖拽调整

**输出物**:
```
📋 行程单（按天/按时段）
├── 每日景点/活动安排（含开放时间、预计停留时长）
├── 交通接驳建议（景点间如何到达、预计时间和费用）
├── 餐饮推荐（按区域 + 预算 + 口味偏好）
└── 备选方案（雨天 Plan B）
```

---

### 3.2 智能目的地推荐（解决：找不到合适的地方）

**问题分析**: 用户往往只有模糊想法（"想看海""想安静""想体验异域风情"），缺乏将感性需求映射到具体地点的能力。

**解决方案**:

- **意图理解引擎**: 通过多轮对话提炼用户偏好维度
  - 自然景观 vs 人文历史 vs 美食体验 vs 户外运动
  - 人多热闹 vs 小众安静
  - 交通便利度
  - 季节适配度
- **智能匹配算法**: 基于用户画像 + 偏好 + 时间 + 预算，从目的地数据库中推荐 Top-N
- **灵感发现**: 随机推荐 + 热门趋势 + 节庆日历 + "和你口味相似的人去了..."
- **对比视图**: 多个目的地并排对比（费用/天气/飞行时间/签证难度）

---

### 3.3 智能预算管理（解决：预算管理）

**问题分析**: 旅行花费分散在交通、住宿、餐饮、门票、购物等多个类目，用户难以做到事前规划和事中控制。

**解决方案**:

- **预算规划器**:
  - 输入总预算 → AI 按行业均值 + 目的地物价自动拆分到各类目
  - 显示"省钱版 / 舒适版 / 豪华版"三档方案
  - 支持用户手动调整各类目占比，实时联动
- **费用预估引擎**:
  - 联网获取实时机票/酒店/门票价格
  - 基于历史数据预测价格趋势（"再等 2 周机票可能降 15%"）
- **旅途记账**:
  - 支持拍照识别小票、语音记账
  - 实时仪表盘：已花 / 剩余 / 各类目占比
  - 超预算预警

**数据模型**:
```
Budget {
  total: number
  currency: string
  categories: {
    transportation: { planned: number, actual: number }
    accommodation:  { planned: number, actual: number }
    food:           { planned: number, actual: number }
    tickets:        { planned: number, actual: number }
    shopping:       { planned: number, actual: number }
    emergency:      { planned: number, actual: number }  // 建议预留 10%
  }
}
```

---

### 3.4 智能票务助手（解决：订票麻烦 + 出行时间不确定）

**问题分析**: 出行时间不确定导致用户反复查票、比价、纠结，错过最佳购票窗口。

**解决方案**:

- **灵活日期搜索**: 显示前后 ±7 天的价格日历，一眼看出最便宜的出行日
- **价格监控 & 提醒**:
  - 用户设置目标价格 → 系统后台持续监控
  - 降价通知（Push + 微信/短信）
  - 预测最佳购买时机
- **多平台聚合比价**: 聚合携程、飞猪、12306、航司官网等渠道价格
- **一键预订代理**: 通过 API/MCP 对接 OTA 平台完成预订流程
- **改签/退票助手**: 展示各渠道退改政策对比，推荐最灵活的购买方案

**技术实现**:
- 使用 MCP (Model Context Protocol) 连接各票务平台的 Tool Server
- Function Calling 实现：查票 → 比价 → 下单 的自动化工作流
- 定时任务（Cron）驱动价格监控

---

### 3.5 当地百科（解决：当地习惯、习俗、法律）

**问题分析**: 尤其出境游，不了解当地文化和法律可能造成尴尬甚至法律风险。

**解决方案**:

- **目的地知识卡片**: 每个目的地配备结构化信息卡
  ```
  🇯🇵 日本·东京
  ├── 📜 法律须知: 不可在公共场所饮酒（部分区域）、大麻严格违法...
  ├── 🎌 文化习俗: 进屋脱鞋、不要边走边吃、电车内保持安静...
  ├── 💬 常用语/手势: すみません、ありがとう...
  ├── 🔌 实用信息: 电压100V/插头A型、小费文化(无)、营业时间习惯...
  ├── ⚠️ 安全提示: 地震应对、紧急电话110/119...
  └── 🏥 医疗信息: 是否需要疫苗、药店购药指南、保险建议...
  ```
- **AI 问答**: 用户随时提问"在泰国能不能用电子烟？"，实时联网查证后回答
- **入境须知生成器**: 根据用户国籍 + 目的地自动生成签证要求、入境卡填写指南、海关申报注意事项

---

### 3.6 出行方式规划（解决：出行方式选择）

**问题分析**: 城市间、景点间的交通方式多样（飞机/高铁/大巴/自驾/轮渡），用户难以全面比较。

**解决方案**:

- **多模式交通方案**: 对于任意两点，给出所有可行交通方式对比
  ```
  北京 → 上海
  ✈️ 飞机: 2h, ¥600-1200, 需提前1.5h到机场
  🚄 高铁: 4.5h, ¥553, 随到随走
  🚗 自驾: 12h, ¥油费约400+高速约500
  ```
- **市内交通指南**: 地铁线路 / 公交卡购买 / 打车App / 租车建议
- **特殊交通攻略**: 如何预约故宫、如何坐渡轮去鼓浪屿、JR Pass 怎么买最划算

---

### 3.7 装备与穿搭助手（解决：需要准备的材料、装备、穿搭建议）

**问题分析**: 不同目的地、季节、活动类型对装备要求差异巨大，遗漏可能影响体验。

**解决方案**:

- **智能清单生成器**: 根据以下维度自动生成个性化打包清单
  - 目的地 + 季节 → 气候适配穿搭
  - 活动类型（徒步/潜水/滑雪/城市观光）→ 专项装备
  - 出行天数 → 数量建议
  - 出境 → 证件 + 转换插头 + 货币兑换提醒
- **穿搭建议**:
  - 基于目的地天气预报推荐每日穿搭方案
  - 考虑宗教/文化着装要求（如清真寺需长袖长裤）
  - 拍照穿搭建议（"去茶卡盐湖穿红裙出片"）
- **证件材料检查单**:
  ```
  ✅ 护照（有效期 > 6个月）
  ✅ 签证 / 电子签 / 落地签材料
  ✅ 机票行程单
  ✅ 酒店预订确认函
  ✅ 旅行保险单
  ✅ 疫苗接种证明（如需要）
  ⬜ 国际驾照（如需要租车）
  ```

---

### 3.8 旅行搭子招募（解决：旅行搭子招募）

**问题分析**: 独自旅行成本高、体验有限，但找到靠谱的旅伴有信任和安全门槛。

**解决方案**:

- **搭子广场**:
  - 发布出行计划（目的地/时间/人数/预算/期望搭子类型），**帖子绑定发布者 `user_id`**
  - 支持标签匹配：摄影搭子、AA搭子、自驾搭子、女生结伴...
- **申请与审核（已实现逻辑）**:
  - 浏览者提交 **简介 `self_intro` + 留言 `message`**，数据写入 `buddy_applications`，仅**发布者**在「我的招募」中可见
  - 发布者对单条申请 **同意 / 拒绝**；当已同意人数达到 `people_wanted` 时，帖子状态变为 **`full`（前端展示为「已找到」）**
- **智能匹配**:
  - 基于行程重合度 + 兴趣标签 + 预算区间 + 出行风格进行推荐
  - "你们都要在 4/15-4/20 去清迈，且都喜欢咖啡店巡礼"
- **信任与安全机制**:
  - 实名认证 + 芝麻信用 / 微信实名
  - 出行评价体系（搭子间互评）
  - 行程分享给紧急联系人
  - 平台担保模式（共同费用由平台托管）
- **沟通工具**: 内置群聊 + 共享行程单 + AA 记账

---

## 四、系统架构

### 4.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层 (Client)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │
│  │ Web App  │  │ 微信小程序 │  │ iOS/安卓  │  │ API (开放平台) │   │
│  │ (Vue 3)  │  │          │  │ (Flutter)│  │              │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬────────┘   │
│       └──────────────┴──────────────┴───────────────┘           │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTPS / WebSocket
┌───────────────────────────────┴─────────────────────────────────┐
│                      API 网关 (Gateway)                          │
│              Kong / Nginx + Rate Limiting + Auth                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────┐
│                     服务层 (Microservices)                        │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  AI 对话服务  │ │ 攻略生成服务  │ │ 目的地推荐   │               │
│  │  (LLM Core) │ │ (Planner)   │ │ (Recommend)  │               │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘               │
│         │               │               │                       │
│  ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐               │
│  │  预算管理     │ │ 票务聚合     │ │ 当地百科     │               │
│  │  (Budget)   │ │ (Booking)   │ │ (Wiki)      │               │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘               │
│         │               │               │                       │
│  ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐               │
│  │  装备清单     │ │ 搭子社交     │ │ 用户服务     │               │
│  │  (Packing)  │ │ (Social)    │ │ (User)      │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────┐
│                     AI 编排层 (AI Orchestrator)                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │     LangGraph ReAct Agent（真实工具执行闭环）              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │ 查票Tool  │ │ 天气Tool  │ │ 搜索Tool  │ │ 地图Tool  │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │ 汇率Tool  │ │ 签证Tool  │ │ 翻译Tool  │ │ 百科Tool  │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           MCP Server Hub (Tool Server 管理)              │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐          │    │
│  │  │ OTA MCP    │ │ Maps MCP   │ │ Weather MCP│          │    │
│  │  │ (携程/飞猪) │ │ (高德/Google)│ │ (和风天气) │          │    │
│  │  └────────────┘ └────────────┘ └────────────┘          │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐          │    │
│  │  │ Search MCP │ │ Translate  │ │ Payment    │          │    │
│  │  │ (联网搜索)  │ │ MCP (翻译) │ │ MCP (支付) │          │    │
│  │  └────────────┘ └────────────┘ └────────────┘          │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────┐
│                       数据层 (Data)                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  MySQL   │ │  Redis   │ │ Elastic  │ │  MinIO   │          │
│  │ (主数据库) │ │ (缓存/会话)│ │ (搜索)   │ │ (文件存储) │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐                                     │
│  │ MongoDB  │ │  Kafka   │                                     │
│  │ (攻略/百科)│ │ (消息队列) │                                     │
│  └──────────┘ └──────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 AI 编排层详细设计

AI 编排层是系统的核心大脑，负责理解用户意图并协调各个 Tool/MCP 完成任务。

```
用户: "帮我规划五一去厦门3天，预算3000，两个人"
                    │
                    ▼
        ┌─────────────────────┐
        │    Intent Parser     │  ← 意图解析
        │  (LLM + Prompt)     │
        └──────────┬──────────┘
                   │ 解析出: destination=厦门, days=3, budget=3000, people=2
                   ▼
        ┌─────────────────────┐
        │   Task Planner       │  ← 任务拆解
        │  (ReAct Agent)      │
        └──────────┬──────────┘
                   │ 拆解为子任务:
                   │  1. 查询厦门5月天气
                   │  2. 搜索厦门必去景点
                   │  3. 查询机票/高铁价格
                   │  4. 搜索酒店价格
                   │  5. 生成预算分配
                   │  6. 编排行程
                   ▼
        ┌─────────────────────┐
        │  Tool Executor       │  ← LangGraph ToolNode：LLM tool_calls → 执行 libs → ToolMessage 回灌
        │  (LangGraph)        │
        └──────────┬──────────┘
                   │ 收集所有工具返回结果
                   ▼
        ┌─────────────────────┐
        │  Response Composer   │  ← 结果整合 & 行程生成
        │  (LLM + Template)   │
        └──────────┬──────────┘
                   │
                   ▼
          结构化行程单 + 预算表
```

### 4.3 工程实现快照（与代码对齐）

| 能力 | 实现说明 |
|------|----------|
| **Agent** | `langgraph.prebuilt.create_react_agent`：多轮 **tool_calls → ToolNode 执行 → ToolMessage 回传**，直至模型给出最终答复（非仅绑定工具不执行）。 |
| **流式输出** | FastAPI `StreamingResponse` + SSE：`text`（模型 token）、`tool_start` / `tool_end`（工具名与结果摘要）、`error`、`done`。 |
| **联网与工具** | `app/libs/*` 封装 302.AI（Tavily / Search1API / DeepL / 小红书等）；高德、和风天气走独立 API Key；OTA 仍为占位，票务由 Agent 结合 **web_search** 等工具降级查询。 |
| **对话记忆** | **Layer 1（已实现）**：前端 Pinia 保留近期会话，`POST /chat` 携带 `history` + 最新 `message`，服务端拼入 LangChain `messages`。 |
| **目的地数据** | `scripts/seed_destinations.py` 预置多条国内外目的地及 `knowledge_card`（Markdown），避免空库无展示。 |
| **搭子流程** | 申请含 `self_intro` + `message`；`GET /buddies/mine`、`GET /buddies/{id}/applications`、`PATCH /buddies/applications/{id}` 完成发布者审核；满员 `status=full`。 |

### 4.4 对话长记忆分层（路线图）

| 层级 | 状态 | 说明 |
|------|------|------|
| **1. 前端有限缓存** | 已实现 | 浏览器侧保留最近 N 轮，随请求上报 `history`，控制上下文长度。 |
| **2. 服务端全量缓存 + 摘要** | 规划中 | `session` 表持久化全量消息；超长会话做 LLM 摘要压缩，再拼接近窗。 |
| **3. 结构化记忆与知识库** | 规划中 | 会话与事实入库；因果关系 / 知识图谱 / 分词画像；可对接 302.AI Memobase 等长期记忆 API。 |

---

## 五、技术栈选型

### 5.1 后端技术栈

| 层级 | 技术选型 | 选型理由 |
|------|---------|---------|
| **语言/框架** | Python (FastAPI) | AI 生态最成熟，FastAPI 异步性能优异 |
| **包管理** | Poetry | 依赖锁定精确，虚拟环境自动管理 |
| **AI/LLM** | OpenAI GPT-4o / Claude / 通义千问 | 多模型适配，按场景选最优模型 |
| **AI 框架** | LangChain + **LangGraph**（`create_react_agent`） | ReAct 工具闭环、流式 `astream_events` |
| **MCP** | MCP SDK (Python) | 标准化 Tool Server 协议，可插拔工具生态 |
| **向量数据库** | Qdrant / Milvus | 目的地/攻略的语义检索 |
| **主数据库** | MySQL 8.0 | 结构化数据存储，团队熟悉度高 |
| **ORM** | SQLAlchemy 2.0 + aiomysql | 异步 ORM，搭配 Alembic 管理迁移 |
| **文档数据库** | MongoDB | 攻略、百科等半结构化内容存储 |
| **缓存** | Redis | 会话管理、热门查询缓存、限流 |
| **搜索引擎** | Elasticsearch | 目的地全文搜索、攻略搜索 |
| **消息队列** | Kafka / RabbitMQ | 异步任务、价格监控通知 |
| **对象存储** | MinIO / 阿里 OSS | 图片、攻略附件存储 |
| **定时任务** | Celery + Beat | 价格监控、定时推送 |

### 5.2 前端技术栈

| 层级 | 技术选型 | 选型理由 |
|------|---------|---------|
| **Web（当前仓库）** | Vue 3 + Vite + TypeScript | 与现有「去哪玩」前端一致，构建快、组合式 API 清晰 |
| **UI 组件** | Element Plus + Tailwind CSS | 组件齐全 + 原子化样式便于统一视觉 |
| **地图** | 高德地图 SDK / Mapbox | 路线规划、景点标注 |
| **移动端** | Flutter / React Native | 跨平台，一套代码多端运行 |
| **小程序** | Taro / uni-app | 微信小程序快速触达用户 |
| **状态管理** | Zustand / Jotai | 轻量灵活 |
| **实时通信** | WebSocket | AI 对话流式输出、搭子聊天 |

### 5.3 基础设施

| 层级 | 技术选型 |
|------|---------|
| **容器化** | Docker + Kubernetes |
| **CI/CD** | GitHub Actions |
| **监控** | Prometheus + Grafana |
| **日志** | ELK Stack |
| **CDN** | Cloudflare / 阿里云 CDN |
| **API 网关** | Kong / APISIX |

---

## 六、MCP 与 Function Calling 设计

### 6.1 MCP Tool Server 规划

MCP (Model Context Protocol) 用于将外部能力标准化地接入 AI Agent：

```yaml
mcp_servers:
  # 票务查询
  - name: booking-mcp
    tools:
      - search_flights        # 查询航班
      - search_trains          # 查询火车票
      - search_hotels          # 查询酒店
      - get_price_calendar     # 获取价格日历
      - create_price_alert     # 创建降价提醒
      - book_ticket            # 预订下单

  # 地图与导航
  - name: maps-mcp
    tools:
      - geocode                # 地理编码
      - route_planning         # 路线规划
      - nearby_search          # 周边搜索 (餐厅/景点/ATM)
      - transit_directions     # 公共交通方案

  # 天气服务
  - name: weather-mcp
    tools:
      - get_current_weather    # 当前天气
      - get_forecast           # 未来天气预报
      - get_historical_weather # 历史天气 (用于推荐最佳旅行月份)

  # 联网搜索
  - name: search-mcp
    tools:
      - web_search             # 网页搜索
      - news_search            # 新闻搜索 (安全预警等)
      - image_search           # 图片搜索 (目的地图片)

  # 翻译与语言
  - name: translate-mcp
    tools:
      - translate_text         # 文本翻译
      - detect_language        # 语言检测

  # 签证与出入境
  - name: visa-mcp
    tools:
      - get_visa_requirements  # 签证要求查询
      - get_entry_requirements # 入境要求 (疫苗/健康码)

  # 汇率与支付
  - name: finance-mcp
    tools:
      - get_exchange_rate      # 实时汇率
      - convert_currency       # 货币换算
      - get_cost_of_living     # 目的地物价水平
```

### 6.2 Function Calling 定义示例

```json
{
  "name": "search_flights",
  "description": "搜索两地之间的航班信息，返回价格、时间、航司等",
  "parameters": {
    "type": "object",
    "properties": {
      "origin": {
        "type": "string",
        "description": "出发城市或机场代码，如 '北京' 或 'PEK'"
      },
      "destination": {
        "type": "string",
        "description": "到达城市或机场代码，如 '厦门' 或 'XMN'"
      },
      "departure_date": {
        "type": "string",
        "description": "出发日期，格式 YYYY-MM-DD"
      },
      "return_date": {
        "type": "string",
        "description": "返回日期，格式 YYYY-MM-DD，单程可不填"
      },
      "passengers": {
        "type": "integer",
        "description": "乘客人数"
      },
      "cabin_class": {
        "type": "string",
        "enum": ["economy", "business", "first"],
        "description": "舱位等级"
      },
      "flexible_dates": {
        "type": "boolean",
        "description": "是否查看前后浮动日期的价格"
      }
    },
    "required": ["origin", "destination", "departure_date"]
  }
}
```

```json
{
  "name": "generate_packing_list",
  "description": "根据目的地、天气、活动类型和出行天数生成个性化打包清单",
  "parameters": {
    "type": "object",
    "properties": {
      "destination": { "type": "string" },
      "travel_dates": {
        "type": "object",
        "properties": {
          "start": { "type": "string" },
          "end": { "type": "string" }
        }
      },
      "activities": {
        "type": "array",
        "items": { "type": "string" },
        "description": "计划的活动类型，如 ['hiking', 'beach', 'city_tour']"
      },
      "traveler_profile": {
        "type": "object",
        "properties": {
          "gender": { "type": "string" },
          "has_children": { "type": "boolean" },
          "medical_needs": { "type": "array", "items": { "type": "string" } }
        }
      },
      "is_international": { "type": "boolean" }
    },
    "required": ["destination", "travel_dates"]
  }
}
```

---

## 七、核心用户流程

### 7.1 主流程：从灵感到出发

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 💡 灵感  │ → │ 🗺️ 规划  │ → │ 💰 预算  │ → │ 🎫 预订  │ → │ 🎒 准备  │
│         │    │         │    │         │    │         │    │         │
│ "想去海边"│    │ AI生成   │    │ 智能拆分 │    │ 聚合比价 │    │ 装备清单 │
│ 意图对话  │    │ 多日行程  │    │ 三档方案 │    │ 价格监控 │    │ 穿搭建议 │
│ 目的地推荐│    │ 路线优化  │    │ 费用预估 │    │ 灵活日期 │    │ 证件检查 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                                  │
                                                                  ▼
┌─────────┐    ┌─────────┐                                ┌─────────┐
│ 📊 回顾  │ ← │ 🧳 旅途  │ ←─────────────────────────── │ 👫 搭子  │
│         │    │         │                                │         │
│ 花费统计 │    │ 实时助手 │                                │ 智能匹配 │
│ 行程回忆 │    │ 旅途记账 │                                │ 信任体系 │
│ 搭子评价 │    │ 突发应对 │                                │ 组队出发 │
└─────────┘    └─────────┘                                └─────────┘
```

### 7.2 AI 对话交互示例

```
用户: 五一想出去玩，不想人太多，预算两个人5000左右

AI: 了解！五一假期避开人潮是个好策略。我帮你分析一下：

    🔍 基于你的需求（避开人群 + 5000预算/2人），我推荐：

    1. 🏖️ 福建·平潭岛 — 小众海岛，五一水温适宜
       预估费用：¥4200/2人 | 推荐指数：⭐⭐⭐⭐⭐
    2. 🏔️ 贵州·荔波 — 地球绿宝石，游客密度低
       预估费用：¥4600/2人 | 推荐指数：⭐⭐⭐⭐
    3. 🌿 浙江·丽水 — 山水秘境，高铁直达
       预估费用：¥3800/2人 | 推荐指数：⭐⭐⭐⭐

    想了解哪个地方的详细行程？或者告诉我更多偏好，我继续筛选。

用户: 平潭岛不错，帮我做个3天攻略

AI: [调用 weather_forecast, web_search, route_planning, search_hotels, search_flights]

    📋 平潭岛3天2晚攻略（5.1-5.3）

    💰 预算分配（总计 ¥4200 / 2人）
    ├── 交通：¥1600（往返高铁/动车）
    ├── 住宿：¥1200（海景民宿 ¥600/晚 × 2晚）
    ├── 餐饮：¥800（海鲜大排档 + 当地小吃）
    ├── 门票/活动：¥300
    └── 备用金：¥300

    📅 Day 1 (5.1 周四)
    09:00 抵达平潭，取车/打车至民宿
    10:30 龙凤头海滨浴场（免费）
    12:00 午餐：阿里山海鲜排档（人均 ¥60）
    14:00 海坛古城（免费）
    17:00 坛南湾看日落
    19:00 晚餐：平潭特色时来运转 + 咸米时

    📅 Day 2 (5.2 周五) ...
    📅 Day 3 (5.3 周六) ...

    🌤️ 天气预报：5.1-5.3 平潭 22-26°C，多云为主
    👗 穿搭建议：轻薄长袖 + 短裤，带一件防风外套，沙滩拖鞋
    📦 需带装备：防晒霜SPF50+、墨镜、泳衣、充电宝

    需要我查一下具体的高铁票价和时刻表吗？
```

---

## 八、数据模型（核心实体）

```
┌──────────────────┐      ┌──────────────────┐
│      User        │      │   Destination    │
├──────────────────┤      ├──────────────────┤
│ id               │      │ id               │
│ nickname         │      │ name             │
│ avatar           │      │ country          │
│ phone            │      │ province/state   │
│ preferences      │◄────►│ tags             │
│ travel_history   │      │ best_seasons     │
│ verified         │      │ avg_cost_per_day │
│ credit_score     │      │ visa_required    │
└──────┬───────────┘      │ safety_level     │
       │                  │ knowledge_card   │
       │                  └──────────────────┘
       │
       │ 1:N
       ▼
┌──────────────────┐      ┌──────────────────┐
│    Trip          │      │   Itinerary      │
├──────────────────┤ 1:1  ├──────────────────┤
│ id               │─────►│ id               │
│ user_id          │      │ trip_id          │
│ destination_id   │      │ days[]           │
│ start_date       │      │   └── activities │
│ end_date         │      │   └── transport  │
│ status           │      │   └── meals      │
│ people_count     │      │ generated_by_ai  │
│ budget           │      │ last_modified    │
└──────┬───────────┘      └──────────────────┘
       │
       │ 1:1
       ▼
┌──────────────────┐      ┌──────────────────┐
│    Budget        │      │  PackingList     │
├──────────────────┤      ├──────────────────┤
│ id               │      │ id               │
│ trip_id          │      │ trip_id          │
│ total            │      │ items[]          │
│ currency         │      │   └── name       │
│ categories{}     │      │   └── category   │
│ expenses[]       │      │   └── checked    │
│   └── amount     │      │   └── quantity   │
│   └── category   │      │ clothing_advice  │
│   └── note       │      │ document_checklist│
│   └── timestamp  │      └──────────────────┘
└──────────────────┘

┌──────────────────┐      ┌──────────────────┐
│  TravelBuddy     │      │  BuddyMatch     │
│  (搭子招募帖)     │      │  (匹配记录)      │
├──────────────────┤      ├──────────────────┤
│ id               │      │ id               │
│ user_id          │ 1:N  │ post_id          │
│ destination      │─────►│ applicant_id     │
│ date_range       │      │ status           │
│ budget_range     │      │ match_score      │
│ people_wanted    │      │ matched_at       │
│ tags[]           │      └──────────────────┘
│ description      │
│ status           │
└──────────────────┘
```

---

## 九、API 设计（RESTful + AI 端点）

### 9.1 核心 API 端点

```
# AI 对话 & 攻略
POST   /api/v1/chat                     # AI 对话（流式返回）
POST   /api/v1/trips/generate           # AI 生成行程
PUT    /api/v1/trips/{id}/itinerary     # 修改行程
GET    /api/v1/trips/{id}               # 获取行程详情

# 目的地
GET    /api/v1/destinations/recommend   # 智能推荐
GET    /api/v1/destinations/{id}        # 目的地详情
GET    /api/v1/destinations/{id}/wiki   # 当地百科

# 预算
POST   /api/v1/budgets                  # 创建预算计划
POST   /api/v1/budgets/{id}/expenses    # 记录花费
GET    /api/v1/budgets/{id}/summary     # 预算摘要

# 票务
POST   /api/v1/tickets/search           # 搜索票务
POST   /api/v1/tickets/price-alert      # 设置价格提醒
GET    /api/v1/tickets/price-calendar   # 价格日历

# 装备清单
POST   /api/v1/packing/generate         # AI 生成清单
PUT    /api/v1/packing/{id}/check       # 勾选物品

# 搭子
GET    /api/v1/buddies                   # 搭子广场
POST   /api/v1/buddies                   # 发布搭子帖
POST   /api/v1/buddies/{id}/apply       # 申请加入
GET    /api/v1/buddies/recommend         # 智能匹配推荐

# 用户
POST   /api/v1/auth/login               # 登录
GET    /api/v1/users/me                  # 当前用户
PUT    /api/v1/users/me/preferences     # 更新偏好
```

### 9.2 AI 对话 API 详细设计

```http
POST /api/v1/chat
Content-Type: application/json

{
  "session_id": "uuid",
  "message": "五一想去海边，预算3000",
  "context": {
    "trip_id": "uuid | null",
    "location": { "lat": 39.9, "lng": 116.4 }
  },
  "stream": true
}

Response (SSE):
event: delta
data: {"type": "text", "content": "了解！我来帮你..."}

event: tool_call
data: {"type": "tool_call", "name": "search_destinations", "args": {...}}

event: tool_result
data: {"type": "tool_result", "name": "search_destinations", "result": {...}}

event: delta
data: {"type": "text", "content": "推荐以下3个目的地..."}

event: done
data: {"type": "done", "usage": {"tokens": 1234}}
```

---

## 十、安全与合规

### 10.1 数据安全

| 措施 | 说明 |
|------|------|
| 数据加密 | 传输层 TLS 1.3，存储层 AES-256 |
| 身份认证 | JWT + Refresh Token，支持 OAuth2.0 (微信登录) |
| 敏感信息 | 手机号、身份证号脱敏存储，仅在必要场景解密 |
| API 安全 | Rate Limiting、请求签名、IP 白名单 |
| AI 安全 | Prompt 注入防护、输出内容审核、有害信息过滤 |

### 10.2 合规要求

- 遵守《个人信息保护法》(PIPL)
- 搭子社交功能需实名认证
- 票务代理需取得相关资质
- AI 生成内容需标注"由 AI 生成，仅供参考"
- 用户数据删除权（Right to Erasure）

---

## 十一、MVP 路线图

### Phase 1: 核心验证（4 周）

- [x] 项目初始化 & 架构搭建
- [ ] AI 对话服务（LLM + 基础 Function Calling）
- [ ] 目的地推荐（基础版，内置数据）
- [ ] 行程生成（AI 生成 + 手动编辑）
- [ ] 预算规划器（基础版）
- [ ] Web 端 MVP

**验证目标**: 用户能否通过对话完成一次完整的行程规划

### Phase 2: 能力增强（6 周）

- [ ] MCP Tool Server 接入（天气、地图、搜索）
- [ ] 票务聚合与比价
- [ ] 当地百科知识库
- [ ] 装备清单生成器
- [ ] 价格监控 & 通知
- [ ] 移动端适配

**验证目标**: 工具链闭环，用户从规划到预订的转化率

### Phase 3: 社交 & 增长（6 周）

- [ ] 搭子招募功能
- [ ] 实名认证 & 信任体系
- [ ] 攻略社区（UGC）
- [ ] 旅途实时助手
- [ ] 微信小程序
- [ ] 分享裂变机制

### Phase 4: 商业化（持续）

- [ ] OTA 佣金模式（票务/酒店导流）
- [ ] 会员订阅（高级 AI 功能）
- [ ] 广告变现（目的地推广）
- [ ] 数据服务（旅行趋势分析）

---

## 十二、关键指标 (KPIs)

| 指标 | MVP 目标 | 解释 |
|------|---------|------|
| 行程生成成功率 | > 90% | AI 生成的行程被用户采纳（未大幅修改） |
| 对话轮次效率 | < 5 轮 | 用户表达需求到拿到行程的平均对话轮次 |
| 用户满意度 | > 4.0/5 | 行程方案的用户评分 |
| 工具调用成功率 | > 95% | Function Call / MCP 工具调用成功比例 |
| 预订转化率 | > 15% | 生成行程后实际完成预订的比例 |
| 搭子匹配成功率 | > 30% | 发帖后成功组队的比例 |
| DAU/MAU | > 20% | 用户粘性 |

---

## 十三、风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|---------|
| LLM 幻觉（编造不存在的景点/错误法规） | 高 | 关键信息强制联网验证 + RAG 知识库兜底 |
| OTA API 变动/限制 | 中 | MCP 抽象层隔离，快速切换数据源 |
| 票务合规风险 | 高 | 初期仅做信息聚合，不直接代售 |
| 搭子安全事故 | 极高 | 实名认证 + 行程共享 + 保险 + 紧急联系人机制 |
| AI 响应延迟 | 中 | 预生成热门路线缓存 + 流式输出 + 降级策略 |
| 数据隐私泄露 | 高 | 最小化数据收集 + 加密 + 定期安全审计 |

---

## 附录 A: 目录结构（建议）

```
wheretogo/
├── docs/                          # 文档
│   └── PRODUCT_DESIGN.md          # 本文档
├── backend/                       # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI 应用入口
│   │   ├── core/                  # 核心配置
│   │   │   ├── config.py          # 环境变量 & 全局配置
│   │   │   ├── database.py        # MySQL 连接 & Session 管理
│   │   │   └── security.py        # JWT / Auth 工具
│   │   ├── models/                # SQLAlchemy ORM 模型 (表结构定义)
│   │   │   ├── user.py
│   │   │   ├── trip.py
│   │   │   ├── destination.py
│   │   │   ├── budget.py
│   │   │   ├── buddy.py
│   │   │   └── ...
│   │   ├── schemas/               # Pydantic 数据校验 (请求/响应 DTO)
│   │   │   ├── user.py
│   │   │   ├── trip.py
│   │   │   ├── chat.py
│   │   │   └── ...
│   │   ├── crud/                  # 数据库 CRUD 操作 (纯数据访问)
│   │   │   ├── base.py            # 通用 CRUD 基类
│   │   │   ├── user.py
│   │   │   ├── trip.py
│   │   │   └── ...
│   │   ├── api/                   # API 路由 (接收请求、调用 service、返回响应)
│   │   │   ├── deps.py            # 路由依赖 (get_db, get_current_user...)
│   │   │   └── v1/
│   │   │       ├── chat_helpers.py # Chat history → LangChain messages
│   │   │       ├── chat.py
│   │   │       ├── trips.py
│   │   │       ├── destinations.py
│   │   │       ├── budgets.py
│   │   │       ├── tickets.py
│   │   │       ├── packing.py
│   │   │       ├── buddies.py
│   │   │       └── users.py
│   │   ├── services/              # 业务逻辑层 (编排 crud + libs + ai)
│   │   │   ├── trip_service.py
│   │   │   ├── budget_service.py
│   │   │   ├── buddy_service.py
│   │   │   └── ...
│   │   ├── libs/                  # 外部服务封装 (第三方 API 客户端)
│   │   │   ├── ota.py             # OTA 平台 (携程/飞猪) 接口
│   │   │   ├── weather.py         # 天气服务 (和风天气等)
│   │   │   ├── maps.py            # 地图服务 (高德/Google)
│   │   │   ├── search.py          # 联网搜索服务
│   │   │   ├── translate.py       # 翻译服务
│   │   │   └── payment.py         # 支付服务
│   │   ├── ai/                    # AI 编排层
│   │   │   ├── agent.py           # LLM Agent (ReAct)
│   │   │   ├── tools/             # Function Calling 定义
│   │   │   │   ├── booking_tool.py
│   │   │   │   ├── weather_tool.py
│   │   │   │   ├── maps_tool.py
│   │   │   │   └── search_tool.py
│   │   │   └── prompts/           # Prompt 模板
│   │   │       ├── planner.py
│   │   │       └── recommender.py
│   │   ├── mcp/                   # MCP Tool Servers
│   │   │   ├── server.py          # MCP Server 启动 & 注册
│   │   │   ├── booking.py         # 票务 MCP
│   │   │   ├── weather.py         # 天气 MCP
│   │   │   ├── maps.py            # 地图 MCP
│   │   │   └── search.py          # 搜索 MCP
│   │   └── utils/                 # 内部工具函数
│   │       └── helpers.py
│   ├── alembic/                   # 数据库迁移
│   │   ├── alembic.ini
│   │   └── versions/
│   ├── scripts/                   # 运维与种子脚本
│   │   └── seed_destinations.py   # 预置目的地数据
│   ├── tests/                     # 测试（含 libs 可选冒烟测试）
│   ├── pyproject.toml             # Poetry 依赖管理
│   ├── poetry.lock
│   ├── Dockerfile
│   └── .env                       # 环境变量 (不入库)
├── frontend/                      # 前端
│   ├── src/
│   │   ├── components/            # 组件
│   │   ├── pages/                 # 页面
│   │   ├── hooks/                 # 自定义 hooks
│   │   ├── services/              # API 调用
│   │   └── stores/                # 状态管理
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml             # 容器编排
└── README.md
```

### 分层职责说明

```
请求流向: Client → API → Service → CRUD → Database
                              ↘ Libs (外部服务)
                              ↘ AI (LLM Agent → Tools/MCP)

┌─────────┐  各层职责清晰分离:
│   API    │  接收 HTTP 请求，参数校验(Schemas)，调用 Service，返回响应
├─────────┤
│ Schemas │  Pydantic 模型：请求体/响应体/内部 DTO 的数据格式 & 校验规则
├─────────┤
│ Service │  业务逻辑编排：组合 CRUD + Libs + AI 完成一个完整业务动作
├─────────┤
│  CRUD   │  纯数据库操作：增删改查，不含业务逻辑，可被多个 Service 复用
├─────────┤
│  Libs   │  外部服务客户端封装：OTA / 天气 / 地图 / 搜索 / 支付等第三方 API
├─────────┤
│ Models  │  SQLAlchemy ORM 模型：数据库表结构定义，与 MySQL 表一一对应
├─────────┤
│   AI    │  LangGraph ReAct Agent + Tools（libs）+ MCP Server（可选暴露）
└─────────┘
```

---

> **说明**: 骨架与核心链路已在仓库中落地；后续按 Phase 路线图扩展 Layer 2/3 记忆、OTA 真接口与小程序等渠道。
