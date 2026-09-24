import { apiClient } from './client'

export interface FileItem {
  id: string
  name: string
  ext: string
  size: string
  size_bytes: number
  status: 'indexed' | 'indexing' | 'pending' | string
  updated_at: string
}

export interface PreviewData {
  name: string
  ext: string
  is_binary: boolean
  content?: string
  size: string
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

/** 预览文件内容 */
export async function fetchPreview(filename: string): Promise<PreviewData> {
  return apiClient.get(`/files/preview/${encodeURIComponent(filename)}`)
}

/** 获取下载 URL */
export function getDownloadUrl(filename: string): string {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  return `${baseURL}/files/download/${encodeURIComponent(filename)}`
}
