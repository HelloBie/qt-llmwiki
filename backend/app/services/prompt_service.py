"""Prompt 服务：基于 Jinja2 模板引擎管理并渲染大模型提示词与人设模板。
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import jinja2

# prompts 目录路径
APP_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = APP_DIR / "prompts"


def _create_jinja_env(prompts_dir: Path) -> jinja2.Environment:
    """创建优化的 Jinja2 提示词渲染环境

    - autoescape=False: 避免在提示词中将 & 或引号转义为 HTML 实体
    - trim_blocks=True, lstrip_blocks=True: 保持模板渲染后的整洁缩进与换行
    - keep_trailing_newline=True: 保持末尾换行符
    """
    try:
        prompts_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(prompts_dir)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


class PromptManager:
    """Jinja2 提示词模板管理器"""

    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir or PROMPTS_DIR
        self._env = _create_jinja_env(self.prompts_dir)

    def reload(self) -> None:
        """重新加载模板缓存"""
        self._env = _create_jinja_env(self.prompts_dir)

    def list_templates(self) -> List[str]:
        """列出 prompts 目录下所有可用模板"""
        if not self.prompts_dir.exists():
            return []
        templates = []
        for p in self.prompts_dir.iterdir():
            if p.is_file() and p.suffix.lower() in (".jinja2", ".j2", ".jinja"):
                templates.append(p.name)
        return sorted(templates)

    def _resolve_template_name(self, name: str) -> str:
        """智能解析模板文件名后缀"""
        if (self.prompts_dir / name).is_file():
            return name
        for ext in (".jinja2", ".j2", ".jinja"):
            candidate = f"{name}{ext}"
            if (self.prompts_dir / candidate).is_file():
                return candidate
        return name

    def render(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """根据模板名渲染提示词

        Args:
            template_name: 模板文件名或不带后缀的基础名
            context: 传递给 Jinja2 模板的变量字典

        Returns:
            渲染后的提示词文本
        """
        ctx = context or {}
        real_name = self._resolve_template_name(template_name)
        try:
            template = self._env.get_template(real_name)
            return template.render(**ctx)
        except jinja2.TemplateNotFound as e:
            raise FileNotFoundError(
                f"未在 prompts 目录找到模板 '{template_name}' (尝试查找: {real_name})"
            ) from e

    def get_system_prompt(
        self,
        template_name: str = "system_default",
        fallback: Optional[str] = None,
        **extra_vars: Any,
    ) -> str:
        """获取系统人设提示词，提供默认变量注入与优雅降级

        Args:
            template_name: 模板名称 (默认 'system_default')
            fallback: 当模板不存在时的回退纯文本
            extra_vars: 额外传递的模板变量
        """
        ctx = {
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            **extra_vars,
        }
        try:
            return self.render(template_name, ctx)
        except FileNotFoundError:
            if fallback is not None:
                return fallback
            return (
                "你是一个专业、严谨且热情的 AI 助手。回答问题时请先给出核心结论，再展开具体依据。"
                "不确定或不知道的内容切勿凭空编造，请使用中文回答。"
            )


# 全局单例
prompt_manager = PromptManager()


def render_prompt(template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
    """快捷函数：渲染指定模板"""
    return prompt_manager.render(template_name, context)


def get_default_system_prompt(fallback: Optional[str] = None, **extra_vars: Any) -> str:
    """快捷函数：获取默认系统提示词"""
    return prompt_manager.get_system_prompt("system_default", fallback=fallback, **extra_vars)
