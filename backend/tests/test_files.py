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


def test_file2md_status_endpoint(client: TestClient):
    """测试获取 file2md 转换状态统计接口"""
    res = client.get("/api/v1/files/file2md/status")
    assert res.status_code == 200
    data = res.json()
    assert "total_files" in data
    assert "converted_files" in data
    assert "pending_files" in data
    assert "files" in data
    assert isinstance(data["files"], list)


def test_file2md_single_conversion_and_fulltext_access(client: TestClient):
    """测试单个文件转换为 Markdown，并验证 fulltext 列表、内容读取与元数据头"""
    test_filename = "pytest_convert_sample.txt"
    test_content = b"Line 1: System requirements\nLine 2: Design architecture\nLine 3: Implementation"

    # 1. 上传文件到 raw/origin
    files = [("files", (test_filename, io.BytesIO(test_content), "text/plain"))]
    upload_res = client.post("/api/v1/files/upload", files=files)
    assert upload_res.status_code == 200

    try:
        # 2. 调用转换接口
        conv_res = client.post(f"/api/v1/files/{test_filename}/file2md", params={"force": True})
        assert conv_res.status_code == 200
        conv_data = conv_res.json()
        assert conv_data["success"] is True
        target_name = conv_data["target_file"]
        assert target_name == "pytest_convert_sample.md"

        # 3. 验证 fulltext 列表
        ft_res = client.get("/api/v1/files/fulltext")
        assert ft_res.status_code == 200
        ft_list = ft_res.json()
        assert any(item["name"] == target_name for item in ft_list)

        # 4. 获取 fulltext 转换后的 markdown 内容
        ft_content_res = client.get(f"/api/v1/files/fulltext/{target_name}")
        assert ft_content_res.status_code == 200
        ft_doc = ft_content_res.json()
        assert ft_doc["name"] == target_name
        md_text = ft_doc["content"]

        # 验证头部元数据
        assert "---" in md_text
        assert 'title: "pytest_convert_sample"' in md_text
        assert 'source_file: "pytest_convert_sample.txt"' in md_text
        assert 'converter: "file2md"' in md_text
        assert "Line 1: System requirements" in md_text

        # 5. 检查文件列表中的 is_converted 状态标记
        list_res = client.get("/api/v1/files")
        assert list_res.status_code == 200
        for f in list_res.json():
            if f["name"] == test_filename:
                assert f["is_converted"] is True
                assert f["converted_target"] == target_name

    finally:
        # 6. 删除文件，同时应联动清理 fulltext 下的 md
        del_res = client.delete(f"/api/v1/files/{test_filename}")
        assert del_res.status_code == 200

        # 验证 fulltext 内容已随着删除被清理
        ft_deleted = client.get(f"/api/v1/files/fulltext/pytest_convert_sample.md")
        assert ft_deleted.status_code == 404


def test_file2md_batch_convert(client: TestClient):
    """测试批量转换接口"""
    file_a = "batch_test_a.txt"
    file_b = "batch_test_b.csv"
    content_a = b"Sample text content A"
    content_b = b"name,role,department\nAlice,Lead Engineer,Avionics\nBob,Architect,Payload"

    client.post("/api/v1/files/upload", files=[("files", (file_a, io.BytesIO(content_a), "text/plain"))])
    client.post("/api/v1/files/upload", files=[("files", (file_b, io.BytesIO(content_b), "text/csv"))])

    try:
        batch_res = client.post("/api/v1/files/file2md", params={"force": True})
        assert batch_res.status_code == 200
        res_data = batch_res.json()
        assert res_data["total"] >= 2
        results = res_data["results"]
        assert any(r["source_file"] == file_a and r["success"] for r in results)
        assert any(r["source_file"] == file_b and r["success"] for r in results)

        # 检查 CSV 转换成 Markdown 包含表格语法 |
        ft_csv = client.get("/api/v1/files/fulltext/batch_test_b.md")
        assert ft_csv.status_code == 200
        csv_md = ft_csv.json()["content"]
        assert "| name | role | department |" in csv_md or "| Alice |" in csv_md

    finally:
        client.delete(f"/api/v1/files/{file_a}")
        client.delete(f"/api/v1/files/{file_b}")


