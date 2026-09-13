# qtllmwiki

前后端分离的 LLM 知识库项目脚手架：后端用 FastAPI 暴露 REST + SSE，智能体由
LangGraph 编排（agent ↔ tools 循环）；前端 Vue 3 单页应用直接消费同一套接口。

| 层 | 技术栈 |
| --- | --- |
| 后端 | Python 3.12 · venv · FastAPI · LangChain · LangGraph（REST + SSE 流式） |
| 前端 | Vue 3 · TypeScript · Vite · Pinia · Vue Router · Axios |

状态：脚手架阶段。对话链路（含流式、工具调用、多轮记忆）已完整可用；
`search_knowledge_base` 是**占位实现**，尚未接入真实检索（见「后续扩展点」）。

## 目录结构

```
qtllmwiki/
├─ main.py                  # 一键启动前后端（py main.py）
├─ backend/                 # FastAPI 服务
│  ├─ .venv/                # Python 虚拟环境（已创建，不入库）
│  ├─ app/
│  │  ├─ main.py            # create_app() 入口 + 根路由
│  │  ├─ core/config.py     # pydantic-settings 配置
│  │  ├─ api/deps.py        # 依赖注入（runtime / settings）
│  │  ├─ api/v1/            # 路由：/health、/chat、/chat/stream、/chat/tools
│  │  ├─ agents/graph.py    # LangGraph 图（agent ↔ tools）
│  │  ├─ agents/llm.py      # init_chat_model 构建聊天模型
│  │  ├─ agents/runtime.py  # 惰性构建并缓存编译后的图
│  │  ├─ agents/tools.py    # DEFAULT_TOOLS：时间 + 知识库检索占位
│  │  ├─ agents/messages.py # LangChain 消息 ↔ 业务 schema 转换
│  │  ├─ services/          # ChatService 编排 + SSE 序列化
│  │  └─ schemas/           # 请求/响应模型
│  ├─ tests/                # pytest（含 EchoChatModel 假模型，无需联网）
│  ├─ requirements.txt
│  └─ requirements-dev.txt
└─ frontend/                # Vue 3 + TS 单页应用
   ├─ src/api/              # axios 实例 + fetch 版 SSE 客户端
   ├─ src/stores/chat.ts    # Pinia：消息、thread_id、流式开关、工具日志
   ├─ src/views/            # ChatView / AboutView
   ├─ .env.development      # VITE_API_BASE_URL / VITE_API_PROXY_TARGET
   └─ vite.config.ts        # /api 代理到后端
```

## 环境要求

- Python **3.11+**（推荐 3.12，虚拟环境按 3.12 创建）
- Node.js **20.19+**（`frontend/package.json` 的 `engines` 约束，Vite 7 要求）
- 一个 OpenAI 兼容的模型端点与 API Key（默认预置 DeepSeek）

## 快速开始

### 一键启动（推荐）

首次准备（只做一次）：

```powershell
# 后端虚拟环境 + 依赖
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env      # 编辑 .env，至少填写 LLM_API_KEY

# 前端依赖
cd ..\frontend
npm install
```

以后每次开发，在仓库根目录执行一条命令即可同时拉起前后端：

```powershell
py main.py                   # 后端(8000, 热重载) + 前端(5173)
py main.py --open            # 启动后自动打开浏览器
py main.py --backend-only    # 只启动后端
py main.py --frontend-only   # 只启动前端
py main.py --no-reload       # 关闭后端热重载
py main.py --no-wait         # 不等待后端健康检查
py main.py --lan             # 监听 0.0.0.0，手机/局域网可访问
```

`main.py` 只依赖标准库，用哪个 Python 解释器运行都可以：

- 自动使用 `backend/.venv` 里的解释器启动后端；找不到时回退到当前解释器。
- 会读取 `backend/.env` 的 `HOST` / `PORT`，并直接调用 `node_modules/vite/bin/vite.js`
  启动前端（显式 `--host`，避免 Vite 只监听 `::1` 导致 `127.0.0.1` 连不上）。
- 轮询 `/api/v1/health`，就绪后打印访问地址；未配置 `LLM_API_KEY` 时额外给出提示
  （`--no-wait` 可跳过等待）。
- 任一子进程退出会连带停止另一个；**Ctrl+C 一次性停止全部服务**。

> `--lan` 会覆盖 `HOST` 为 `0.0.0.0`（同时影响后端的 CORS/监听与 Vite 的监听地址），
> 请自行确认局域网环境可信。
>
> 若在受限 shell（例如本项目的 DSH 沙箱）中运行，uvicorn 的 `--reload`
> 需要创建命名管道，会被拒绝；此时加 `--no-reload` 即可，普通终端不受影响。

### 分开启动

