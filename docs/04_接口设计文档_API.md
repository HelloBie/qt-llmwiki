# qt-llmwiki 接口设计文档（API Doc）

**文档版本**：v1.0.0  
**编写日期**：2026-10-10  
**文档状态**：正式发布（持续维护）  
**规范标准**：RESTful + Server-Sent Events (SSE) / OpenAPI 3.1  

---

## 1. 接口通用规范

### 1.1 服务基准地址
- **本地开发环境**：`http://127.0.0.1:8000/api/v1`
- **容器化/生产环境**：`http://localhost/api/v1`（通过 Nginx 80 端口统一反向代理）
- **交互式文档地址**：
  - Swagger UI：`http://127.0.0.1:8000/docs`
  - ReDoc：`http://127.0.0.1:8000/redoc`

### 1.2 通用响应码约定
| HTTP 状态码 | 业务语义 | 说明 |
| :---: | :--- | :--- |
| `200 OK` | 请求成功 | 标准操作成功返回 |
| `400 Bad Request` | 请求参数非法 | 必填参数缺失或尝试路径遍历攻击越界 |
| `404 Not Found` | 资源不存在 | 请求的文件、目录或路由不存在 |
| `502 Bad Gateway` | 上游模型网关错误 | 调用第三方大模型端点超时、网络中断或返回格式异常 |
| `503 Service Unavailable` | 服务凭据未就绪 | 大模型 API Key 尚未在设置或 `config.yaml` 中配置 |

### 1.3 统一错误响应 Schema
```json
{
  "detail": "错误原因详细说明字符串"
}
```

---

## 2. 智能问答接口 (Chat API)

