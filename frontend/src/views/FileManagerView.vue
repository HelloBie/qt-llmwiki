<template>
  <div class="file-viewport">
    <!-- 顶部状态栏 -->
    <header class="file-topbar">
      <div class="topbar-left">
        <h2 class="page-title">文件管理</h2>
        <div class="path-breadcrumbs">
          <span class="crumb">raw</span>
          <span class="crumb-sep">/</span>
          <span class="crumb active">origin</span>
        </div>
      </div>

      <div class="topbar-right">
        <button class="btn btn-secondary btn-sm" @click="loadFiles" :disabled="loading" title="刷新列表">
          <svg :class="{ spinning: loading }" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          <span>{{ loading ? '同步中...' : '刷新' }}</span>
        </button>

        <button class="btn btn-primary" @click="showUploadModal = true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <span>上传文件</span>
        </button>
      </div>
    </header>

    <div class="file-content">
      <!-- 过滤与搜索栏 -->
      <div class="filter-bar">
        <div class="search-input-wrap">
          <svg class="search-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            v-model="searchQuery"
            placeholder="搜索文件名称..."
          />
          <button v-if="searchQuery" class="clear-search" @click="searchQuery = ''">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div class="type-segmented">
          <button
            v-for="tab in filterTabs"
            :key="tab.key"
            :class="['seg-btn', { active: currentFilter === tab.key }]"
            @click="currentFilter = tab.key"
          >
            {{ tab.name }}
            <span class="count-pill">{{ getFilterCount(tab.key) }}</span>
          </button>
        </div>
      </div>

      <!-- 文件表格 -->
      <div class="table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th class="th-name">名称</th>
              <th class="th-type">格式</th>
              <th class="th-size">大小</th>
              <th class="th-status">知识库状态</th>
              <th class="th-date">修改时间</th>
              <th class="th-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="file in filteredFiles" :key="file.id" class="table-row">
              <td class="td-name">
                <div class="file-icon-box">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                </div>
                <span class="file-title" :title="file.name">{{ file.name }}</span>
              </td>
              <td class="td-type">
                <span class="tag-ext">{{ file.ext.toUpperCase() }}</span>
              </td>
              <td class="td-size">{{ file.size }}</td>
              <td class="td-status">
                <span class="status-chip indexed">
                  <span class="chip-dot"></span>
                  已就绪
                </span>
              </td>
              <td class="td-date">{{ file.updated_at }}</td>
              <td class="td-actions">
                <div class="action-group">
                  <button class="icon-btn" @click="handlePreview(file)" title="预览内容">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  </button>
                  <button class="icon-btn" @click="handleDownload(file)" title="下载文件">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                  </button>
                  <button class="icon-btn danger-hover" @click="handleDelete(file)" title="删除文件">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredFiles.length === 0">
              <td colspan="6" class="empty-state-cell">
                <div class="empty-content">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                  </svg>
                  <span>{{ loading ? '正在加载文件列表...' : 'raw/origin 目录下暂无文件，点击上方按钮上传' }}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 上传弹窗 Modal -->
    <div v-if="showUploadModal" class="modal-backdrop" @click.self="showUploadModal = false">
      <div class="modal-card">
        <div class="modal-titlebar">
          <h3>上传资料至 raw/origin</h3>
          <button class="close-icon-btn" @click="showUploadModal = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div class="modal-content">
          <div
            class="drag-drop-panel"
            :class="{ active: isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
          >
            <input
              type="file"
              ref="fileInputRef"
              style="display: none"
              multiple
              accept=".md,.txt,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.pdf,.csv,.json"
              @change="handleFileInput"
            />
            <div class="upload-icon-circle">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="16 16 12 12 8 16" />
                <line x1="12" y1="12" x2="12" y2="21" />
                <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
              </svg>
            </div>
            <div class="drag-text">点击选择文件 或 将文件拖放到此处</div>
            <div class="drag-types">支持 Office (.docx, .xlsx, .pptx)、Markdown (.md)、纯文本 (.txt)、PDF</div>
          </div>

          <div v-if="uploadList.length > 0" class="queue-box">
            <div class="queue-heading">已选文件 ({{ uploadList.length }})</div>
            <div class="queue-list">
              <div v-for="(item, idx) in uploadList" :key="idx" class="queue-row">
                <span class="queue-name">{{ item.name }}</span>
                <span class="queue-size">{{ formatBytes(item.size) }}</span>
                <button class="queue-del" @click="uploadList.splice(idx, 1)">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showUploadModal = false">取消</button>
          <button class="btn btn-primary" :disabled="uploadList.length === 0 || uploading" @click="confirmUpload">
            <span>{{ uploading ? '正在上传至服务端...' : '确认上传' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 文本预览弹窗 Modal -->
    <div v-if="previewInfo" class="modal-backdrop" @click.self="previewInfo = null">
      <div class="modal-card modal-large">
        <div class="modal-titlebar">
          <div class="preview-title-info">
            <span class="tag-ext">{{ previewInfo.ext.toUpperCase() }}</span>
            <h3>{{ previewInfo.name }}</h3>
          </div>
          <button class="close-icon-btn" @click="previewInfo = null">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div class="modal-content">
          <pre v-if="!previewInfo.is_binary" class="code-view">{{ previewInfo.content }}</pre>
          <div v-else class="binary-doc-view">
            <p>该文件为二进制文档 ({{ previewInfo.size }})，已成功持久化至 raw/origin，可直接下载在本地软件中查看。</p>
            <button class="btn btn-secondary btn-sm" @click="triggerDownloadByName(previewInfo.name)">下载源文件</button>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="previewInfo = null">关闭</button>
        </div>
      </div>
    </div>

    <!-- 操作提示 Toast -->
    <transition name="toast">
      <div v-if="toastMessage" class="toast-card">
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  fetchFiles,
  uploadFiles,
  deleteFile,
  fetchPreview,
  getDownloadUrl,
  FileItem,
  PreviewData,
} from '@/api/files'

const showUploadModal = ref(false)
const previewInfo = ref<PreviewData | null>(null)
const isDragging = ref(false)
const searchQuery = ref('')
const currentFilter = ref('all')
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadList = ref<File[]>([])
const toastMessage = ref('')
const loading = ref(false)
const uploading = ref(false)

const filterTabs = [
  { key: 'all', name: '全部' },
  { key: 'doc', name: 'Office 文档' },
  { key: 'md', name: 'Markdown' },
  { key: 'txt', name: '纯文本' },
]

const files = ref<FileItem[]>([])

async function loadFiles() {
  loading.value = true
  try {
    files.value = await fetchFiles()
  } catch (err: any) {
    showToast(err.message || '加载文件列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFiles()
})

const filteredFiles = computed(() => {
  return files.value.filter((file) => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.value.trim().toLowerCase())
    if (!matchesSearch) return false

    const ext = file.ext.toLowerCase()
    if (currentFilter.value === 'doc') {
      return ['docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'pdf'].includes(ext)
    } else if (currentFilter.value === 'md') {
      return ext === 'md'
    } else if (currentFilter.value === 'txt') {
      return ext === 'txt'
    }
    return true
  })
})

function getFilterCount(key: string): number {
  if (key === 'all') return files.value.length
  if (key === 'doc') return files.value.filter((f) => ['docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'pdf'].includes(f.ext.toLowerCase())).length
  if (key === 'md') return files.value.filter((f) => f.ext.toLowerCase() === 'md').length
  if (key === 'txt') return files.value.filter((f) => f.ext.toLowerCase() === 'txt').length
  return 0
}

function showToast(msg: string) {
  toastMessage.value = msg
  setTimeout(() => {
    toastMessage.value = ''
  }, 2200)
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files) {
    uploadList.value.push(...Array.from(target.files))
  }
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  if (e.dataTransfer?.files) {
    uploadList.value.push(...Array.from(e.dataTransfer.files))
  }
}

async function confirmUpload() {
  if (uploadList.value.length === 0 || uploading.value) return
  uploading.value = true
  try {
    const res = await uploadFiles(uploadList.value)
    showToast(`成功上传 ${res.length} 个文件至 raw/origin`)
    uploadList.value = []
    showUploadModal.value = false
    await loadFiles()
  } catch (err: any) {
    showToast(err.message || '上传文件失败')
  } finally {
    uploading.value = false
  }
}

async function handlePreview(file: FileItem) {
  try {
    previewInfo.value = await fetchPreview(file.name)
  } catch (err: any) {
    showToast(err.message || '获取预览失败')
  }
}

function handleDownload(file: FileItem) {
  triggerDownloadByName(file.name)
}

function triggerDownloadByName(filename: string) {
  const url = getDownloadUrl(filename)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  showToast(`已开始下载: ${filename}`)
}

async function handleDelete(file: FileItem) {
  if (confirm(`确定要从 raw/origin 目录中永久删除 "${file.name}" 吗？`)) {
    try {
      await deleteFile(file.name)
      showToast(`已成功删除: ${file.name}`)
      await loadFiles()
    } catch (err: any) {
      showToast(err.message || '删除失败')
    }
  }
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i]
}
</script>

<style scoped>
.file-viewport {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-app);
}

