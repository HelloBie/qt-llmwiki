<template>
  <div class="docs-container">
    <!-- 顶部文档快速切换导航条 -->
    <div class="docs-selector-bar">
      <div class="selector-heading">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </svg>
        <span>系统工程设计文档</span>
      </div>

      <div class="docs-pills">
        <button
          v-for="doc in docsList"
          :key="doc.id"
          :class="['doc-pill', { active: currentDocId === doc.id }]"
          @click="selectDoc(doc.id)"
          :title="doc.description"
        >
          <span class="pill-badge" :data-badge="doc.badge">{{ doc.badge }}</span>
          <span class="pill-title">{{ doc.title }}</span>
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="gh-loading-body">
      <div class="spinner"></div>
      <p>正在读取设计文档...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="gh-error-body">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <p>{{ error }}</p>
      <button class="btn btn-secondary btn-sm" @click="loadCurrentDoc">重试</button>
    </div>

    <!-- GitHub 风格 Markdown 渲染查看器 -->
    <MarkdownViewer
      v-else-if="activeDoc"
      :content="activeDoc.content"
      :filename="activeDoc.filename"
      breadcrumb-dir="qt-llmwiki / docs"
      :doc-id="activeDoc.badge"
      :line-count="activeDoc.line_count"
      :size-text="formatFileSize(activeDoc.size_bytes)"
      :updated-at="activeDoc.updated_at"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  fetchDesignDocs,
  fetchDesignDocDetail,
  DesignDocMeta,
  DesignDocDetail,
} from '@/api/settings'
import MarkdownViewer from '@/components/MarkdownViewer.vue'

const docsList = ref<DesignDocMeta[]>([])
const currentDocId = ref('01_hld')
const activeDoc = ref<DesignDocDetail | null>(null)
const loading = ref(false)
const error = ref('')

async function loadDocsList() {
  try {
    const list = await fetchDesignDocs()
    docsList.value = list
    if (list.length > 0 && !docsList.value.some((d) => d.id === currentDocId.value)) {
      currentDocId.value = list[0].id
    }
    await loadCurrentDoc()
  } catch (err: any) {
    error.value = `加载文档列表失败: ${err.message}`
  }
}

async function loadCurrentDoc() {
  if (!currentDocId.value) return
  loading.value = true
  error.value = ''
  try {
    const doc = await fetchDesignDocDetail(currentDocId.value)
    activeDoc.value = doc
  } catch (err: any) {
    error.value = `加载文档内容失败: ${err.message}`
  } finally {
    loading.value = false
  }
}

function selectDoc(id: string) {
  if (currentDocId.value === id) return
  currentDocId.value = id
  loadCurrentDoc()
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

onMounted(() => {
  loadDocsList()
})
</script>

<style scoped>
.docs-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

/* 顶部文档快速切换导航条 */
.docs-selector-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 8px 14px;
  box-shadow: var(--shadow-sm);
}

.selector-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.docs-pills {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.doc-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.doc-pill:hover {
  background-color: var(--bg-surface);
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.doc-pill.active {
  background-color: var(--primary);
  border-color: var(--primary);
  color: var(--primary-text);
  font-weight: 500;
}

.pill-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 3px;
  background-color: rgba(0, 0, 0, 0.08);
}

.doc-pill.active .pill-badge {
  background-color: rgba(255, 255, 255, 0.25);
  color: #ffffff;
}

/* 状态体 */
.gh-loading-body,
.gh-error-body {
  padding: 60px 20px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-muted);
  font-size: 13px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-default);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
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
</style>
