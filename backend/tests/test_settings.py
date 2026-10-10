import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import yaml

from app.core.yaml_config import CONFIG_YAML_PATH, load_yaml_config, save_yaml_config


@pytest.fixture(autouse=True)
def preserve_config_yaml():
    """保存原有的 config.yaml 并在测试结束后恢复，避免测试污染用户文件"""
    orig_content = CONFIG_YAML_PATH.read_text(encoding="utf-8") if CONFIG_YAML_PATH.is_file() else None
    yield
    if orig_content is not None:
        CONFIG_YAML_PATH.write_text(orig_content, encoding="utf-8")


def test_get_settings_config(client: TestClient):
    """测试读取模型配置"""
    res = client.get("/api/v1/settings/config")
    assert res.status_code == 200
    data = res.json()
    assert "base_url" in data
    assert "model" in data
    assert "temperature" in data


def test_save_settings_to_config_yaml(client: TestClient):
    """测试将模型配置保存写入 config.yaml 文件"""
    payload = {
        "base_url": "https://api.test-custom.com/v1",
        "api_key": "sk-test-key-9999",
        "model": "test-gpt-custom-v1",
        "temperature": 0.85,
        "max_tokens": 8192,
        "top_p": 0.9,
        "organization": "org-test-unit",
        "project_id": "proj-test-unit",
    }

    res = client.post("/api/v1/settings/config", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True

    # 验证磁盘上的 config.yaml 文件
    assert CONFIG_YAML_PATH.is_file()
    with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
        saved_yaml = yaml.safe_load(f)

    assert "openai" in saved_yaml
    openai_part = saved_yaml["openai"]
    assert openai_part["base_url"] == "https://api.test-custom.com/v1"
    assert openai_part["api_key"] == "sk-test-key-9999"
    assert openai_part["model"] == "test-gpt-custom-v1"
    assert openai_part["temperature"] == 0.85
    assert openai_part["max_tokens"] == 8192
    assert openai_part["top_p"] == 0.9
    assert openai_part["organization"] == "org-test-unit"
    assert openai_part["project_id"] == "proj-test-unit"


def test_test_connection_endpoint(client: TestClient):
    """测试连通性检测接口结构"""
    payload = {
        "base_url": "https://api.openai.com/v1",
        "api_key": "sk-dummy-key",
        "model": "gpt-4o",
    }
    res = client.post("/api/v1/settings/test-connection", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "success" in data
    assert "latency_ms" in data
    assert "message" in data
    assert "models" in data
    assert isinstance(data["models"], list)


def test_models_fetch_endpoint(client: TestClient):
    """测试拉取模型列表专用接口 /api/v1/settings/models"""
    payload = {
        "base_url": "https://api.openai.com/v1",
        "api_key": "sk-dummy-key",
    }
    res = client.post("/api/v1/settings/models", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "success" in data
    assert "models" in data
    assert isinstance(data["models"], list)


def test_extract_model_ids_helper():
    """测试各种兼容格式的模型ID解析提取器"""
    from app.api.v1.settings import extract_model_ids

    # 1. 官方 OpenAI 格式 {"data": [{"id": "gpt-4o"}, ...]}
    openai_data = {
        "object": "list",
        "data": [
            {"id": "gpt-4o", "object": "model"},
            {"id": "gpt-4o-mini", "object": "model"},
            {"id": "gpt-4o", "object": "model"},  # 重复项应被自动去重
        ],
    }
    assert extract_model_ids(openai_data) == ["gpt-4o", "gpt-4o-mini"]

    # 2. Ollama / vLLM 兼容格式 {"models": [{"name": "llama3:latest"}, {"id": "mistral"}]}
    ollama_data = {
        "models": [
            {"name": "llama3:latest"},
            {"id": "qwen2.5:7b"},
        ]
    }
    assert extract_model_ids(ollama_data) == ["llama3:latest", "qwen2.5:7b"]

    # 3. 数组列表格式 [{"id": "deepseek-chat"}, {"model": "claude-3-5-sonnet"}]
    list_data = [
        {"id": "deepseek-chat"},
        {"model": "claude-3-5-sonnet"},
        "gemini-1.5-pro",
    ]
    assert extract_model_ids(list_data) == ["deepseek-chat", "claude-3-5-sonnet", "gemini-1.5-pro"]


def test_list_design_docs_endpoint(client: TestClient):
    """测试获取系统工程设计文档列表端点"""
    res = client.get("/api/v1/settings/docs")
    assert res.status_code == 200
    docs = res.json()
    assert isinstance(docs, list)
    assert len(docs) == 5

    doc_ids = [d["id"] for d in docs]
    assert "01_hld" in doc_ids
    assert "02_dd" in doc_ids
    assert "03_dbd" in doc_ids
    assert "04_api" in doc_ids
    assert "readme" in doc_ids

    # 验证字段完整性
    for doc in docs:
        assert "filename" in doc
        assert "title" in doc
        assert "badge" in doc
        assert "description" in doc
        assert "size_bytes" in doc
        assert "line_count" in doc
        assert doc["size_bytes"] > 0
        assert doc["line_count"] > 0


def test_get_design_doc_detail_endpoint(client: TestClient):
    """测试获取具体设计文档内容端点及防穿透机制"""
    # 正常获取 01_hld
    res = client.get("/api/v1/settings/docs/01_hld")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "01_hld"
    assert data["badge"] == "HLD"
    assert "概要设计说明书" in data["title"]
    assert "content" in data
    assert len(data["content"]) > 100
    assert "系统总体架构" in data["content"]

    # 正常获取 readme
    res_readme = client.get("/api/v1/settings/docs/readme")
    assert res_readme.status_code == 200
    assert res_readme.json()["badge"] == "INDEX"

    # 测试不存在的文档 ID 返回 404
    res_404 = client.get("/api/v1/settings/docs/non_existent_doc")
    assert res_404.status_code == 404

    # 测试路径穿越攻击阻止返回 404
    res_traversal = client.get("/api/v1/settings/docs/../../etc/passwd")
    assert res_traversal.status_code == 404


def test_multi_role_models_config(client: TestClient):
    """测试五大分工模型的配置获取与分别保存"""
    # 1. 验证获取配置时包含五大模型角色
    res = client.get("/api/v1/settings/config")
    assert res.status_code == 200
    data = res.json()
    assert "chat" in data
    assert "digest" in data
    assert "embedding" in data
    assert "rerank" in data
    assert "expansion" in data
    assert data["chat"]["name"]
    assert data["embedding"]["name"] == "bge-m3"

    # 2. 分别修改配置并保存
    payload = {
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "sk-unit-test-multi",
        "model": "deepseek-chat",
        "temperature": 0.5,
        "max_tokens": 4096,
        "top_p": 1.0,
        "chat": {
            "name": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-unit-test-multi",
            "temperature": 0.6,
        },
        "digest": {
            "name": "qwen-plus",
            "temperature": 0.2,
        },
        "embedding": {
            "name": "bge-m3",
            "base_url": "http://localhost:11434/v1",
            "dimension": 1024,
        },
        "rerank": {
            "name": "bge-reranker-v2-m3",
            "base_url": "http://localhost:11434",
            "top_n": 8,
        },
        "expansion": {
            "name": "qwen2.5:1.5b",
            "base_url": "http://localhost:11434/v1",
            "temperature": 0.3,
        },
    }
    save_res = client.post("/api/v1/settings/config", json=payload)
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True

    # 3. 再次获取验证持久化生效
    verify_res = client.get("/api/v1/settings/config")
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["chat"]["name"] == "deepseek-chat"
    assert v_data["digest"]["name"] == "qwen-plus"
    assert v_data["embedding"]["name"] == "bge-m3"
    assert v_data["rerank"]["top_n"] == 8
    assert v_data["expansion"]["name"] == "qwen2.5:1.5b"


