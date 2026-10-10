import pytest
from pathlib import Path
from app.services.prompt_service import (
    PromptManager,
    render_prompt,
    get_default_system_prompt,
)


def test_list_templates():
    manager = PromptManager()
    templates = manager.list_templates()
    assert "system_default.jinja2" in templates


def test_render_system_default():
    result = render_prompt("system_default", {
        "assistant_name": "测试助理",
        "current_date": "2026-10-10",
        "extra_rules": ["遵守保密协议", "响应迅速"]
    })

    assert "测试助理" in result
    assert "2026-10-10" in result
    assert "遵守保密协议" in result
    assert "响应迅速" in result
    assert "先结论后阐述" in result


def test_get_default_system_prompt_fallback(tmp_path: Path):
    manager = PromptManager(prompts_dir=tmp_path / "empty_prompts")
    fallback_text = "默认降级人设"
    res = manager.get_system_prompt("not_found", fallback=fallback_text)
    assert res == fallback_text


def test_template_extension_resolution():
    manager = PromptManager()
    # 无论带不带 .jinja2 后缀，都能正确识别
    res1 = manager.render("system_default", {"assistant_name": "助手A"})
    res2 = manager.render("system_default.jinja2", {"assistant_name": "助手A"})
    assert res1 == res2
    assert "助手A" in res1
