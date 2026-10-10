import os
import shutil
from pathlib import Path
from typing import List, Literal, Optional, Dict, Any
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
    rel_path: str = Field(default="", description="相对 llm-wiki 根目录的路径")
    in_origin: bool = Field(default=False, description="是否位于 raw/origin，可执行 file2md")
    updated_at: Optional[str] = Field(default=None, description="文件最后修改时间")


class BrowseEntry(BaseModel):
    name: str
    rel_path: str = Field(description="相对 llm-wiki 根目录的路径")
    kind: Literal["dir", "file"]
    ext: str = ""
    size: str = ""
    size_bytes: int = 0
    updated_at: str = ""
    doc_id: Optional[int] = None
    is_converted: bool = False
    converted_target: Optional[str] = None
    origin_path: Optional[str] = None
    md_path: Optional[str] = None
    in_origin: bool = False


class BrowseResponse(BaseModel):
    root: str = "llm-wiki"
    path: str = Field(description="当前目录相对 llm-wiki 根目录的路径，根目录为空字符串")
    parent: Optional[str] = Field(default=None, description="上级目录相对路径；根目录为 null，根下第一级的上级为空字符串")
    entries: List[BrowseEntry] = Field(default_factory=list)


def format_file_size(size_bytes: int) -> str:
    """人类可读的文件大小格式化"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# 不在文件管理里展示的内部文件（SQLite 与隐藏占位）
_HIDDEN_NAMES = {
    "documents.db",
    "documents.db-wal",
    "documents.db-shm",
}
_TEXT_EXTENSIONS = {"md", "txt", "csv", "json", "yaml", "yml"}


def get_safe_file_path(filename: str) -> Path:
    """安全解析文件名，防止目录遍历攻击 (Directory Traversal)"""
    safe_name = Path(filename).name
    if not safe_name or safe_name in (".", "..") or "/" in safe_name or "\\" in safe_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="非法的文件名格式"
        )
    return RAW_ORIGIN_DIR / safe_name


def normalize_rel_path(rel: str) -> str:
    """把用户传入的路径收成 llm-wiki 内的相对路径，拒绝越界"""
    raw = (rel or "").strip().replace("\\", "/")
    if raw.startswith("/") or (len(raw) >= 2 and raw[1] == ":"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="非法路径")
    parts: List[str] = []
    for part in raw.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="非法路径")
        parts.append(part)
    return "/".join(parts)


def resolve_wiki_path(rel: str) -> Path:
    """解析并确认目标位于 llm-wiki 根目录之内"""
    normalized = normalize_rel_path(rel)
    root = DOCUMENT_DIR.resolve()
    target = (root / normalized).resolve() if normalized else root
    try:
        inside = os.path.commonpath([str(root), str(target)]) == str(root)
    except ValueError:
        inside = False
    if not inside:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="非法路径")
    return target


def resolve_wiki_file(rel: str) -> Path:
    """解析 llm-wiki 内的文件路径"""
    target = resolve_wiki_path(rel)
    if not target.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {normalize_rel_path(rel) or rel}",
        )
    return target


def _is_origin_file(path: Path) -> bool:
    return path.is_file() and path.parent.resolve() == RAW_ORIGIN_DIR.resolve()


def _is_fulltext_file(path: Path) -> bool:
    return path.is_file() and path.parent.resolve() == RAW_FULLTEXT_DIR.resolve()


def _rel_to_wiki(path: Path) -> str:
    return path.resolve().relative_to(DOCUMENT_DIR.resolve()).as_posix()


def _should_hide(path: Path) -> bool:
    return path.name.startswith(".") or path.name in _HIDDEN_NAMES


def _lookup_doc(path: Path) -> Dict[str, Any]:
    if _is_origin_file(path):
        return get_record_by_origin_filename(path.name) or {}
    if _is_fulltext_file(path):
        return get_record_by_md_filename(path.name) or {}
    return {}


def _entry_from_path(path: Path) -> BrowseEntry:
    rel = _rel_to_wiki(path)
    stat = path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
    if path.is_dir():
        return BrowseEntry(
            name=path.name,
            rel_path=rel,
            kind="dir",
            updated_at=mtime,
            size="—",
        )

    ext = path.suffix.lstrip(".").lower()
    in_origin = _is_origin_file(path)
    rec = _lookup_doc(path)
    raw_id = rec.get("doc_id")
    doc_id = int(raw_id) if raw_id else None
    target_md = RAW_FULLTEXT_DIR / f"{path.stem}.md"
    is_conv = target_md.is_file() if in_origin else _is_fulltext_file(path) and ext == "md"
    return BrowseEntry(
        name=path.name,
        rel_path=rel,
        kind="file",
        ext=ext,
        size=format_file_size(stat.st_size),
        size_bytes=stat.st_size,
        updated_at=mtime,
        doc_id=doc_id,
        is_converted=is_conv,
        converted_target=target_md.name if in_origin and is_conv else None,
        origin_path=rec.get("origin_path") if rec else (rel if in_origin else None),
        md_path=rec.get("md_path") if is_conv else None,
        in_origin=in_origin,
    )


def build_preview(file_path: Path) -> PreviewResponse:
    """读取 llm-wiki 内任意文件的预览。文本直接展示；origin 里的二进制优先展示已转换 Markdown。"""
    stat = file_path.stat()
    ext = file_path.suffix.lstrip(".").lower()
    size_str = format_file_size(stat.st_size)
    updated_at_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    rel = _rel_to_wiki(file_path)
    in_origin = _is_origin_file(file_path)
    rec = _lookup_doc(file_path)
    raw_doc_id = rec.get("doc_id")
    doc_id: Optional[int] = int(raw_doc_id) if raw_doc_id is not None else None

    if ext in _TEXT_EXTENSIONS:
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
                rel_path=rel,
                in_origin=in_origin,
                updated_at=updated_at_str,
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
                rel_path=rel,
                in_origin=in_origin,
                updated_at=updated_at_str,
            )

    if in_origin:
        target_md = RAW_FULLTEXT_DIR / f"{file_path.stem}.md"
        if target_md.is_file():
            try:
                conv_content = target_md.read_text(encoding="utf-8", errors="replace")
                target_stat = target_md.stat()
                return PreviewResponse(
                    name=file_path.name,
                    ext=ext,
                    is_binary=False,
                    content=conv_content,
                    size=format_file_size(target_stat.st_size),
                    doc_id=doc_id,
                    is_converted_preview=True,
                    rel_path=rel,
                    in_origin=True,
                    updated_at=datetime.fromtimestamp(target_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                )
            except Exception:
                pass

    return PreviewResponse(
        name=file_path.name,
        ext=ext,
        is_binary=True,
        content=None,
        size=size_str,
        doc_id=doc_id,
        is_converted_preview=False,
        rel_path=rel,
        in_origin=in_origin,
        updated_at=updated_at_str,
    )


def delete_origin_file(file_path: Path) -> Dict[str, Any]:
    """删除 raw/origin 中的文件，并清理对应全文与数据库记录"""
    filename = file_path.name
    file_path.unlink()
    fulltext_target = RAW_FULLTEXT_DIR / f"{file_path.stem}.md"
    if fulltext_target.is_file():
        try:
            fulltext_target.unlink()
        except Exception:
            pass
    delete_record_by_origin_filename(filename)
    return {"success": True, "message": f"文件 {filename} 已成功删除"}


@router.get("", response_model=BrowseResponse, summary="浏览 llm-wiki 目录")
async def list_files(path: str = "") -> BrowseResponse:
    """列出 llm-wiki 下指定目录的子文件夹与文件。path 为空时返回根目录。"""
    normalized = normalize_rel_path(path)
    current = resolve_wiki_path(normalized)
    if not current.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"目录不存在: {normalized or 'llm-wiki'}",
        )

    RAW_FULLTEXT_DIR.mkdir(parents=True, exist_ok=True)
    sync_documents_with_disk(RAW_ORIGIN_DIR, RAW_FULLTEXT_DIR)

    entries: List[BrowseEntry] = []
    for entry in current.iterdir():
        if _should_hide(entry):
            continue
        if entry.is_dir() or entry.is_file():
            entries.append(_entry_from_path(entry))

    entries.sort(key=lambda item: (item.kind != "dir", item.name.lower()))
    parent: Optional[str]
    if not normalized:
        parent = None
    else:
        parent = "/".join(normalized.split("/")[:-1])

    return BrowseResponse(root="llm-wiki", path=normalized, parent=parent, entries=entries)


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


def _file_response(file_path: Path) -> FileResponse:
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@router.get("/download", summary="按相对路径下载 llm-wiki 内的文件")
async def download_by_path(path: str):
    """从 llm-wiki 下载指定相对路径的文件"""
    return _file_response(resolve_wiki_file(path))


@router.get("/download/{filename}", summary="下载 raw/origin 下的指定文件")
async def download_file(filename: str):
    """从 raw/origin 下载指定文件"""
    file_path = get_safe_file_path(filename)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {filename}"
        )
    return _file_response(file_path)


@router.delete("/entry", summary="按相对路径删除 llm-wiki 内的文件")
async def delete_by_path(path: str):
    """删除 llm-wiki 内的单个文件。raw/origin 下的文件会同时清理全文与数据库记录。"""
    file_path = resolve_wiki_file(path)
    if _should_hide(file_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除该文件")
    try:
        if _is_origin_file(file_path):
            return delete_origin_file(file_path)
        file_path.unlink()
        return {"success": True, "message": f"文件 {normalize_rel_path(path)} 已成功删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {e}",
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
        return delete_origin_file(file_path)
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


@router.get("/preview", response_model=PreviewResponse, summary="按相对路径预览 llm-wiki 内的文件")
async def preview_by_path(path: str) -> PreviewResponse:
    """预览 llm-wiki 下任意文本文件；origin 中的二进制文件优先展示已转换 Markdown"""
    return build_preview(resolve_wiki_file(path))


@router.get("/preview/{filename}", response_model=PreviewResponse, summary="预览 raw/origin 文件内容")
async def preview_file(filename: str) -> PreviewResponse:
    """获取文本类文件内容或查看已转换的 Markdown 内容"""
    file_path = get_safe_file_path(filename)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {filename}"
        )
    return build_preview(file_path)
