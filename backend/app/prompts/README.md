# Prompts 提示词资产管理目录

本目录用于统一存放与版本化管理大语言模型（LLM）的**固定人设（Persona）、系统提示词（System Prompt）以及各类工作流任务提示词**。

统一使用 **Jinja2** 模板语法进行编写，文件后缀推荐为 `.jinja2`（亦兼容 `.j2`）。

---

## 📁 目录规范

```text
prompts/
├── README.md                  # 目录规范与使用说明文档
├── system_default.jinja2      # 全局默认系统人设与问答规范
├── wiki_qa.jinja2             # (示例) 专门针对 RAG 检索问答的提示词
└── extractor.jinja2           # (示例) 实体/关键词提取结构化提示词
```

---

## 💡 为什么选用 Jinja2？

1. **兼备 Markdown 结构与动态插值**：
   正文直接书写美观的 Markdown，同时支持 `{{ assistant_name }}` 变量注入，大模型原生理解效果极佳。
2. **逻辑控制与条件分支**：
   支持 `{% if ... %}`、`{% for item in items %}` 等，方便根据不同场景动态注入安全规则、文件列表或时间上下文。
3. **注释隔离**：
   使用 `{# ... #}` 记录维护者、版本与变量说明，注释在渲染时会被完全剔除，**不会消耗大模型 Token**。

---

## 🛠️ 模板编写规范示例

```jinja2
{# ============================================================================== #}
{# 模板名称: 航天知识库问答助手                                                     #}
{# 维护人: System Architect                                                      #}
{# 支持变量:                                                                     #}
{#   - assistant_name: 助理名称                                                   #}
{#   - current_date: 当前系统时间                                                 #}
{#   - context_docs: 检索到的知识库上下文列表 (可选)                                 #}
{# ============================================================================== #}
# Role
你是一个专业且严谨的 {{ assistant_name | default("知识库专家助手") }}。

## 核心原则
1. **先结论后阐述**：先在第一行给出清晰结论，再展开阐述依据。
2. **严禁捏造**：知识库未提及的内容明确告知不知道。

{% if context_docs %}
## 参考资料
{% for doc in context_docs %}
### [文档 {{ loop.index }}] {{ doc.title }}
{{ doc.content }}
{% endfor %}
{% endif %}

{% if current_date %}
- 当前基准时间: {{ current_date }}
{% endif %}
```

---

## 💻 Python 代码调用方式

在后端代码中（例如 `app.agents` 或 `app.services`）：

```python
from app.services.prompt_service import render_prompt, get_default_system_prompt

# 1. 快捷获取并渲染默认系统提示词（自动注入日期等变量）
system_prompt = get_default_system_prompt(
    assistant_name="航天知识库智能体",
    extra_rules=["重点关注卫星总体参数"]
)

# 2. 渲染指定自定义模板
custom_prompt = render_prompt("system_default", {
    "assistant_name": "问答助手",
    "enable_strict_citations": True
})
```