### 2.1 SSE 流式对话长连接
- **路径**：`POST /api/v1/chat/stream`
- **说明**：建立 Server-Sent Events (SSE) 长连接，支持打字机 Token 实时推送与工具调用可视化。
- **请求头**：`Content-Type: application/json`
- **响应头**：
  - `Content-Type: text/event-stream`
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`
  - `X-Accel-Buffering: no`
- **请求体 (ChatRequest)**：
  ```json
  {
    "messages": [
      {
        "role": "user",
        "content": "航天器总体设计师的核心岗位职责是什么？"
      }
    ],
    "thread_id": "optional-thread-session-id"
  }
  ```
- **SSE 事件帧格式规范**：
  - **`event: start`**：会话建立
    ```text
    event: start
    data: {"thread_id": "c1f7b7677..."}
    ```
  - **`event: token`**：文本增量生成
    ```text
    event: token
    data: {"node": "agent", "text": "航天器"}
    ```
  - **`event: tool_call`**：Agent 发起工具调用
    ```text
    event: tool_call
    data: {"node": "agent", "name": "search_knowledge_base", "args": {"query": "航天器总体设计师"}}
    ```
  - **`event: tool_result`**：工具执行完成并返回结果
    ```text
    event: tool_result
    data: {"node": "agent", "name": "search_knowledge_base", "content": "【知识库事实内容...】"}
    ```
  - **`event: done`**：本次回答完成
    ```text
    event: done
    data: {"thread_id": "c1f7b7677..."}
    ```
  - **`event: error`**：异常中断
    ```text
    event: error
    data: {"message": "未配置 LLM API Key"}
    ```

### 2.2 同步非流式对话
- **路径**：`POST /api/v1/chat`
- **请求体**：同 `ChatRequest`
- **成功响应 (ChatResponse)**：
  ```json
  {
    "thread_id": "c1f7b7677...",
    "content": "航天器总体设计师负责总体技术方案设计...",
    "messages": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ],
    "elapsed_ms": 1284.5
  }
  ```

### 2.3 获取智能体已注册工具列表
- **路径**：`GET /api/v1/chat/tools`
- **成功响应**：
  ```json
  [
    {
      "name": "get_current_time",
      "description": "获取系统当前准确的日期和时间。",
      "parameters": {"type": "object", "properties": {}}
    },
    {
      "name": "search_knowledge_base",
      "description": "在知识库中检索与问题相关的事实、文档片段和参考资料。",
      "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "检索关键词"}},
        "required": ["query"]
      }
    }
  ]
  ```

---

## 3. 知识库与文件管理接口 (Files API)

### 3.1 树状浏览 llm-wiki 目录条目
- **路径**：`GET /api/v1/files`
- **查询参数**：
  - `path` (string, 可选): 知识库内相对路径，默认空字符串浏览根目录。示例：`"raw/origin"`、`"wiki/entities"`
- **成功响应 (BrowseResponse)**：
  ```json
  {
    "root": "llm-wiki",
    "path": "raw/origin",
    "parent": "raw",
    "entries": [
      {
        "kind": "file",
        "name": "航天器总体设计师岗位说明.docx",
        "rel_path": "raw/origin/航天器总体设计师岗位说明.docx",
        "id": "1",
        "doc_id": 1,
        "ext": "docx",
        "size": "12.4 KB",
        "size_bytes": 12728,
        "status": "indexed",
        "updated_at": "2026-09-24 16:12",
        "is_converted": true,
        "converted_target": "航天器总体设计师岗位说明.md",
        "origin_path": "raw/origin/航天器总体设计师岗位说明.docx",
        "md_path": "raw/fulltext/航天器总体设计师岗位说明.md",
        "in_origin": true
      }
    ]
  }
  ```

### 3.2 批量上传原始素材
- **路径**：`POST /api/v1/files/upload`
- **请求类型**：`multipart/form-data`
- **入参**：`files`: 文件列表（支持多选）
- **成功响应**：返回新登记分配了纯数字自增 `doc_id` 的 `List[FileInfo]`。

### 3.3 相对路径预览文件内容
- **路径**：`GET /api/v1/files/preview`
- **查询参数**：`path` (string, 必需): 相对文件路径，如 `wiki/index.md` 或 `raw/origin/xxx.docx`
- **成功响应 (PreviewResponse)**：
  ```json
  {
    "name": "航天器总体设计师岗位说明.docx",
    "ext": "docx",
    "is_binary": false,
    "content": "---\ndoc_id: 1\n...\n**文件编号**：1\n\n航天器总体设计师...",
    "size": "12.4 KB",
    "doc_id": 1,
    "is_converted_preview": true,
    "rel_path": "raw/origin/航天器总体设计师岗位说明.docx",
    "in_origin": true
  }
  ```

### 3.4 触发 file2md 转换
- **批量转换**：`POST /api/v1/files/file2md?force={true/false}`
- **单文件转换**：`POST /api/v1/files/{filename}/file2md?force={true/false}`
- **成功响应**：
  ```json
  {
    "success": true,
    "doc_id": 1,
    "source_file": "航天器总体设计师岗位说明.docx",
    "target_file": "航天器总体设计师岗位说明.md",
    "target_path": "/app/document/llm-wiki/raw/fulltext/航天器总体设计师岗位说明.md",
    "char_count": 837,
    "file_size": "2.9 KB",
    "message": "成功将 航天器总体设计师岗位说明.docx 转换为 Markdown (唯一标识: 1)"
  }
  ```

### 3.5 查询 SQLite 数据库文档映射全表
- **路径**：`GET /api/v1/files/records`
- **说明**：返回 `document_records` 表中所有映射数据（支持前端数据表弹窗查看）。
- **成功响应**：
  ```json
  [
    {
      "doc_id": 1,
      "origin_filename": "航天器总体设计师岗位说明.docx",
      "md_filename": "航天器总体设计师岗位说明.md",
      "origin_path": "raw/origin/航天器总体设计师岗位说明.docx",
      "md_path": "raw/fulltext/航天器总体设计师岗位说明.md",
      "file_type": "docx",
      "file_size": 12728,
      "status": "converted",
      "created_at": "2026-09-24 16:12:01",
      "updated_at": "2026-09-24 16:17:12"
    }
  ]
  ```

### 3.6 相对路径文件删除
- **路径**：`DELETE /api/v1/files/entry?path={rel_path}`
- **说明**：物理删除文件。若删除的是 `raw/origin/` 下的原件，同步清理 `raw/fulltext/` 下的对应 Markdown 与数据库映射记录。

---

## 4. 系统设置与大模型端点接口 (Settings API)

### 4.1 获取当前模型配置
- **路径**：`GET /api/v1/settings/config`
- **成功响应 (OpenAIModelConfig)**：
  ```json
  {
    "base_url": "https://api.deepseek.com/v1",
    "api_key": "sk-***",
    "model": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 1.0,
    "organization": "",
    "project_id": ""
  }
  ```

### 4.2 保存模型配置并持久化生效
- **路径**：`POST /api/v1/settings/config`
- **请求体**：同 `OpenAIModelConfig`
- **成功响应**：
  ```json
  {
    "success": true,
    "message": "配置已成功保存并写入 config.yaml，当前会话已生效"
  }
  ```

### 4.3 测试端点连通性与动态模型拉取
- **路径**：`POST /api/v1/settings/test-connection`
- **请求体**：
  ```json
  {
    "base_url": "https://api.deepseek.com/v1",
    "api_key": "sk-***"
  }
  ```
- **成功响应**：
  ```json
  {
    "success": true,
    "message": "连通成功！端点正常，获取到 2 个可用模型",
    "latency_ms": 165.2,
    "status_code": 200,
    "available_models_count": 2,
    "models": ["deepseek-chat", "deepseek-reasoner"]
  }
  ```
