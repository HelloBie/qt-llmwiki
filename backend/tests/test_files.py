import io
from fastapi.testclient import TestClient


def test_list_files(client: TestClient):
    """测试获取 raw/origin 文件列表"""
    res = client.get("/api/v1/files")
    assert res.status_code == 200
    files = res.json()
    assert isinstance(files, list)


def test_upload_preview_download_delete_cycle(client: TestClient):
    """测试完整的文件上传、预览、下载、删除生命周期"""
    test_filename = "pytest_temp_document.md"
    test_content = b"# PyTest Title\n\nThis is a temporary test document."

    # 1. 上传文件
    files = [("files", (test_filename, io.BytesIO(test_content), "text/markdown"))]
    upload_res = client.post("/api/v1/files/upload", files=files)
    assert upload_res.status_code == 200
    uploaded_data = upload_res.json()
    assert len(uploaded_data) >= 1
    assert any(f["name"] == test_filename for f in uploaded_data)

    # 2. 验证列表中存在
    list_res = client.get("/api/v1/files")
    assert list_res.status_code == 200
    assert any(f["name"] == test_filename for f in list_res.json())

    # 3. 预览文本内容
    preview_res = client.get(f"/api/v1/files/preview/{test_filename}")
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["is_binary"] is False
    assert "PyTest Title" in preview_data["content"]

    # 4. 下载文件
    download_res = client.get(f"/api/v1/files/download/{test_filename}")
    assert download_res.status_code == 200
    assert download_res.content == test_content

    # 5. 删除文件
    delete_res = client.delete(f"/api/v1/files/{test_filename}")
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    # 6. 再次删除返回 404
    delete_again = client.delete(f"/api/v1/files/{test_filename}")
    assert delete_again.status_code == 404
