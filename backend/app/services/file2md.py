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
import posixpath
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


def col_letter_to_index(col_str: str) -> int:
    """Excel 列名转 0-indexed 索引，如 A->0, B->1, Z->25, AA->26"""
    idx = 0
    for char in col_str.upper():
        if "A" <= char <= "Z":
            idx = idx * 26 + (ord(char) - ord("A") + 1)
    return idx - 1


def parse_xlsx_to_markdown(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """深度解析 .xlsx 工作簿为 Markdown：
    1. 提取 core.xml 元数据 (标题、作者、修改时间等)；
    2. 提取 sharedStrings.xml (支持单段及富文本多 run)；
    3. 读取 workbook.xml 与 rels 映射真实 Sheet 业务名称；
    4. 完整支持 inlineStr, s (sharedString), b (bool), str (公式文本), n (数值) 等单元格格式；
    5. 基于行列坐标构建二维网格，自动切分表格标题/横幅段落与数据表，保留完整数据与多表格结构。
    """
    metadata: Dict[str, Any] = {}
    md_lines: List[str] = []

    try:
        with zipfile.ZipFile(file_path, "r") as z:
            s_ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
            r_ns = "{http://schemas.openxmlformats.org/package/2006/relationships}"

            # 1. 提取 core.xml 元数据
            if "docProps/core.xml" in z.namelist():
                try:
                    core_tree = ET.fromstring(z.read("docProps/core.xml"))
                    for child in core_tree:
                        tag_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        if child.text:
                            metadata[tag_name] = child.text.strip()
                except Exception:
                    pass

            # 2. 提取 sharedStrings.xml 共享字符串池
            shared_strings: List[str] = []
            if "xl/sharedStrings.xml" in z.namelist():
                try:
                    ss_tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                    for si in ss_tree.iter(f"{s_ns}si"):
                        texts = [t.text for t in si.iter(f"{s_ns}t") if t.text]
                        shared_strings.append("".join(texts))
                except Exception:
                    pass

            # 3. 解析工作表列表及对应物理路径
            sheets: List[Tuple[str, str]] = []
            if "xl/workbook.xml" in z.namelist() and "xl/_rels/workbook.xml.rels" in z.namelist():
                try:
                    wb_tree = ET.fromstring(z.read("xl/workbook.xml"))
                    wb_rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
                    rel_map = {
                        rel.get("Id"): rel.get("Target")
                        for rel in wb_rels.findall(f"{r_ns}Relationship")
                    }

                    for sheet_elem in wb_tree.iter(f"{s_ns}sheet"):
                        s_name = sheet_elem.get("name") or "Sheet"
                        r_id = sheet_elem.get(
                            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                        )
                        raw_target = rel_map.get(r_id, "")
                        if raw_target:
                            clean_t = raw_target.lstrip("/")
                            norm_target = clean_t if clean_t.startswith("xl/") else f"xl/{clean_t}"
                            norm_target = posixpath.normpath(norm_target)
                            if norm_target in z.namelist():
                                sheets.append((s_name, norm_target))
                except Exception:
                    pass

            if not sheets:
                raw_sheet_paths = [
                    n for n in z.namelist() if re.match(r"^xl/worksheets/sheet\d+\.xml$", n)
                ]
                raw_sheet_paths.sort()
                for idx, sp in enumerate(raw_sheet_paths, 1):
                    sheets.append((f"Sheet {idx}", sp))

            # 4. 解析每个 Worksheet
            for sheet_name, sheet_path in sheets:
                md_lines.append(f"## {sheet_name}\n")
                sheet_tree = ET.fromstring(z.read(sheet_path))

                # 建立行列二维字典 {(row_idx, col_idx): value}
                grid: Dict[Tuple[int, int], str] = {}
                max_r = 0
                max_c = 0

                for row in sheet_tree.iter(f"{s_ns}row"):
                    row_attr = row.get("r")
                    curr_r = int(row_attr) if row_attr and row_attr.isdigit() else max_r + 1

                    for c in row.iter(f"{s_ns}c"):
                        cell_ref = c.get("r", "")
                        match = re.match(r"^([A-Za-z]+)(\d+)$", cell_ref)
                        if match:
                            col_str, row_str = match.groups()
                            c_idx = col_letter_to_index(col_str)
                            r_idx = int(row_str)
                        else:
                            c_idx = max_c + 1
                            r_idx = curr_r

                        c_type = c.get("t")
                        val = ""

                        if c_type == "inlineStr":
                            texts = [t.text for t in c.iter(f"{s_ns}t") if t.text]
                            val = "".join(texts)
                        elif c_type == "s":
                            v = c.find(f"{s_ns}v")
                            if v is not None and v.text and v.text.isdigit():
                                s_idx = int(v.text)
                                if s_idx < len(shared_strings):
                                    val = shared_strings[s_idx]
                        elif c_type == "b":
                            v = c.find(f"{s_ns}v")
                            if v is not None and v.text:
                                val = "TRUE" if v.text == "1" else "FALSE"
                        else:
                            # 提取数值、公式计算缓存 <v>，或内嵌 <t>
                            v = c.find(f"{s_ns}v")
                            if v is not None and v.text:
                                val = v.text
                            else:
                                texts = [t.text for t in c.iter(f"{s_ns}t") if t.text]
                                if texts:
                                    val = "".join(texts)

                        # 清洗与格式化单元格内容
                        val = val.strip().replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")
                        if val:
                            grid[(r_idx, c_idx)] = val
                            if c_idx > max_c:
                                max_c = c_idx
                            if r_idx > max_r:
                                max_r = r_idx

                if not grid:
                    md_lines.append("> (空白工作表)\n")
                    continue

                # 识别表格与标题段落结构
                elements: List[Tuple[str, Any]] = []
                current_table: List[List[str]] = []

                for r in range(1, max_r + 1):
                    row_vals = [grid.get((r, c), "") for c in range(max_c + 1)]
                    non_empty = [v for v in row_vals if v]

                    if not non_empty:
                        if current_table:
                            elements.append(("table", current_table))
                            current_table = []
                        continue

                    # 若整行仅有 1 个非空单元格，且位于靠前列（如标题/说明行）
                    if len(non_empty) == 1 and row_vals[0]:
                        if current_table:
                            elements.append(("table", current_table))
                            current_table = []
                        elements.append(("heading", row_vals[0]))
                    else:
                        current_table.append(row_vals)

                if current_table:
                    elements.append(("table", current_table))

                # 渲染元素
                for el_type, el_data in elements:
                    if el_type == "heading":
                        md_lines.append(f"### {el_data}\n")
                    elif el_type == "table":
                        # 计算此子表格实际用到的最大列
                        sub_max_col = max(
                            max(c for c, cell in enumerate(r_vals) if cell)
                            for r_vals in el_data
                        )
                        col_count = sub_max_col + 1
                        table_rows = []
                        for r_vals in el_data:
                            trimmed = [r_vals[c].replace("|", "\\|") for c in range(col_count)]
                            table_rows.append(trimmed)

                        if table_rows:
                            header = table_rows[0]
                            md_lines.append("| " + " | ".join(header) + " |")
                            md_lines.append("| " + " | ".join(["---"] * col_count) + " |")
                            for data_row in table_rows[1:]:
                                md_lines.append("| " + " | ".join(data_row) + " |")
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
