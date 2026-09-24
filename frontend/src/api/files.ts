import { apiClient } from './client'

export interface FileItem {
  id: string
  doc_id?: string
  name: string
  ext: string
  size: string
  size_bytes: number
  status: 'indexed' | 'indexing' | 'pending' | string
  updated_at: string
  is_converted?: boolean
  converted_target?: string
  origin_path?: string
  md_path?: string
}

export interface PreviewData {
  name: string
  ext: string
  is_binary: boolean
  content?: string
  size: string
  doc_id?: string
  is_converted_preview?: boolean
}

export interface DocumentRecord {
  doc_id: string
  origin_filename: string
  md_filename?: string
  origin_path: string
  md_path?: string
  file_type?: string
  file_size?: number
  status: string
  created_at: string
  updated_at: string
}

export interface File2MdResult {
  success: boolean
  doc_id?: string
  source_file: string
  target_file?: string
  message: string
  skipped?: boolean
  char_count?: number
  file_size?: string
}

export interface FulltextItem {
  name: string
  doc_id?: string
  origin_filename?: string
  origin_path?: string
  md_path?: string
  size: string
  size_bytes: number
  updated_at: string
}

/** 获取 raw/origin 目录下的所有文件 */
export async function fetchFiles(): Promise<FileItem[]> {
  return apiClient.get('/files')
}

/** 上传文件至 raw/origin */
export async function uploadFiles(files: File[]): Promise<FileItem[]> {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  return apiClient.post('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

/** 删除 raw/origin 下的指定文件 */
export async function deleteFile(filename: string): Promise<void> {
  return apiClient.delete(`/files/${encodeURIComponent(filename)}`)
}

/** 预览文件内容（支持原生文本与已转换 Markdown 预览） */
export async function fetchPreview(filename: string): Promise<PreviewData> {
  return apiClient.get(`/files/preview/${encodeURIComponent(filename)}`)
}

/** 单个文件转换为 Markdown */
export async function convertSingleFile2Md(filename: string, force = true): Promise<File2MdResult> {
  return apiClient.post(`/files/${encodeURIComponent(filename)}/file2md?force=${force}`)
}

/** 批量全部文件转换为 Markdown */
export async function convertAllFiles2Md(force = false): Promise<{ success: boolean; message: string; results: File2MdResult[] }> {
  return apiClient.post(`/files/file2md?force=${force}`)
}

/** 获取 raw/fulltext 下已转换的文件列表 */
export async function fetchFulltextList(): Promise<FulltextItem[]> {
  return apiClient.get('/files/fulltext')
}

/** 读取已转换的 Markdown 文件文本 */
export async function fetchFulltextContent(filename: string): Promise<{ filename: string; content: string; size: string; updated_at: string }> {
  return apiClient.get(`/files/fulltext/${encodeURIComponent(filename)}`)
}

/** 获取下载 URL */
export function getDownloadUrl(filename: string): string {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  return `${baseURL}/files/download/${encodeURIComponent(filename)}`
}

/** 获取 SQLite 数据库中记录的文档映射全表信息 */
export async function fetchDocumentRecords(): Promise<DocumentRecord[]> {
  return apiClient.get('/files/records')
}
