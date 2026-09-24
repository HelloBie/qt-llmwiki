import pytest
from fastapi.testclient import TestClient


def test_root_info(client: TestClient):
    """测试根路径服务元信息"""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["app"] == "qtllmwiki-test"
    assert data["docs"] == "/docs"


def test_root_health(client: TestClient):
    """测试根路径存活探针"""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_v1_health_healthy(client: TestClient):
    """测试配置 Key 时健康检查返回 healthy"""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["llm_configured"] is True
    assert data["tools_count"] >= 1


def test_v1_health_degraded(unconfigured_client: TestClient):
    """测试未配置 Key 时健康检查返回 degraded"""
    res = unconfigured_client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "degraded"
    assert data["llm_configured"] is False


def test_ready_probe(client: TestClient):
    """测试就绪探针"""
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    assert res.json()["ready"] is True


def test_tools_list(client: TestClient):
    """测试注册工具列表"""
    res = client.get("/api/v1/chat/tools")
    assert res.status_code == 200
    tools = res.json()
    assert isinstance(tools, list)
    names = [t["name"] for t in tools]
    assert "get_current_time" in names or "search_knowledge_base" in names


def test_chat_sync_success(client: TestClient):
    """测试非流式正常对话响应"""
    payload = {
        "messages": [{"role": "user", "content": "你好世界"}],
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "thread_id" in data
    assert "你好世界" in data["content"]
    assert len(data["messages"]) >= 2
    assert data["elapsed_ms"] >= 0


def test_chat_multi_turn_memory(client: TestClient):
    """测试同一 thread_id 下的多轮记忆共享"""
    thread_id = "test-session-12345"
    # 第一轮
    res1 = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "我的名字是小秋"}], "thread_id": thread_id},
    )
    assert res1.status_code == 200
    assert res1.json()["thread_id"] == thread_id

    # 第二轮
    res2 = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "我叫什么？"}], "thread_id": thread_id},
    )
    assert res2.status_code == 200
    assert res2.json()["thread_id"] == thread_id


def test_chat_empty_messages_validation(client: TestClient):
    """测试空 messages 请求体验证失败返回 422"""
    res = client.post("/api/v1/chat", json={"messages": []})
    assert res.status_code == 422


def test_chat_unconfigured_503(unconfigured_client: TestClient):
    """测试未配置 Key 时直接调用 /chat 返回 503"""
    payload = {"messages": [{"role": "user", "content": "你好"}]}
    res = unconfigured_client.post("/api/v1/chat", json=payload)
    assert res.status_code == 503
    assert "LLM_API_KEY" in res.json()["detail"]


def test_chat_stream_sse(client: TestClient):
    """测试 SSE 流式对话事件帧"""
    payload = {"messages": [{"role": "user", "content": "流式测试"}]}
    with client.stream("POST", "/api/v1/chat/stream", json=payload) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        text = response.read().decode("utf-8")
        assert "event: start" in text
        assert "event: token" in text
        assert "event: done" in text