#### 1. 后端

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
# 或等价写法（host/port/reload 取自配置）：
.\.venv\Scripts\python.exe -m app.main
```

- 交互式文档：<http://127.0.0.1:8000/docs>（ReDoc 在 `/redoc`）
- 健康检查：<http://127.0.0.1:8000/api/v1/health>

未配置 `LLM_API_KEY` 时服务仍可正常启动：`/api/v1/chat` 与 `/chat/stream` 返回 **503**，
健康检查状态为 `degraded`、`/health/ready` 返回 `{"ready": false}`。
模型是按请求惰性构建的（`AgentRuntime`），因此改完 `backend/.env` 热重载后即刻生效。

#### 2. 前端

```powershell
cd frontend
npm install
npm run dev        # http://127.0.0.1:5173
```

开发环境下 Vite 把 `/api` 代理到 `VITE_API_PROXY_TARGET`（默认 `http://127.0.0.1:8000`），
因此无需处理 CORS（后端的 `CORS_ORIGINS` 主要留给不经代理的直连场景）。

```powershell
npm run build      # vue-tsc 类型检查 + 生产构建到 dist/
npm run type-check # 仅类型检查
npm run preview    # 本地预览 dist/
```

## 接口一览

### 通用

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 服务信息（`app` / `version` / `env` / `docs` / `api_prefix`） |
| GET | `/health` | 根路径存活探针 |
| GET | `/api/v1/health` | 存活探针（含 `llm_configured`、`llm_model`；未配置 Key 时为 `degraded`） |
| GET | `/api/v1/health/ready` | 就绪探针（触发 Agent 图构建） |
| GET | `/api/v1/openapi.json` | OpenAPI 描述（注意在 `api_prefix` 下） |

### 对话

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/chat` | 一轮对话，返回完整回答 + 会话消息 |
| POST | `/api/v1/chat/stream` | SSE 流式对话 |
| GET | `/api/v1/chat/tools` | 列出 Agent 已注册工具 |

请求体（两个对话接口共用）：

```json
{
  "messages": [{ "role": "user", "content": "你好" }],
  "thread_id": "可选，用于多轮记忆隔离，最长 128 字符"
}
```

- `messages` 至少一条，`role` 取 `system | user | assistant | tool`。
- `thread_id` 不传时由服务端生成（uuid hex）并随响应返回；同一 `thread_id`
  的多轮请求共享 `InMemorySaver` 中的历史消息。
- 前端每次「新会话」都会换一个新的 `thread_id`，因此会话之间互不污染。

非流式响应：

```json
{
  "thread_id": "5f1c…",
  "content": "你好，有什么可以帮你？",
  "messages": [{ "role": "user", "content": "你好" }, { "role": "assistant", "content": "…" }],
  "elapsed_ms": 812.35
}
```

### SSE 流式事件

`POST /api/v1/chat/stream` 返回 `text/event-stream`，每帧形如 `event: <name>\ndata: <json>\n\n`：

| 事件 | `data` | 说明 |
| --- | --- | --- |
| `start` | `{ thread_id }` | 流开始，前端据此刷新当前会话 ID |
| `token` | `{ node, text }` | 模型增量文本（`node` 为 `agent` / `tools`） |
| `tool_call` | `{ node, name, args }` | 模型发起工具调用 |
| `tool_result` | `{ node, name, content }` | 工具返回内容 |
| `done` | `{ thread_id }` | 正常结束 |
| `error` | `{ message }` | 上游异常（异常被转成事件，不会直接断开连接） |

示例：

```powershell
$body = '{"messages":[{"role":"user","content":"现在几点？"}]}'
curl.exe -N -X POST http://127.0.0.1:8000/api/v1/chat/stream `
  -H "Content-Type: application/json" -d $body
```

> 浏览器端 `EventSource` 只支持 GET，所以 `frontend/src/api/chat.ts` 用
> `fetch` + `ReadableStream` + `TextDecoder` 手工解析 SSE 帧，并支持 `AbortController` 中断。

### 错误码

| 状态码 | 触发条件 |
| --- | --- |
| 422 | 请求体校验失败（如 `messages` 为空） |
| 503 | 未配置 `LLM_API_KEY`（`/chat*` 直接拦截） |
| 502 | 上游模型调用失败（非流式接口统一包装） |

流式接口的模型异常以 `error` 事件下发，HTTP 状态仍为 200。

## 配置项（backend/.env）

复制 `.env.example` 为 `.env` 后按需修改，字段名即环境变量名（大小写不敏感）。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_NAME` | `qtllmwiki-api` | 服务名，出现在 `/` 与健康检查 |
| `APP_ENV` / `DEBUG` | `dev` / `true` | 运行环境与日志级别（`DEBUG=true` 时第三方库降噪） |
| `API_PREFIX` | `/api/v1` | 接口前缀，同时决定 `openapi.json` 路径 |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | 监听地址（`main.py` 与 `python -m app.main` 都会读取） |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | 逗号分隔的允许来源 |
| `LLM_PROVIDER` | `openai` | OpenAI 兼容协议，可指向 DeepSeek / 自建网关 |
| `LLM_MODEL` | `deepseek-chat` | 模型名 |
| `LLM_API_KEY` | 空 | 为空时回退到环境变量 `OPENAI_API_KEY`；两者皆空则 `/chat*` 返回 503 |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1` | 兼容端点，留空用 SDK 默认 |
| `LLM_TEMPERATURE` | `0.2` | 采样温度 |
| `LLM_TIMEOUT` | `60` | 单次模型请求超时（秒） |
| `LLM_MAX_RETRIES` | `2` | SDK 层重试次数 |
| `AGENT_MAX_ITERATIONS` | `8` | 工具调用循环上限，换算成 `recursion_limit = 2n + 1` |
| `SYSTEM_PROMPT` | 见 `core/config.py` | 系统提示词（默认要求先结论后依据、不编造、中文回答） |

切换到 OpenAI：把 `LLM_MODEL` 改为 `gpt-4o-mini`、`LLM_BASE_URL` 清空或改为
`https://api.openai.com/v1`，再填对应 `LLM_API_KEY` 即可，代码无需改动。

