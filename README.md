# QT-LLMWiki 智能知识库平台

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4%2B-4FC08D.svg)](https://vuejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-23%20Passed-success.svg)](./backend/tests)

现代简约风格的前后端分离 **大模型与智能知识库管理平台**。
后端基于 **FastAPI + LangGraph** 编排智能体（Agent ↔ Tools）与多轮会话状态；前端采用 **Vue 3 + TypeScript + Vite**，以经典三栏式 SPA 界面呈现，集成高精细纯矢量 SVG 图标与深色质感侧边栏。

---

## 核心特性

- 💬 **智能问答 (Smart Chat)**
  - 支持 **SSE 实时流式打字输出** 与标准非流式 REST 响应；
  - 智能体工具调用（Tool Calling）透明可视化展示，支持折叠与状态追踪；
  - 基于 LangGraph 记忆机制的多轮上下文持久隔离（`thread_id`）。
- 📁 **知识库文件管理、file2md 转换与统一标识库 (File Management & SQLite Metadata)**
  - 管理原始素材池（`raw/origin/`）中的各类文件；
  - 真实支持常见 Office 文档（`.docx` / `.pptx` / `.xlsx`）、`.md`、`.txt`、`.csv`、`.json`、`.pdf` 等文件的上传、下载、删除；
  - **纯数字自增唯一标识（`doc_id`）**：从 1 开始递增的纯数字编号（1, 2, 3...），原文件与其转换生成的 Markdown 全文严格共用同一个唯一标识；分配拥有标识后永久不允许改变；
  - **SQLite 单表文档映射（`document_records`）**：在数据库同一张表中完整持久化记录原文件名、MD 文件名、纯数字标识（`doc_id`）、原始文件路径（`origin_path`）、MD 全文路径（`md_path`）、文件大小、状态与更新时间；
  - **`file2md` 全文结构化转换**：读取 `raw/origin` 下的原始文件，转换为带有标准 **YAML Frontmatter**（包含 `doc_id` / `file_number` 纯数字编号、文件名、源路径、目标路径、类型、大小、字数、时间戳与 `converter: file2md`）及引用头信息的 Markdown 文档；**文档标识作为『文件编号』直接写入 Markdown 正文起始处**，规范化存入 `raw/fulltext/`；
  - 前端支持一键单个/全量批量转换，文件表格与弹窗展示唯一标识，支持在线查看文档映射全表（SQLite）；
  - 支持后端 CLI 独立调用：`python -m app.services.file2md [--file <file>] [--force] [--status]`。
- ⚙️ **模型设置与持久化 (Model Settings & Config)**
  - 完全兼容 **OpenAI 标准协议**，支持官方端点、DeepSeek、Ollama、OneAPI 等兼容网关；
  - 配置持久化写入磁盘 [`config.yaml`](./config.yaml)，智能体图缓存热重载即刻生效；
  - **模型名称双元素设计**：
    - **下拉选择框**：彻底摒弃静态死数据，仅通过网络实时拉取目标端点已开放的模型列表；未读取到时自动禁用交互；
    - **手动输入框**：支持自由键入私有微调或本地模型名，二者双向联动；
  - 支持一键测试网络连通性并测算往返毫秒数。
- 📚 **Wiki 知识库体系 (Wiki Knowledge Base)**
  - 严格规范的知识分层结构：`raw/` 原始不可变素材 + `wiki/` AI 核心沉淀页；
  - 物理路径位于 `app/document/llm-wiki/`。
- 🐳 **开箱即用容器化 (Docker Ready)**
  - 提供 `docker-compose.yml`，宿主机文档目录与 `config.yaml` 均双向实时挂载映射到容器内；
  - 容器内修改与宿主机保持 100% 实时同步。

---

## 知识库目录结构规范

```
app/document/llm-wiki/
├── raw/                     # 原始素材池（用户输入源）
│   ├── origin/              # 原始文件：PDF、Word (.docx)、网页、TXT、Markdown
│   └── fulltext/            # 全文提取缓存区
└── wiki/                    # 核心知识沉淀区（AI 自动组织维护的 Markdown 文档）
    ├── entities/            # 实体页（人物、工具、组件、概念实体）
    ├── sources/             # 素材摘要页（与 raw 原始文件双向关联）
    ├── concepts/            # 主题与核心领域知识汇总页
    ├── comparisons/         # 方案选型与技术横向对比页
    └── index.md             # 全站核心知识索引目录
```

> **提示**：根目录下建立了软链接 `app -> backend/app`、`document -> backend/app/document` 和 `config.yaml -> backend/config.yaml`，无论在宿主机任何路径访问均保持一致。

---

## 项目架构与技术栈

```
qt-llmwiki/
├── main.py                  # 本地一键启动前后端脚手架 (支持热重载、等待就绪)
├── config.yaml              # 全局大模型持久化配置 (软链接至 backend/config.yaml)
├── docker-compose.yml       # Docker 容器化编排 (前端 Nginx + 后端 FastAPI)
├── app/                     # 顶层 app 软链接 (指向 backend/app)
├── document/                # 顶层 document 软链接 (指向 backend/app/document)
│
├── backend/                 # 后端 FastAPI 根目录
│   ├── Dockerfile           # 后端 Python 3.12 生产镜像构建
│   ├── config.yaml          # 持久化配置文件
│   ├── requirements.txt     # 核心运行时依赖 (FastAPI, LangGraph, PyYAML 等)
│   ├── app/
│   │   ├── main.py          # FastAPI 工厂与生命周期初始化
│   │   ├── core/            # 配置单例 (config.py) 与 YAML 引擎 (yaml_config.py)
│   │   ├── db/              # SQLite 文档记录表管理 (doc_records.py: document_records 单表映射)
│   │   ├── api/v1/          # 业务路由: chat, files, settings, health
│   │   ├── agents/          # LangGraph 图编排、运行时缓存、提示词与工具定义
│   │   ├── services/        # 业务编排 (file2md.py 全文转换, sse.py 流式响应)
│   │   └── document/        # Wiki 知识库实体目录 (llm-wiki 挂载持久化)
│   └── tests/               # 完整自动化测试套件 (23 个测试全部通过)
│
└── frontend/                # 前端 Vue 3 根目录
    ├── Dockerfile           # 前端多阶段构建 + Nginx 静态托管
    ├── nginx.conf           # 反向代理配置 (处理 SPA 路由与 SSE 流式长连接)
    ├── package.json
    └── src/
        ├── App.vue          # 现代极简风格三栏 SPA 布局与侧边栏
        ├── api/             # 封装 Axios 客户端与 fetch SSE 客户端 (chat, files, settings)
        ├── views/
        │   ├── ChatView.vue         # 智能问答视图 (打字机效果、工具记录展开)
        │   ├── FileManagerView.vue  # 文件管理视图 (列表、上传、下载、删除、文本预览)
        │   └── SettingsView.vue     # 模型设置视图 (OpenAI 协议、在线拉取模型列表)
        └── assets/style.css         # 全局现代简约无 Emoji 设计系统变量
```

| 层级 | 技术栈与工具 |
| :--- | :--- |
| **后端 (Backend)** | Python 3.12 · FastAPI · LangChain · LangGraph · Pydantic · HTTPX · PyYAML · Uvicorn |
| **前端 (Frontend)** | Vue 3 · TypeScript · Vite · Pinia · Vue Router · Axios · 生产级纯矢量 SVG 图标 |
| **部署与运维** | Docker · Docker Compose · Nginx (反向代理 + SSE 缓冲禁用) |

---

## 快速开始

### 方式一：Docker Compose 一键启动（生产与容器体验）

只需确保本地安装了 Docker 与 Docker Compose：

```bash
# 1. 启动容器编排（自动构建并以后台守护运行）
docker compose up -d --build

# 2. 查看容器运行状态
docker compose ps
```

- **前端应用界面**：浏览器打开 [http://localhost](http://localhost)（或 [http://localhost:5173](http://localhost:5173)）
- **后端交互式文档**：访问 [http://localhost:8000/docs](http://localhost:8000/docs)
- **配置持久化**：修改宿主机根目录或容器内的 `config.yaml`，双向实时同步生效应。

---

### 方式二：本地开发一键启动（推荐用于日常开发）

#### 1. 准备后端环境
```bash
cd backend
python3 -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows:
# .\.venv\Scripts\activate

pip install -r requirements-dev.txt
cp .env.example .env
cd ..
```

#### 2. 准备前端环境
```bash
cd frontend
npm install
cd ..
```

#### 3. 运行根目录 `main.py`
根目录下的 `main.py` 会自动探测解释器并并行启动前后端开发服务：

```bash
python3 main.py
```
- 后端自动挂载热重载：`http://127.0.0.1:8000`
- 前端 Vite 开发服务器：`http://127.0.0.1:5173`
- 支持快捷参数：
  - `python3 main.py --open`：启动成功后自动唤起浏览器
  - `python3 main.py --backend-only`：仅启动后端
  - `python3 main.py --frontend-only`：仅启动前端

---

## API 接口概览

### 1. 模型设置与配置 (`/api/v1/settings`)
| 方法 | 路径 | 功能说明 |
| :--- | :--- | :--- |
| **GET** | `/api/v1/settings/config` | 读取当前 `config.yaml` 中的 OpenAI 配置 |
| **POST** | `/api/v1/settings/config` | 保存配置写入 `config.yaml` 并即时热重载 Agent |
| **POST** | `/api/v1/settings/models` | 实时向指定端点抓取可用模型 ID 列表 |
| **POST** | `/api/v1/settings/test-connection` | 测试 API 基础端点网络连通性并测算延迟 |

### 2. 文件管理 (`/api/v1/files`)
| 方法 | 路径 | 功能说明 |
| :--- | :--- | :--- |
| **GET** | `/api/v1/files` | 获取 `raw/origin/` 目录下的所有文件元信息列表 |
| **POST** | `/api/v1/files/upload` | 上传原始资料文件（支持常见文档、表格、Markdown） |
| **DELETE** | `/api/v1/files/{filename}` | 安全删除指定文件 |
| **GET** | `/api/v1/files/{filename}/preview` | 预览文件文本内容（最大读取 50KB） |
| **GET** | `/api/v1/files/{filename}/download` | 流式下载原始文件 |

### 3. 智能问答与健康检测 (`/api/v1/chat` & `/api/v1/health`)
| 方法 | 路径 | 功能说明 |
| :--- | :--- | :--- |
| **POST** | `/api/v1/chat/stream` | SSE 流式对话端点（返回 `token`、`tool_call`、`done`） |
| **POST** | `/api/v1/chat` | 非流式一轮对话端点 |
| **GET** | `/api/v1/health` | 服务健康与 LLM 就绪状态检查 |

---

## 自动化测试

后端具备完备的单元测试与接口集成测试，包含 Mock 测试环境与配置安全恢复机制：

```bash
cd backend
./.venv/bin/pytest tests/
```

- **测试范围**：存活与就绪探针、SSE 事件帧、文件上传下载安全路径校验、`config.yaml` 读写持久化、多种响应格式模型提取器等；
- **测试结果**：**18 个测试用例全部 100% 通过**。
