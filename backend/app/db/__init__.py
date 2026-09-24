"""数据库模块：基于 SQLite 的轻量文档记录与状态持久化管理"""
from .doc_records import (
    init_db,
    get_or_create_record,
    get_record_by_doc_id,
    get_record_by_origin_filename,
    get_record_by_md_filename,
    update_record_converted,
    delete_record_by_origin_filename,
    list_all_records,
    sync_documents_with_disk,
    get_db_path,
)

__all__ = [
    "init_db",
    "get_or_create_record",
    "get_record_by_doc_id",
    "get_record_by_origin_filename",
    "get_record_by_md_filename",
    "update_record_converted",
    "delete_record_by_origin_filename",
    "list_all_records",
    "sync_documents_with_disk",
    "get_db_path",
]
