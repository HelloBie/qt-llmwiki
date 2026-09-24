"""file2md 服务：将 wiki/raw/origin 目录下的各类原始素材文件转换为 Markdown，
并在文档头部注入标准属性元数据（YAML Frontmatter 与可读摘要），
最终保存到 wiki/raw/fulltext 目录下。
"""

import os
import sys
import csv
import json
import zipfile
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
import xml.etree.ElementTree as ET

# 默认路径计算
BACKEND_APP_DIR = Path(__file__).resolve().parent.parent
DOCUMENT_DIR = BACKEND_APP_DIR / "document" / "llm-wiki"
RAW_ORIGIN_DIR = DOCUMENT_DIR / "raw" / "origin"
RAW_FULLTEXT_DIR = DOCUMENT_DIR / "raw" / "fulltext"

if str(BACKEND_APP_DIR.parent) not in sys.path:
    sys.path.insert(0, str(BACKEND_APP_DIR.parent))

from app.db.doc_records import (
    get_or_create_record,
    update_record_converted,
    get_record_by_origin_filename,
    sync_documents_with_disk,
)


def ensure_dirs(origin_dir: Optional[Path] = None, fulltext_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """确保输入输出目录存在"""
    od = origin_dir or RAW_ORIGIN_DIR
    fd = fulltext_dir or RAW_FULLTEXT_DIR
    od.mkdir(parents=True, exist_ok=True)
    fd.mkdir(parents=True, exist_ok=True)
    return od, fd


def format_file_size(size_bytes: int) -> str:
    """人类可读的文件大小格式化"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def read_text_with_encoding(file_path: Path) -> str:
    """自动探测编码读取纯文本文件"""
    encodings = ["utf-8", "utf-8-sig", "gb18030", "gbk", "big5", "latin-1"]
    for enc in encodings:
        try:
            return file_path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return file_path.read_text(encoding="utf-8", errors="replace")


def parse_docx_to_markdown(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """解析 .docx 文件为结构化 Markdown（段落、各级标题、表格），并提取 core.xml 元数据"""
    metadata: Dict[str, Any] = {}
    md_lines: List[str] = []

    with zipfile.ZipFile(file_path, "r") as z:
        # 1. 提取 core.xml 中的作者、创建时间等元信息
        if "docProps/core.xml" in z.namelist():
            try:
                core_xml = z.read("docProps/core.xml")
                core_tree = ET.fromstring(core_xml)
                for child in core_tree:
                    tag_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child.text:
                        metadata[tag_name] = child.text.strip()
            except Exception:
                pass

        # 2. 提取 word/document.xml 内容
        if "word/document.xml" not in z.namelist():
            return "", metadata

        doc_xml = z.read("word/document.xml")
        tree = ET.fromstring(doc_xml)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

        body = tree.find(f"{ns}body")
        if body is None:
            return "", metadata

        for elem in body:
            tag = elem.tag.replace(ns, "")

            # 处理段落
            if tag == "p":
                texts = [t.text for t in elem.iter(f"{ns}t") if t.text]
                if not texts:
                    continue
                p_text = "".join(texts).strip()
                if not p_text:
                    continue

                # 识别标题级别
                pPr = elem.find(f"{ns}pPr")
                pStyle = pPr.find(f"{ns}pStyle") if pPr is not None else None
                style_val = pStyle.get(f"{ns}val", "") if pStyle is not None else ""

                if style_val in ("Heading1", "1", "Title"):
                    md_lines.append(f"# {p_text}\n")
                elif style_val in ("Heading2", "2", "Subtitle"):
                    md_lines.append(f"## {p_text}\n")
                elif style_val in ("Heading3", "3"):
                    md_lines.append(f"### {p_text}\n")
                elif style_val in ("Heading4", "4"):
                    md_lines.append(f"#### {p_text}\n")
                else:
                    # 检查是否为列表项
                    numPr = pPr.find(f"{ns}numPr") if pPr is not None else None
                    if numPr is not None:
                        md_lines.append(f"- {p_text}")
                    else:
                        md_lines.append(f"{p_text}\n")

            # 处理表格
            elif tag == "tbl":
                rows: List[List[str]] = []
                for tr in elem.iter(f"{ns}tr"):
                    row: List[str] = []
                    for tc in tr.iter(f"{ns}tc"):
                        cell_paras: List[str] = []
                        for p in tc.iter(f"{ns}p"):
                            cell_text = "".join(t.text for t in p.iter(f"{ns}t") if t.text).strip()
                            if cell_text:
                                cell_paras.append(cell_text)
                        cell_combined = "<br>".join(cell_paras).replace("|", "\\|")
                        row.append(cell_combined)
                    if any(row):
                        rows.append(row)

                if rows:
                    col_count = max(len(r) for r in rows)
                    # 表头行
                    header = rows[0] + [""] * (col_count - len(rows[0]))
                    md_lines.append("| " + " | ".join(header) + " |")
                    md_lines.append("| " + " | ".join(["---"] * col_count) + " |")
                    # 数据行
                    for r in rows[1:]:
                        padded = r + [""] * (col_count - len(r))
                        md_lines.append("| " + " | ".join(padded) + " |")
                    md_lines.append("\n")

    return "\n".join(md_lines).strip(), metadata


def parse_pptx_to_markdown(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """解析 .pptx 幻灯片为 Markdown"""
    metadata: Dict[str, Any] = {}
    md_lines: List[str] = []

    try:
        with zipfile.ZipFile(file_path, "r") as z:
            slide_names = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml", n)]
            slide_names.sort(key=lambda s: int(re.search(r"\d+", s).group()))

            for idx, slide_path in enumerate(slide_names, 1):
                md_lines.append(f"## Slide {idx}\n")
                slide_xml = z.read(slide_path)
                tree = ET.fromstring(slide_xml)
                a_ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

                for p_elem in tree.iter(f"{a_ns}p"):
                    texts = [t.text for t in p_elem.iter(f"{a_ns}t") if t.text]
                    if texts:
                        line = "".join(texts).strip()
                        if line:
                            md_lines.append(f"- {line}")
                md_lines.append("")
    except Exception as e:
        md_lines.append(f"> PPTX 解析异常: {e}")

    return "\n".join(md_lines).strip(), metadata


def parse_xlsx_to_markdown(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """解析 .xlsx 表格为 Markdown"""
    metadata: Dict[str, Any] = {}
    md_lines: List[str] = []

    try:
        with zipfile.ZipFile(file_path, "r") as z:
            shared_strings = []
            if "xl/sharedStrings.xml" in z.namelist():
                ss_tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                s_ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
                for si in ss_tree.iter(f"{s_ns}si"):
                    text_parts = [t.text for t in si.iter(f"{s_ns}t") if t.text]
                    shared_strings.append("".join(text_parts))

            sheet_names = [n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml", n)]
            sheet_names.sort()

            for sheet_idx, sheet_path in enumerate(sheet_names, 1):
                md_lines.append(f"### Sheet {sheet_idx}\n")
                sheet_tree = ET.fromstring(z.read(sheet_path))
                s_ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

                rows_data: List[List[str]] = []
                for row_elem in sheet_tree.iter(f"{s_ns}row"):
                    row_vals: List[str] = []
                    for c_elem in row_elem.iter(f"{s_ns}c"):
                        cell_type = c_elem.get("t")
                        v_elem = c_elem.find(f"{s_ns}v")
                        val = v_elem.text if v_elem is not None and v_elem.text else ""
                        if cell_type == "s" and val.isdigit():
                            idx = int(val)
                            val = shared_strings[idx] if idx < len(shared_strings) else val
                        row_vals.append(val.replace("|", "/"))
                    if any(row_vals):
                        rows_data.append(row_vals)

                if rows_data:
                    max_cols = max(len(r) for r in rows_data)
                    header = rows_data[0] + [""] * (max_cols - len(rows_data[0]))
                    md_lines.append("| " + " | ".join(header) + " |")
                    md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")
                    for r in rows_data[1:]:
                        md_lines.append("| " + " | ".join(r + [""] * (max_cols - len(r))) + " |")
                    md_lines.append("")
    except Exception as e:
        md_lines.append(f"> XLSX 解析异常: {e}")

    return "\n".join(md_lines).strip(), metadata


def parse_csv_to_markdown(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """解析 CSV 为 Markdown 表格"""
    content = read_text_with_encoding(file_path)
    md_lines: List[str] = []
    rows: List[List[str]] = []

    try:
        reader = csv.reader(content.splitlines())
        for row in reader:
            if row:
                rows.append([cell.replace("|", "\\|").strip() for cell in row])
        if rows:
            col_count = max(len(r) for r in rows)
            header = rows[0] + [""] * (col_count - len(rows[0]))
            md_lines.append("| " + " | ".join(header) + " |")
            md_lines.append("| " + " | ".join(["---"] * col_count) + " |")
            for r in rows[1:]:
                padded = r + [""] * (col_count - len(r))
                md_lines.append("| " + " | ".join(padded) + " |")
    except Exception:
        md_lines.append(f"```csv\n{content}\n```")

    return "\n".join(md_lines).strip(), {}


def parse_pdf_to_markdown(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """解析 PDF 文件文本"""
    metadata: Dict[str, Any] = {}
    text_content = ""

    # 优先尝试 pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        metadata["pages_count"] = len(reader.pages)
        pages_text = []
        for idx, page in enumerate(reader.pages, 1):
            t = page.extract_text() or ""
            if t.strip():
                pages_text.append(f"## Page {idx}\n\n{t.strip()}")
        text_content = "\n\n".join(pages_text)
    except ImportError:
        # 尝试 pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(str(file_path)) as pdf:
                metadata["pages_count"] = len(pdf.pages)
                pages_text = []
                for idx, page in enumerate(pdf.pages, 1):
                    t = page.extract_text() or ""
                    if t.strip():
                        pages_text.append(f"## Page {idx}\n\n{t.strip()}")
                text_content = "\n\n".join(pages_text)
        except ImportError:
            # 纯 Python 二进制流提取可打印字符兜底
            raw_bytes = file_path.read_bytes()
            # 匹配常规可打印 UTF-8 / ASCII 字符串片段
            matches = re.findall(rb"[(]([\w\s\u4e00-\u9fa5\.,:;?!-]{2,})[)]", raw_bytes)
            extracted = [m.decode("utf-8", errors="ignore") for m in matches]
            if extracted:
                text_content = "\n\n".join(extracted)
            else:
                text_content = f"> [PDF] 该文件已存入知识库，原文件大小为 {format_file_size(len(raw_bytes))}。"

    return text_content.strip(), metadata


def extract_content(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """根据文件类型调用对应的提取器"""
    ext = file_path.suffix.lower()

    if ext == ".docx":
        return parse_docx_to_markdown(file_path)
    elif ext == ".pptx":
        return parse_pptx_to_markdown(file_path)
    elif ext == ".xlsx":
        return parse_xlsx_to_markdown(file_path)
    elif ext == ".csv":
        return parse_csv_to_markdown(file_path)
    elif ext == ".json":
        raw = read_text_with_encoding(file_path)
        try:
            obj = json.loads(raw)
            formatted = json.dumps(obj, ensure_ascii=False, indent=2)
            return f"```json\n{formatted}\n```", {}
        except Exception:
            return f"```json\n{raw}\n```", {}
    elif ext == ".pdf":
        return parse_pdf_to_markdown(file_path)
    elif ext in (".md", ".markdown"):
        raw = read_text_with_encoding(file_path)
        # 剔除可能已存在的 YAML Frontmatter 以免重复嵌套
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                raw = parts[2].strip()
        return raw.strip(), {}
    elif ext == ".txt":
        raw = read_text_with_encoding(file_path)
        return raw.strip(), {}
    else:
        # 其他类型作为纯文本读取尝试
        raw = read_text_with_encoding(file_path)
        return raw.strip(), {}


def inject_doc_number_to_content(content: str, doc_id: Optional[Union[int, str]]) -> str:
    """将文件标识作为『文件编号』写入 Markdown 正文起始处"""
    if doc_id is None:
        return content

    doc_str = str(doc_id).strip()
    prefix = f"**文件编号**：{doc_str}\n\n"

    # 若正文已经存在文件编号标记，避免重复注入
    stripped = content.strip()
    if (
        stripped.startswith(f"**文件编号**：{doc_str}")
        or stripped.startswith(f"文件编号：{doc_str}")
        or stripped.startswith(f"**文件编号**:{doc_str}")
        or stripped.startswith(f"文件编号:{doc_str}")
    ):
        return content

    if content:
        return f"{prefix}{content.lstrip()}"
    return prefix.rstrip()


def generate_frontmatter(
    source_file: Path,
    target_file: Path,
    content: str,
    doc_id: Optional[Union[int, str]] = None,
    extra_meta: Optional[Dict[str, Any]] = None,
) -> str:
    """生成包含来源属性与时间戳的标准 YAML Frontmatter 及可视化文档头（包含纯数字递增文件编号 doc_id）"""
    stat = source_file.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    ctime = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    size_str = format_file_size(stat.st_size)
    char_count = len(content)

    frontmatter_dict: Dict[str, Any] = {}
    if doc_id is not None:
        try:
            numeric_id = int(doc_id)
            frontmatter_dict["doc_id"] = numeric_id
            frontmatter_dict["file_number"] = numeric_id
        except (ValueError, TypeError):
            frontmatter_dict["doc_id"] = doc_id
            frontmatter_dict["file_number"] = doc_id
    frontmatter_dict.update({
        "title": source_file.stem,
        "source_file": source_file.name,
        "source_path": f"raw/origin/{source_file.name}",
        "target_file": target_file.name,
        "target_path": f"raw/fulltext/{target_file.name}",
        "file_type": source_file.suffix.lower().lstrip("."),
        "file_size": size_str,
        "file_size_bytes": stat.st_size,
        "char_count": char_count,
        "created_at": ctime,
        "modified_at": mtime,
        "converted_at": now_str,
        "converter": "file2md",
    })

    if extra_meta:
        for k, v in extra_meta.items():
            if k not in frontmatter_dict and v:
                frontmatter_dict[k] = v

    # 构造 YAML
    yaml_lines = ["---"]
    for k, v in frontmatter_dict.items():
        if isinstance(v, (int, float, bool)):
            yaml_lines.append(f"{k}: {v}")
        else:
            # 安全转义双引号
            safe_str = str(v).replace('"', '\\"')
            yaml_lines.append(f'{k}: "{safe_str}"')
    yaml_lines.append("---\n")

    # 可读视觉信息块（头部展示文件编号与源素材信息）
    doc_id_chip = f"**文件编号**：{doc_id} | " if doc_id is not None else ""
    header_block = (
        f"> {doc_id_chip}**原始素材**：`raw/origin/{source_file.name}` ({size_str}) | "
        f"**转换时间**：{now_str} | **字数**：{char_count}\n\n"
    )

    return "\n".join(yaml_lines) + "\n" + header_block


def convert_file(
    source_file: Path,
    fulltext_dir: Optional[Path] = None,
    force: bool = False,
    doc_id: Optional[Union[int, str]] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """转换单个 origin 原始文件到 fulltext Markdown 文件，统一由数据库分配/读取相同 doc_id，并将标识作为文件编号写入正文"""
    if not source_file.is_file():
        raise FileNotFoundError(f"源文件不存在: {source_file}")

    target_dir = fulltext_dir or RAW_FULLTEXT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    # 转换后目标文件名为 原文件名.md
    target_name = f"{source_file.stem}.md"
    target_file = target_dir / target_name

    # 1. 查询或创建数据库记录，确保原文件与转换出的 MD 文档共享同一个唯一标识 doc_id
    stat = source_file.stat()
    file_type = source_file.suffix.lstrip(".").lower()
    rec = get_or_create_record(
        origin_filename=source_file.name,
        origin_path=f"raw/origin/{source_file.name}",
        md_filename=target_name,
        md_path=f"raw/fulltext/{target_name}",
        file_type=file_type,
        file_size=stat.st_size,
        status="pending",
        db_path=db_path,
    )
    assigned_doc_id = int(doc_id) if doc_id is not None else int(rec["doc_id"])

    # 检查是否已转换且未过期（源文件未改动）
    if not force and target_file.is_file():
        source_mtime = source_file.stat().st_mtime
        target_mtime = target_file.stat().st_mtime
        if target_mtime >= source_mtime:
            update_record_converted(
                doc_id=assigned_doc_id,
                md_filename=target_name,
                md_path=f"raw/fulltext/{target_name}",
                db_path=db_path,
            )
            return {
                "success": True,
                "skipped": True,
                "doc_id": assigned_doc_id,
                "source_file": source_file.name,
                "target_file": target_name,
                "target_path": str(target_file),
                "message": "文件已是最新转换版本，无需重复处理",
            }

    # 执行内容提取
    content, extra_meta = extract_content(source_file)

    # 将文件标识作为『文件编号』写入正文起始处
    body_content = inject_doc_number_to_content(content, assigned_doc_id)

    # 生成 Frontmatter 头部与元信息（写入统一标识 doc_id 及 file_number）
    header = generate_frontmatter(
        source_file=source_file,
        target_file=target_file,
        content=body_content,
        doc_id=assigned_doc_id,
        extra_meta=extra_meta,
    )

    # 完整 Markdown：Frontmatter + 顶部引用头 + 包含文件编号的正文
    full_markdown = header + body_content + "\n"

    # 写入 target_file
    target_file.write_text(full_markdown, encoding="utf-8")

    # 更新数据库为 converted 状态，记录 md_filename 与 md_path
    update_record_converted(
        doc_id=assigned_doc_id,
        md_filename=target_name,
        md_path=f"raw/fulltext/{target_name}",
        db_path=db_path,
    )

    return {
        "success": True,
        "skipped": False,
        "doc_id": assigned_doc_id,
        "source_file": source_file.name,
        "target_file": target_name,
        "target_path": str(target_file),
        "char_count": len(content),
        "file_size": format_file_size(target_file.stat().st_size),
        "converted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": f"成功将 {source_file.name} 转换为 Markdown (唯一标识: {assigned_doc_id})",
    }


def convert_all(
    origin_dir: Optional[Path] = None,
    fulltext_dir: Optional[Path] = None,
    force: bool = False,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """批量扫描并转换 origin 目录下的所有文件"""
    od, fd = ensure_dirs(origin_dir, fulltext_dir)
    results: List[Dict[str, Any]] = []

    # 扫描所有非隐藏文件
    for item in sorted(od.iterdir()):
        if item.is_file() and not item.name.startswith("."):
            try:
                res = convert_file(item, fd, force=force, db_path=db_path)
                results.append(res)
            except Exception as e:
                results.append({
                    "success": False,
                    "skipped": False,
                    "source_file": item.name,
                    "target_file": f"{item.stem}.md",
                    "error": str(e),
                    "message": f"转换失败: {str(e)}",
                })

    return results


def get_conversion_status(
    origin_dir: Optional[Path] = None,
    fulltext_dir: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """查询当前 origin 原始素材库与 fulltext 转换库的对应状态与数据库持久化记录"""
    od, fd = ensure_dirs(origin_dir, fulltext_dir)

    # 磁盘与数据库先建立同步一致性
    sync_documents_with_disk(od, fd, db_path=db_path)

    origin_files: List[Dict[str, Any]] = []
    converted_count = 0
    total_count = 0

    for item in sorted(od.iterdir()):
        if item.is_file() and not item.name.startswith("."):
            total_count += 1
            target_name = f"{item.stem}.md"
            target_file = fd / target_name
            is_converted = target_file.is_file()
            rec = get_record_by_origin_filename(item.name, db_path=db_path) or {}

            status_info: Dict[str, Any] = {
                "doc_id": rec.get("doc_id"),
                "source_file": item.name,
                "origin_path": rec.get("origin_path", f"raw/origin/{item.name}"),
                "source_size": format_file_size(item.stat().st_size),
                "is_converted": is_converted,
                "target_file": target_name if is_converted else None,
                "md_path": rec.get("md_path") if is_converted else None,
            }

            if is_converted:
                converted_count += 1
                status_info["converted_size"] = format_file_size(target_file.stat().st_size)
                status_info["converted_at"] = datetime.fromtimestamp(
                    target_file.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S")
                # 检查是否过期
                status_info["is_outdated"] = item.stat().st_mtime > target_file.stat().st_mtime

            origin_files.append(status_info)

    return {
        "total_files": total_count,
        "converted_files": converted_count,
        "pending_files": total_count - converted_count,
        "files": origin_files,
    }


if __name__ == "__main__":
    """CLI 入口：支持直接 python -m app.services.file2md 运行"""
    import argparse

    parser = argparse.ArgumentParser(description="file2md: 将 raw/origin 文件转换为 Markdown 并存入 raw/fulltext")
    parser.add_argument("--file", type=str, help="指定转换单个文件（文件名或路径）")
    parser.add_argument("--force", action="store_true", help="强制覆盖已转换的文件")
    parser.add_argument("--status", action="store_true", help="查看转换状态统计")

    args = parser.parse_args()

    if args.status:
        st = get_conversion_status()
        print(f"📊 转换状态统计：总计 {st['total_files']} 个原始文件，已转换 {st['converted_files']} 个，待处理 {st['pending_files']} 个")
        for f in st["files"]:
            conv_flag = "✅ 已转换" if f["is_converted"] else "⏳ 待转换"
            print(f"  - [{f.get('doc_id')}] {f['source_file']} ({f['source_size']}): {conv_flag}")
    elif args.file:
        target_path = Path(args.file)
        if not target_path.is_file():
            target_path = RAW_ORIGIN_DIR / args.file
        print(f"🚀 开始转换单个文件: {target_path}")
        res = convert_file(target_path, force=args.force)
        print(f"结果: {res['message']}")
    else:
        print(f"🚀 开始全量批量转换 raw/origin -> raw/fulltext ...")
        results = convert_all(force=args.force)
        success_num = sum(1 for r in results if r["success"] and not r.get("skipped"))
        skip_num = sum(1 for r in results if r.get("skipped"))
        fail_num = sum(1 for r in results if not r["success"])
        print(f"🎉 批量转换完成！成功: {success_num}, 跳过(最新): {skip_num}, 失败: {fail_num}")
        for r in results:
            print(f"  - {r['source_file']} -> {r.get('target_file', 'N/A')}: {r['message']}")