## 前端配置与功能

前端环境变量（`frontend/.env.development` / `.env.production`）：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api/v1` | axios 与 SSE 客户端共用的 API 前缀；跨域部署时填完整地址 |
| `VITE_API_PROXY_TARGET` | `http://127.0.0.1:8000` | **仅开发环境**：Vite `/api` 代理目标 |

页面：

- `/` 对话页：消息气泡、`流式输出` 开关（关闭则走 `/chat` 非流式）、工具调用记录折叠面板、
  `停止`（`AbortController` 中断流）、`新会话`、Enter 发送 / Shift+Enter 换行、自动滚动。
- `/about` 关于页：实时读取 `/health` 与 `/chat/tools`，展示服务版本、状态、模型、
  API Key 是否配置以及已注册工具。

状态集中在 `src/stores/chat.ts`（Pinia setup store）：`messages` / `threadId` /
`sending` / `error` / `useStreaming` / `toolLog`，以及 `send` / `stop` / `reset`。

## 测试与检查

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest          # 10 个用例：单元 + 接口（假模型，不联网）
.\.venv\Scripts\python.exe -m ruff check .    # 代码规范（line-length 100，当前全绿）
.\.venv\Scripts\python.exe -m mypy app        # 类型检查（可选）
```

> `mypy` 目前会在 LangChain / LangGraph 多版本兼容的 `try/except ImportError` 分支上
> 报少量 `unused-ignore` / `arg-type` 诊断（`agents/graph.py`、`agents/llm.py`、
> `services/chat_service.py`），属于兼容层的已知噪音，不影响运行与测试。

测试要点：`tests/conftest.py` 用 `EchoChatModel` 注入假模型并清空工具，因此
不消耗额度也不需要网络；覆盖非流式对话、多轮记忆、SSE 帧、空消息 422、
工具列表、未配置 Key 时的 503 与 `degraded`。

```powershell
cd frontend
npm run type-check
```

## 后续扩展点

- **接入知识库检索**：替换 `backend/app/agents/tools.py` 中 `search_knowledge_base`
  的函数体（当前返回占位文案），可对接向量库或全文检索；工具签名与描述即模型可见的
  契约，改完无需动图。
- **新增工具**：在 `DEFAULT_TOOLS` 中注册即可，`build_agent_graph` 会自动把它绑到模型
  并接入 `ToolNode`；`/api/v1/chat/tools` 与前端「关于」页会同步列出。
- **记忆持久化**：当前使用 LangGraph `InMemorySaver`（进程重启即丢失）。生产环境可换成
  `langgraph-checkpoint-sqlite` / `langgraph-checkpoint-postgres`，只需给
  `build_agent_graph(..., checkpointer=...)` 传入 saver。
- **鉴权与配额**：在 `app/api/deps.py` 增加依赖项即可，路由层已经统一走 `RuntimeDep` /
  `SettingsDep`。
- **部署**：`npm run build` 产物在 `frontend/dist/`，可由 Nginx 静态托管并把 `/api`
  反代到 FastAPI（保持同域则 `VITE_API_BASE_URL=/api/v1` 不变）。

## 设计说明

- **配置单例**：`get_settings()` 用 `lru_cache` 做进程级单例；测试通过
  `create_app(Settings(_env_file=None, ...))` 注入独立配置。
- **惰性图构建**：`AgentRuntime` 在首次访问 `.graph` 时才构建图（加锁双检），
  保证没有 API Key 也能启动并通过健康检查。
- **消息兼容层**：`agents/messages.py` 统一了 `message.text`（属性/方法）与
  `content`（`str` / content blocks）在不同 langchain-core 版本上的差异。
- **工具异常不打断对话**：内置兜底 `ToolNode` 会把工具异常作为 `ToolMessage` 回灌给模型；
  流式接口的上游异常则转成 `error` 事件。

## 许可

内部脚手架，未附带开源许可证。