def test_file2md_service_unit(tmp_path):
    """测试 file2md 服务内部转换逻辑与工具函数"""
    from pathlib import Path
    from app.services.file2md import format_file_size, generate_frontmatter

    # 测试文件大小格式化
    assert format_file_size(500) == "500 B"
    assert format_file_size(2048) == "2.0 KB"
    assert format_file_size(5 * 1024 * 1024) == "5.0 MB"

    # 测试生成 Markdown 头部 Frontmatter
    fake_source = tmp_path / "test_doc.docx"
    fake_source.write_text("dummy content")
    fake_target = tmp_path / "test_doc.md"

    header = generate_frontmatter(
        source_file=fake_source,
        target_file=fake_target,
        content="Parsed text content for testing",
        extra_meta={"Author": "Tester"},
    )
    assert header.startswith("---")
    assert 'source_file: "test_doc.docx"' in header
    assert 'target_file: "test_doc.md"' in header
    assert 'file_type: "docx"' in header
    assert 'Author: "Tester"' in header
    assert 'converter: "file2md"' in header
    assert "> **原始素材**" in header


def test_document_records_database_and_shared_id(client: TestClient):
    """测试原文件与转换出的 MD 文档共用纯数字自增唯一标识 doc_id（从 1 开始递增且不可变更），
    并在 SQLite 数据库单表中记录原文件名、md文件名、标识、双路径。
    """
    test_filename = "db_test_sample.txt"
    test_content = b"Content for document records database verification."

    # 1. 上传文件
    files = [("files", (test_filename, io.BytesIO(test_content), "text/plain"))]
    upload_res = client.post("/api/v1/files/upload", files=files)
    assert upload_res.status_code == 200
    uploaded_info = upload_res.json()[0]
    doc_id = uploaded_info["doc_id"]
    assert isinstance(doc_id, int)
    assert doc_id >= 1
    assert uploaded_info["id"] == str(doc_id)
    assert uploaded_info["origin_path"] == f"raw/origin/{test_filename}"

    try:
        # 2. 查询 /files/records 数据库表接口
        records_res = client.get("/api/v1/files/records")
        assert records_res.status_code == 200
        records = records_res.json()
        target_rec = next((r for r in records if r["origin_filename"] == test_filename), None)
        assert target_rec is not None
        assert target_rec["doc_id"] == doc_id
        assert target_rec["origin_filename"] == test_filename
        assert target_rec["md_filename"] == "db_test_sample.md"
        assert target_rec["origin_path"] == f"raw/origin/{test_filename}"
        assert target_rec["md_path"] == "raw/fulltext/db_test_sample.md"

        # 3. 触发单个文件转 Markdown
        conv_res = client.post(f"/api/v1/files/{test_filename}/file2md", params={"force": True})
        assert conv_res.status_code == 200
        conv_data = conv_res.json()
        assert conv_data["success"] is True
        assert conv_data["doc_id"] == doc_id

        # 4. 再次转换（验证标识不可变性：拥有标识后标识绝对不允许改变）
        conv_res2 = client.post(f"/api/v1/files/{test_filename}/file2md", params={"force": True})
        assert conv_res2.status_code == 200
        assert conv_res2.json()["doc_id"] == doc_id

        # 5. 读取转换后的 MD 全文，检查头部元数据中是否写入了相同的唯一数字标识 doc_id
        ft_content_res = client.get("/api/v1/files/fulltext/db_test_sample.md")
        assert ft_content_res.status_code == 200
        ft_doc = ft_content_res.json()
        assert ft_doc["doc_id"] == doc_id
        md_text = ft_doc["content"]

        # 检查 Frontmatter 与引用块中的标识与文件编号
        assert f"doc_id: {doc_id}" in md_text
        assert f"file_number: {doc_id}" in md_text
        assert f"**文件编号**：{doc_id}" in md_text
        # 验证文件编号作为文件编号写入 md 正文
        assert f"**文件编号**：{doc_id}\n\nContent for document records database verification." in md_text

        # 6. 验证数据库中该记录状态已更新为 converted，且 doc_id 严格保持不变
        records_after = client.get("/api/v1/files/records").json()
        rec_after = next(r for r in records_after if r["origin_filename"] == test_filename)
        assert rec_after["status"] == "converted"
        assert rec_after["doc_id"] == doc_id

        # 7. 验证预览接口返回同样的 doc_id
        prev_res = client.get(f"/api/v1/files/preview/{test_filename}")
        assert prev_res.status_code == 200
        assert prev_res.json()["doc_id"] == doc_id

    finally:
        # 8. 删除文件并验证数据库记录被同步清理
        del_res = client.delete(f"/api/v1/files/{test_filename}")
        assert del_res.status_code == 200

        records_final = client.get("/api/v1/files/records").json()
        assert not any(r["origin_filename"] == test_filename for r in records_final)



