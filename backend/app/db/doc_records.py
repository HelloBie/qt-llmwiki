"""文档元数据数据库管理模块：
基于 SQLite 单表记录原始文件与转换后 Markdown 文件的映射关系、纯数字自增唯一标识 doc_id（从 1 开始递增且不可变更）及文件双路径。
"""

import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager

BACKEND_APP_DIR = Path(__file__).resolve().parent.parent
DOCUMENT_DIR = BACKEND_APP_DIR / "document" / "llm-wiki"
DEFAULT_DB_PATH = DOCUMENT_DIR / "documents.db"


def get_db_path() -> Path:
    """获取 SQLite 数据库文件物理路径，若环境变量有指定则优先采用"""
    env_path = os.getenv("DOC_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


@contextmanager
def get_db_connection(db_path: Optional[Path] = None):
    """SQLite 数据库连接上下文管理器，自动管理事务与 Row 工厂，并保证基础表结构存在"""
    target_path = db_path or get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS document_records (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_filename TEXT NOT NULL UNIQUE,
            md_filename TEXT,
            origin_path TEXT NOT NULL,
            md_path TEXT,
            file_type TEXT,
            file_size INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    """初始化数据库表结构：创建 document_records 表（纯数字自增编号，从 1 开始递增）及索引"""
    with get_db_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_records (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_filename TEXT NOT NULL UNIQUE,
                md_filename TEXT,
                origin_path TEXT NOT NULL,
                md_path TEXT,
                file_type TEXT,
                file_size INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_origin_filename ON document_records(origin_filename);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_md_filename ON document_records(md_filename);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON document_records(status);")


def get_record_by_doc_id(doc_id: Union[int, str], db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """根据唯一文档数字标识 doc_id 获取记录"""
    try:
        numeric_id = int(doc_id)
    except (ValueError, TypeError):
        return None

    with get_db_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM document_records WHERE doc_id = ?", (numeric_id,)).fetchone()
        return dict(row) if row else None


def get_record_by_origin_filename(origin_filename: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """根据原始文件名获取记录"""
    with get_db_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM document_records WHERE origin_filename = ?", (origin_filename,)).fetchone()
        return dict(row) if row else None


def get_record_by_md_filename(md_filename: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """根据转换后的 Markdown 文件名获取记录"""
    with get_db_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM document_records WHERE md_filename = ?", (md_filename,)).fetchone()
        return dict(row) if row else None


def get_or_create_record(
    origin_filename: str,
    origin_path: Optional[str] = None,
    md_filename: Optional[str] = None,
    md_path: Optional[str] = None,
    file_type: Optional[str] = None,
    file_size: int = 0,
    status: str = "pending",
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """获取已有记录；若不存在则为原始文件分配自增纯数字唯一标识（从 1 开始递增，且永久不可改变）"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stem = Path(origin_filename).stem
    default_origin_path = origin_path or f"raw/origin/{origin_filename}"
    default_md_filename = md_filename or f"{stem}.md"
    default_md_path = md_path or f"raw/fulltext/{default_md_filename}"
    ftype = file_type or Path(origin_filename).suffix.lstrip(".").lower()

    with get_db_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT * FROM document_records WHERE origin_filename = ?",
            (origin_filename,)
        ).fetchone()

        if existing:
            # 拥有标识后标识（doc_id）绝对不允许改变，仅更新元数据路径或大小
            conn.execute(
                """
                UPDATE document_records
                SET origin_path = COALESCE(?, origin_path),
                    file_size = CASE WHEN ? > 0 THEN ? ELSE file_size END,
                    updated_at = ?
                WHERE origin_filename = ?
                """,
                (origin_path, file_size, file_size, now_str, origin_filename)
            )
            updated = conn.execute(
                "SELECT * FROM document_records WHERE origin_filename = ?",
                (origin_filename,)
            ).fetchone()
            return dict(updated)

        # 插入新记录，由 SQLite AUTOINCREMENT 生成从 1 开始递增的纯数字编号
        cursor = conn.execute(
            """
            INSERT INTO document_records (
                origin_filename, md_filename, origin_path, md_path,
                file_type, file_size, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                origin_filename,
                default_md_filename,
                default_origin_path,
                default_md_path,
                ftype,
                file_size,
                status,
                now_str,
                now_str,
            )
        )
        new_doc_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM document_records WHERE doc_id = ?", (new_doc_id,)).fetchone()
        return dict(row)


def update_record_converted(
    doc_id: Union[int, str],
    md_filename: Optional[str] = None,
    md_path: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """标记文档已转换完成，更新 md 文件名、路径与修改时间，但 doc_id 严格保持不变"""
    try:
        numeric_id = int(doc_id)
    except (ValueError, TypeError):
        return None

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE document_records
            SET status = 'converted',
                md_filename = COALESCE(?, md_filename),
                md_path = COALESCE(?, md_path),
                updated_at = ?
            WHERE doc_id = ?
            """,
            (md_filename, md_path, now_str, numeric_id)
        )
        row = conn.execute("SELECT * FROM document_records WHERE doc_id = ?", (numeric_id,)).fetchone()
        return dict(row) if row else None


def delete_record_by_origin_filename(origin_filename: str, db_path: Optional[Path] = None) -> bool:
    """根据原始文件名删除记录"""
    with get_db_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM document_records WHERE origin_filename = ?", (origin_filename,))
        return cur.rowcount > 0


def delete_record_by_doc_id(doc_id: Union[int, str], db_path: Optional[Path] = None) -> bool:
    """根据唯一文档标识删除记录"""
    try:
        numeric_id = int(doc_id)
    except (ValueError, TypeError):
        return False

    with get_db_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM document_records WHERE doc_id = ?", (numeric_id,))
        return cur.rowcount > 0


def list_all_records(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """列出全部文档记录，按 doc_id 升序排序"""
    with get_db_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM document_records ORDER BY doc_id ASC").fetchall()
        return [dict(r) for r in rows]


def sync_documents_with_disk(
    origin_dir: Path,
    fulltext_dir: Path,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """扫描磁盘目录并与数据库建立一致性同步：
    1. 磁盘有文件但数据库无记录：为其分配全局唯一的从 1 递增的纯数字 doc_id 并入库；
    2. 若对应的 fulltext/{stem}.md 存在，则标记 status 为 converted 并记录对应 md_path；
    3. 磁盘文件若已物理删除，则同步清理数据库遗留记录。
    """
    init_db(db_path)
    origin_dir.mkdir(parents=True, exist_ok=True)
    fulltext_dir.mkdir(parents=True, exist_ok=True)

    disk_files: Dict[str, Path] = {}
    for item in sorted(origin_dir.iterdir()):
        if item.is_file() and not item.name.startswith("."):
            disk_files[item.name] = item

    # 1. 注册或更新所有磁盘文件（保持文件名排序录入，从 1 递增分配）
    for name, path in disk_files.items():
        stem = path.stem
        target_md = fulltext_dir / f"{stem}.md"
        is_converted = target_md.is_file()
        file_size = path.stat().st_size
        file_type = path.suffix.lstrip(".").lower()

        rec = get_or_create_record(
            origin_filename=name,
            origin_path=f"raw/origin/{name}",
            md_filename=f"{stem}.md",
            md_path=f"raw/fulltext/{stem}.md",
            file_type=file_type,
            file_size=file_size,
            status="converted" if is_converted else "pending",
            db_path=db_path,
        )

        if is_converted and rec.get("status") != "converted":
            update_record_converted(
                rec["doc_id"],
                md_filename=f"{stem}.md",
                md_path=f"raw/fulltext/{stem}.md",
                db_path=db_path,
            )

    # 2. 清理磁盘已不存在的旧记录
    all_recs = list_all_records(db_path)
    for r in all_recs:
        if r["origin_filename"] not in disk_files:
            delete_record_by_origin_filename(r["origin_filename"], db_path)

    return list_all_records(db_path)