.file-topbar {
  height: 54px;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.path-breadcrumbs {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  background-color: var(--bg-subtle);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
}

.crumb.active {
  color: var(--primary);
  font-weight: 600;
}

.crumb-sep {
  color: var(--text-faint);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-content {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 16px;
}

.search-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  width: 260px;
}

.search-svg {
  position: absolute;
  left: 10px;
  color: var(--text-muted);
}

.search-input-wrap input {
  width: 100%;
  padding: 7px 30px 7px 32px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  font-size: 12px;
  outline: none;
  transition: all 0.15s ease;
}

.search-input-wrap input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary);
}

.clear-search {
  position: absolute;
  right: 8px;
  color: var(--text-faint);
}

.type-segmented {
  display: flex;
  background-color: var(--bg-subtle);
  padding: 2px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
}

.seg-btn {
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 6px;
}

.seg-btn:hover {
  color: var(--text-primary);
}

.seg-btn.active {
  background-color: var(--bg-surface);
  color: var(--text-primary);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.count-pill {
  font-size: 10px;
  background-color: var(--bg-muted);
  padding: 1px 5px;
  border-radius: 9999px;
  color: var(--text-secondary);
}

.table-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;
}

.data-table th {
  background-color: var(--bg-subtle);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-default);
}

.table-row td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-secondary);
}

