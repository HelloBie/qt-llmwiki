import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.file2md import (
    RAW_FULLTEXT_DIR,
    convert_file,
    convert_all,
    get_conversion_status,
)
from app.db.doc_records import (
    init_db,
    get_or_create_record,
    get_record_by_doc_id,
    get_record_by_origin_filename,
    get_record_by_md_filename,
    delete_record_by_origin_filename,
    list_all_records,
    sync_documents_with_disk,
)

router = APIRouter(prefix="/files", tags=["files"])

# 定位 raw/origin 与 raw/fulltext 物理存储路径
BACKEND_APP_DIR = Path(__file__).resolve().parent.parent.parent
DOCUMENT_DIR = BACKEND_APP_DIR / "document" / "llm-wiki"
RAW_ORIGIN_DIR = DOCUMENT_DIR / "raw" / "origin"
RAW_ORIGIN_DIR.mkdir(parents=True, exist_ok=True)
RAW_FULLTEXT_DIR.mkdir(parents=True, exist_ok=True)

# 允许上传的文件扩展名白名单
ALLOWED_EXTENSIONS = {
    ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".md", ".txt", ".pdf", ".csv", ".json"
}


class FileInfo(BaseModel):
    id: str = Field(description="文档全局唯一标识字符串")
    doc_id: int = Field(description="文档全局唯一纯数字编号标识，从 1 开始递增且永久不变")
    name: str = Field(description="原始文件名")
    ext: str
    size: str
    size_bytes: int
    status: str
    updated_at: str
    is_converted: bool = Field(default=False, description="是否已在 raw/fulltext 中生成对应的 Markdown 文件")
    converted_target: Optional[str] = Field(default=None, description="生成的 Markdown 文件名")
    origin_path: str = Field(default="", description="原始素材存储路径")
    md_path: Optional[str] = Field(default=None, description="转换后 Markdown 存储路径")


class File2MdResponse(BaseModel):
    success: bool
    message: str
    total: int = 0
    results: List[Dict[str, Any]] = Field(default_factory=list)


class PreviewResponse(BaseModel):
    name: str
    ext: str
    is_binary: bool
    content: Optional[str] = None
    size: str
    doc_id: Optional[int] = Field(default=None, description="文档全局唯一纯数字编号标识")
    is_converted_preview: bool = Field(default=False, description="是否展示的是从 raw/fulltext 提取的 Markdown 转换预览")


