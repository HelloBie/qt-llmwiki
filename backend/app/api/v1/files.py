import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/files", tags=["files"])

# 定位 raw/origin 物理存储路径
BACKEND_APP_DIR = Path(__file__).resolve().parent.parent.parent
RAW_ORIGIN_DIR = BACKEND_APP_DIR / "document" / "llm-wiki" / "raw" / "origin"
RAW_ORIGIN_DIR.mkdir(parents=True, exist_ok=True)

# 允许上传的文件扩展名白名单
ALLOWED_EXTENSIONS = {
    ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".md", ".txt", ".pdf", ".csv", ".json"
}


class FileInfo(BaseModel):
    id: str
    name: str
    ext: str
    size: str
    size_bytes: int
    status: str
    updated_at: str


class PreviewResponse(BaseModel):
    name: str
    ext: str
    is_binary: bool
    content: Optional[str] = None
    size: str


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
    """读取并列出 raw/origin 目录下的所有文件及元数据"""
    if not RAW_ORIGIN_DIR.exists():
        return []

    file_items: List[FileInfo] = []
    # 扫描目录下的文件
    for entry in sorted(RAW_ORIGIN_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if entry.is_file():
            stat = entry.stat()
            ext = entry.suffix.lstrip(".").lower()
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            file_items.append(
                FileInfo(
                    id=entry.name,
                    name=entry.name,
                    ext=ext,
                    size=format_file_size(stat.st_size),
                    size_bytes=stat.st_size,
                    status="indexed",  # 接入物理文件后默认就绪状态
                    updated_at=mtime,
                )
            )
    return file_items


@router.post("/upload", response_model=List[FileInfo], summary="上传文件至 raw/origin")
async def upload_files(files: List[UploadFile] = File(...)) -> List[FileInfo]:
    """支持批量将文件保存到 raw/origin/ 目录下"""
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

        uploaded_items.append(
            FileInfo(
                id=target_path.name,
                name=target_path.name,
                ext=ext.lstrip("."),
                size=format_file_size(stat.st_size),
                size_bytes=stat.st_size,
                status="indexed",
                updated_at=mtime,
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


@router.delete("/{filename}", summary="删除 raw/origin 下的指定文件")
async def delete_file(filename: str):
    """从 raw/origin 物理删除指定文件"""
    file_path = get_safe_file_path(filename)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {filename}"
        )

    try:
        file_path.unlink()
        return {"success": True, "message": f"文件 {filename} 已成功删除"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {e}"
        )


@router.get("/preview/{filename}", response_model=PreviewResponse, summary="预览 raw/origin 文件内容")
async def preview_file(filename: str) -> PreviewResponse:
    """获取文本类文件内容或二进制元信息"""
    file_path = get_safe_file_path(filename)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {filename}"
        )

    stat = file_path.stat()
    ext = file_path.suffix.lstrip(".").lower()
    size_str = format_file_size(stat.st_size)

    text_extensions = {"md", "txt", "csv", "json"}

    if ext in text_extensions:
        try:
            # 读取前 100KB 防止大文件溢出
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(100 * 1024)
            return PreviewResponse(
                name=file_path.name,
                ext=ext,
                is_binary=False,
                content=content,
                size=size_str
            )
        except Exception as e:
            return PreviewResponse(
                name=file_path.name,
                ext=ext,
                is_binary=False,
                content=f"读取文件内容失败: {e}",
                size=size_str
            )
    else:
        return PreviewResponse(
            name=file_path.name,
            ext=ext,
            is_binary=True,
            content=None,
            size=size_str
        )