.table-row:hover {
  background-color: var(--bg-subtle);
}

.td-name {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-primary);
  font-weight: 500;
}

.file-icon-box {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  flex-shrink: 0;
}

.file-title {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-ext {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-default);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.td-size,
.td-date {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
}

.chip-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-chip.indexed {
  color: var(--success);
}
.status-chip.indexed .chip-dot {
  background-color: var(--success);
}

.action-group {
  display: flex;
  gap: 4px;
}

.icon-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
}

.icon-btn:hover {
  background-color: var(--bg-muted);
  color: var(--text-primary);
}

.icon-btn.danger-hover:hover {
  background-color: var(--danger-subtle);
  color: var(--danger);
}

.empty-state-cell {
  padding: 48px;
  text-align: center;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text-faint);
  font-size: 13px;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(1px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  width: 500px;
  max-width: 90vw;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.modal-large {
  width: 700px;
}

.modal-titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-default);
}

.modal-titlebar h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-icon-btn {
  color: var(--text-muted);
  padding: 4px;
}

.close-icon-btn:hover {
  color: var(--text-primary);
}

.modal-content {
  padding: 18px;
}

.drag-drop-panel {
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-md);
  padding: 36px 16px;
  text-align: center;
  cursor: pointer;
  background-color: var(--bg-app);
  transition: all 0.15s ease;
}

.drag-drop-panel:hover,
.drag-drop-panel.active {
  border-color: var(--primary);
  background-color: var(--primary-subtle);
}

.upload-icon-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.drag-text {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.drag-types {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.queue-box {
  margin-top: 14px;
}

.queue-heading {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.queue-list {
  max-height: 140px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.queue-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background-color: var(--bg-subtle);
  border-radius: var(--radius-sm);
  font-size: 12px;
}

.queue-name {
  color: var(--text-primary);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.queue-size {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 11px;
}

.queue-del {
  color: var(--danger);
  padding: 2px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 18px;
  background-color: var(--bg-subtle);
  border-top: 1px solid var(--border-default);
}

.code-view {
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 14px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  max-height: 380px;
  overflow-y: auto;
  white-space: pre-wrap;
}

.binary-doc-view {
  text-align: center;
  padding: 32px 16px;
  font-size: 13px;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.preview-title-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn {
  padding: 7px 14px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background-color: var(--primary);
  color: var(--primary-text);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-hover);
}

.btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
}

.btn-secondary:hover {
  background-color: var(--bg-subtle);
  color: var(--text-primary);
}

.btn-sm {
  padding: 5px 10px;
  font-size: 11px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.toast-card {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background-color: var(--primary);
  color: var(--primary-text);
  padding: 9px 16px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 200;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