def format_file_size(size_bytes: int) -> str:
    """人类可读的文件大小格式化"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_safe_file_path(filename: str) -> Path:
    """安全解析文件名，防止目录遍历攻击 (Directory Traversal)"""
    safe_name = Path(filename).name
    if not safe_name or safe_name in (".", "..") or "/" in safe_name or "\\" in safe_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="非法的文件名格式"
        )
    return RAW_ORIGIN_DIR / safe_name


@router.get("", response_model=List[FileInfo], summary="获取 raw/origin 下的文件列表")
async def list_files() -> List[FileInfo]:
    """读取并列出 raw/origin 目录下的所有文件及元数据，包含统一唯一标识 doc_id 及双路径记录"""
    if not RAW_ORIGIN_DIR.exists():
        return []

    RAW_FULLTEXT_DIR.mkdir(parents=True, exist_ok=True)
    # 同步磁盘与数据库中的记录与标识
    sync_documents_with_disk(RAW_ORIGIN_DIR, RAW_FULLTEXT_DIR)

    file_items: List[FileInfo] = []

    # 扫描目录下的文件
    for entry in sorted(RAW_ORIGIN_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if entry.is_file() and not entry.name.startswith("."):
            stat = entry.stat()
            ext = entry.suffix.lstrip(".").lower()
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            target_md = RAW_FULLTEXT_DIR / f"{entry.stem}.md"
            is_conv = target_md.is_file()

            rec = get_record_by_origin_filename(entry.name) or {}
            raw_id = rec.get("doc_id", 0)
            doc_id = int(raw_id) if raw_id else 0

            file_items.append(
                FileInfo(
                    id=str(doc_id),
                    doc_id=doc_id,
                    name=entry.name,
                    ext=ext,
                    size=format_file_size(stat.st_size),
                    size_bytes=stat.st_size,
                    status="indexed",
                    updated_at=mtime,
                    is_converted=is_conv,
                    converted_target=target_md.name if is_conv else None,
                    origin_path=rec.get("origin_path", f"raw/origin/{entry.name}"),
                    md_path=rec.get("md_path") if is_conv else None,
                )
            )
    return file_items


@router.post("/upload", response_model=List[FileInfo], summary="上传文件至 raw/origin")
async def upload_files(files: List[UploadFile] = File(...)) -> List[FileInfo]:
    """支持批量将文件保存到 raw/origin/ 目录下，并在数据库中分配纯数字自增唯一标识 doc_id"""
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未提供有效文件")

    uploaded_items: List[FileInfo] = []

    for file in files:
        if not file.filename:
            continue

        safe_filename = Path(file.filename).name
        ext = Path(safe_filename).suffix.lower()

        # 扩展名校验
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件格式: {ext}，仅支持 Office、Markdown、纯文本及 PDF 文档"
            )

        target_path = RAW_ORIGIN_DIR / safe_filename

        try:
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存文件 {safe_filename} 失败: {e}"
            )
        finally:
            file.file.close()

        stat = target_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

        # 登记入库，分配从 1 递增的纯数字标识 doc_id 并关联原始文件与对应 md 文件的路径
        rec = get_or_create_record(
            origin_filename=safe_filename,
            origin_path=f"raw/origin/{safe_filename}",
            md_filename=f"{target_path.stem}.md",
            md_path=f"raw/fulltext/{target_path.stem}.md",
            file_type=ext.lstrip("."),
            file_size=stat.st_size,
            status="pending",
        )
        doc_id = int(rec["doc_id"])

        uploaded_items.append(
            FileInfo(
                id=str(doc_id),
                doc_id=doc_id,
                name=target_path.name,
                ext=ext.lstrip("."),
                size=format_file_size(stat.st_size),
                size_bytes=stat.st_size,
                status="indexed",
                updated_at=mtime,
                is_converted=False,
                converted_target=None,
                origin_path=rec.get("origin_path", f"raw/origin/{safe_filename}"),
                md_path=None,
            )
        )

    return uploaded_items


@router.get("/download/{filename}", summary="下载 raw/origin 下的指定文件")
async def download_file(filename: str):
    """从 raw/origin 下载指定文件"""
    file_path = get_safe_file_path(filename)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {filename}"
        )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@router.delete("/{filename}", summary="删除 raw/origin 下的指定文件及已转换的 Markdown")
async def delete_file(filename: str):
    """从 raw/origin 物理删除指定文件，若在 raw/fulltext 中已存在转换文档亦同步清理"""
    file_path = get_safe_file_path(filename)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {filename}"
        )

    try:
        file_path.unlink()
        # 同步清理 raw/fulltext 中的对应转换文件
        fulltext_target = RAW_FULLTEXT_DIR / f"{file_path.stem}.md"
        if fulltext_target.is_file():
            try:
                fulltext_target.unlink()
            except Exception:
                pass
        # 同步清理数据库记录
        delete_record_by_origin_filename(file_path.name)
        return {"success": True, "message": f"文件 {filename} 已成功删除"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {e}"
        )


@router.get("/records", summary="查询数据库记录表 (原文件名, md文件名, 唯一标识, 双路径)")
async def get_document_records():
    """获取 SQLite 数据库中记录的文档映射全表信息"""
    sync_documents_with_disk(RAW_ORIGIN_DIR, RAW_FULLTEXT_DIR)
    return list_all_records()


@router.post("/file2md", response_model=File2MdResponse, summary="批量将 raw/origin 文件转换为 Markdown 并存入 raw/fulltext")
async def trigger_file2md_all(force: bool = False) -> File2MdResponse:
    """批量扫描 raw/origin/ 原始素材并转换为 Markdown 存入 raw/fulltext/"""
    results = convert_all(RAW_ORIGIN_DIR, RAW_FULLTEXT_DIR, force=force)
    success_num = sum(1 for r in results if r["success"] and not r.get("skipped"))
    skip_num = sum(1 for r in results if r.get("skipped"))
    return File2MdResponse(
        success=True,
        total=len(results),
        message=f"file2md 转换完成：处理了 {len(results)} 个文件，新生成 {success_num} 个，最新跳过 {skip_num} 个",
        results=results,
    )


@router.post("/{filename}/file2md", summary="将指定 raw/origin 单个文件转换为 Markdown")
async def trigger_file2md_single(filename: str, force: bool = True):
    """将指定的 origin 原始文件转换为 Markdown 存入 raw/fulltext/"""
    file_path = get_safe_file_path(filename)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"原始文件不存在: {filename}"
        )

    res = convert_file(file_path, RAW_FULLTEXT_DIR, force=force)
    return res


@router.get("/file2md/status", summary="查询文件转 Markdown 状态统计")
async def get_file2md_status():
    """获取 origin 与 fulltext 对应转换统计"""
    return get_conversion_status(RAW_ORIGIN_DIR, RAW_FULLTEXT_DIR)


@router.get("/fulltext", summary="获取 raw/fulltext 下已转换的所有 Markdown 文件列表")
async def list_fulltext_files():
    """读取并列出 raw/fulltext 目录下的所有已转换文档及对应的 doc_id"""
    RAW_FULLTEXT_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for entry in sorted(RAW_FULLTEXT_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if entry.is_file() and entry.suffix.lower() == ".md":
            stat = entry.stat()
            rec = get_record_by_md_filename(entry.name) or {}
            raw_id = rec.get("doc_id")
            doc_id = int(raw_id) if raw_id is not None else None
            items.append({
                "doc_id": doc_id,
                "name": entry.name,
                "origin_filename": rec.get("origin_filename"),
                "origin_path": rec.get("origin_path"),
                "md_path": rec.get("md_path", f"raw/fulltext/{entry.name}"),
                "size": format_file_size(stat.st_size),
                "size_bytes": stat.st_size,
                "updated_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
    return items


@router.get("/fulltext/{filename}", summary="读取 raw/fulltext 下转换后的 Markdown 文本内容")
async def get_fulltext_content(filename: str):
    """获取已转换好的 Markdown 文件文本内容与对应的唯一标识"""
    safe_name = Path(filename).name
    fulltext_path = RAW_FULLTEXT_DIR / safe_name
    if not fulltext_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Markdown 转换文件不存在: {filename}"
        )
    rec = get_record_by_md_filename(safe_name) or {}
    raw_id = rec.get("doc_id")
    doc_id = int(raw_id) if raw_id is not None else None
    return {
        "doc_id": doc_id,
        "name": safe_name,
        "filename": safe_name,
        "origin_filename": rec.get("origin_filename"),
        "origin_path": rec.get("origin_path"),
        "md_path": rec.get("md_path", f"raw/fulltext/{safe_name}"),
        "content": fulltext_path.read_text(encoding="utf-8", errors="replace"),
        "size": format_file_size(fulltext_path.stat().st_size),
        "updated_at": datetime.fromtimestamp(fulltext_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/preview/{filename}", response_model=PreviewResponse, summary="预览 raw/origin 文件内容")
async def preview_file(filename: str) -> PreviewResponse:
    """获取文本类文件内容或查看已转换的 Markdown 内容"""
    file_path = get_safe_file_path(filename)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {filename}"
        )

    stat = file_path.stat()
    ext = file_path.suffix.lstrip(".").lower()
    size_str = format_file_size(stat.st_size)

    rec = get_record_by_origin_filename(file_path.name) or {}
    raw_doc_id = rec.get("doc_id")
    doc_id: Optional[int] = int(raw_doc_id) if raw_doc_id is not None else None

    text_extensions = {"md", "txt", "csv", "json"}

    # 1. 如果源文件本身就是文本类文件，直接读取
    if ext in text_extensions:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(100 * 1024)
            return PreviewResponse(
                name=file_path.name,
                ext=ext,
                is_binary=False,
                content=content,
                size=size_str,
                doc_id=doc_id,
                is_converted_preview=False,
            )
        except Exception as e:
            return PreviewResponse(
                name=file_path.name,
                ext=ext,
                is_binary=False,
                content=f"读取文件内容失败: {e}",
                size=size_str,
                doc_id=doc_id,
                is_converted_preview=False,
            )

    # 2. 如果源文件是二进制类（如 .docx），检查是否已经在 raw/fulltext 下转换出 Markdown
    target_md = RAW_FULLTEXT_DIR / f"{file_path.stem}.md"
    if target_md.is_file():
        try:
            conv_content = target_md.read_text(encoding="utf-8", errors="replace")
            return PreviewResponse(
                name=file_path.name,
                ext=ext,
                is_binary=False,
                content=conv_content,
                size=format_file_size(target_md.stat().st_size),
                doc_id=doc_id,
                is_converted_preview=True,
            )
        except Exception:
            pass

    # 3. 未转换的二进制文件
    return PreviewResponse(
        name=file_path.name,
        ext=ext,
        is_binary=True,
        content=None,
        size=size_str,
        doc_id=doc_id,
        is_converted_preview=False,
    )
