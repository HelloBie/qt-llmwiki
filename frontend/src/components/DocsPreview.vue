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

    <!-- 主视口：仿 GitHub README 样式卡片 -->
    <div class="github-readme-box" ref="readmeBoxRef">
      <!-- GitHub 风格文件头信息栏 (File Header) -->
      <div class="gh-header">
        <div class="gh-header-left">
          <!-- GitHub 经典文件图标 -->
          <svg class="gh-file-icon" viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
            <path d="M2 1.75C2 .784 2.784 0 3.75 0h6.586c.464 0 .909.184 1.237.513l3.914 3.914c.329.328.513.773.513 1.237v8.586A1.75 1.75 0 0 1 14.25 16h-10.5A1.75 1.75 0 0 1 2 14.25Zm1.75-.25a.25.25 0 0 0-.25.25v12.5c0 .138.112.25.25.25h10.5a.25.25 0 0 0 .25-.25V6h-2.75A1.75 1.75 0 0 1 10 4.25V1.5Zm7.75 0v2.75c0 .138.112.25.25.25h2.75Z" />
          </svg>

          <!-- 路径面包屑 -->
          <div class="gh-breadcrumbs">
            <span class="crumb-dir">qt-llmwiki</span>
            <span class="crumb-slash">/</span>
            <span class="crumb-dir">docs</span>
            <span class="crumb-slash">/</span>
            <span class="crumb-file">{{ activeDoc?.filename || 'README.md' }}</span>
          </div>

          <!-- 元数据指标 -->
          <div class="gh-file-meta" v-if="activeDoc">
            <span class="meta-item">{{ activeDoc.line_count }} lines</span>
            <span class="meta-dot">·</span>
            <span class="meta-item">{{ formatFileSize(activeDoc.size_bytes) }}</span>
            <span class="meta-dot">·</span>
            <span class="meta-item">Updated: {{ activeDoc.updated_at }}</span>
          </div>
        </div>

        <div class="gh-header-right">
          <!-- 大纲目录开关按钮 (Outline) -->
          <button
            class="gh-tool-btn"
            :class="{ active: showToc }"
            @click="showToc = !showToc"
            title="查看章节大纲"
            v-if="viewMode === 'preview' && tocItems.length > 0"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
              <path d="M2 3.75C2 3.336 2.336 3 2.75 3h10.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 3.75Zm0 4.25c0-.414.336-.75.75-.75h10.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 8Zm0 4.25c0-.414.336-.75.75-.75h10.5a.75.75 0 0 1 0 1.5H2.75a.75.75 0 0 1-.75-.75Z" />
            </svg>
            <span>Outline</span>
            <span class="gh-badge-count">{{ tocItems.length }}</span>
          </button>

          <!-- 模式切换：Preview / Code -->
          <div class="gh-view-toggle">
            <button
              class="toggle-btn"
              :class="{ active: viewMode === 'preview' }"
              @click="viewMode = 'preview'"
              title="预览渲染视图"
            >
              <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 2a6 6 0 1 0 0 12A6 6 0 0 0 8 2ZM0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8Z" />
                <path d="M8 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z" />
              </svg>
              <span>Preview</span>
            </button>
            <button
              class="toggle-btn"
              :class="{ active: viewMode === 'raw' }"
              @click="viewMode = 'raw'"
              title="查看原始 Markdown 源码"
            >
              <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor">
                <path d="m11.28 3.22 4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.749.749 0 0 1-1.275-.326.749.749 0 0 1 .215-.734L14.19 8l-3.97-3.97a.749.749 0 0 1 .215-.734.749.749 0 0 1 1.06 0Zm-6.56 0a.75.75 0 0 1 0 1.06L.75 8.25l3.97 3.97a.751.751 0 0 1-.018 1.042.751.751 0 0 1-1.042.018l-4.25-4.25a.75.75 0 0 1 0-1.06l4.25-4.25a.75.75 0 0 1 1.06 0Z" />
              </svg>
              <span>Raw</span>
            </button>
          </div>

          <!-- 一键复制源码按钮 -->
          <button class="gh-tool-btn" @click="copyRawContent" :title="copied ? '已复制！' : '复制 Markdown 原始文本'">
            <svg v-if="!copied" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>{{ copied ? 'Copied!' : 'Copy raw' }}</span>
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

      <!-- 文档主体容器 -->
      <div v-else class="gh-body-layout">
        <!-- 左侧大纲导航抽屉 (GitHub Outline Drawer) -->
        <aside v-if="showToc && viewMode === 'preview' && tocItems.length > 0" class="gh-toc-panel">
          <div class="toc-header">
            <span>TABLE OF CONTENTS</span>
            <button class="toc-close-btn" @click="showToc = false" title="关闭大纲">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <ul class="toc-list">
            <li
              v-for="item in tocItems"
              :key="item.id"
              :class="['toc-item', `toc-level-${item.level}`]"
            >
              <a :href="`#${item.id}`" @click.prevent="scrollToHeading(item.id)">
                {{ item.text }}
              </a>
            </li>
          </ul>
        </aside>

        <!-- Markdown 渲染区 / 源码显示区 -->
        <main class="gh-content-viewport" ref="contentViewportRef">
          <!-- 预览模式: GitHub .markdown-body -->
          <article
            v-if="viewMode === 'preview'"
            class="markdown-body"
            v-html="parsedHtml"
            @click="handleBodyClick"
          ></article>

          <!-- Raw 源码模式: 带行号的 GitHub 原始代码视图 -->
          <div v-else class="gh-raw-viewer">
            <div class="raw-lines-col">
              <span v-for="n in rawLineCount" :key="n" class="raw-line-num">{{ n }}</span>
            </div>
            <pre class="raw-code-col"><code>{{ rawContent }}</code></pre>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  fetchDesignDocs,
  fetchDesignDocDetail,
  DesignDocMeta,
  DesignDocDetail,
} from '@/api/settings'
import { parseMarkdown, TocItem } from '@/utils/markdown'

const docsList = ref<DesignDocMeta[]>([])
const currentDocId = ref('01_hld')
const activeDoc = ref<DesignDocDetail | null>(null)
const loading = ref(false)
const error = ref('')
const viewMode = ref<'preview' | 'raw'>('preview')
const showToc = ref(false)
const copied = ref(false)

const readmeBoxRef = ref<HTMLElement | null>(null)
const contentViewportRef = ref<HTMLElement | null>(null)

// 转换缓存
const parsedResult = computed(() => {
  if (!activeDoc.value?.content) return { html: '', toc: [] }
  return parseMarkdown(activeDoc.value.content)
})

const parsedHtml = computed(() => parsedResult.value.html)
const tocItems = computed<TocItem[]>(() => parsedResult.value.toc)
const rawContent = computed(() => activeDoc.value?.content || '')
const rawLineCount = computed(() => {
  if (!rawContent.value) return 0
  return rawContent.value.split('\n').length
})

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

async function copyRawContent() {
  if (!rawContent.value) return
  try {
    await navigator.clipboard.writeText(rawContent.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy raw text', err)
  }
}

function scrollToHeading(id: string) {
  const el = contentViewportRef.value?.querySelector(`#${id}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function handleBodyClick(e: MouseEvent) {
  const target = (e.target as HTMLElement).closest('.btn-copy-code') as HTMLElement | null
  if (target) {
    const code = decodeURIComponent(target.getAttribute('data-code') || '')
    navigator.clipboard.writeText(code).then(() => {
      const label = target.querySelector('span')
      if (label) {
        const orig = label.textContent
        label.textContent = 'Copied!'
        setTimeout(() => {
          label.textContent = orig
        }, 2000)
      }
    })
  }
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

/* GitHub 风格 README 卡片外盒 */
.github-readme-box {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* GitHub 文件头信息栏 */
.gh-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background-color: var(--bg-subtle);
  border-bottom: 1px solid var(--border-default);
  user-select: none;
}

.gh-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.gh-file-icon {
  color: var(--text-muted);
  flex-shrink: 0;
}

.gh-breadcrumbs {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-family: var(--font-mono);
}

.crumb-dir {
  color: var(--accent);
  font-weight: 500;
}

.crumb-slash {
  color: var(--text-faint);
}

.crumb-file {
  color: var(--text-primary);
  font-weight: 600;
}

.gh-file-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
  margin-left: 8px;
}

.meta-dot {
  color: var(--text-faint);
}

.gh-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.gh-view-toggle {
  display: inline-flex;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 2px;
}

.toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-muted);
  border-radius: 4px;
}

.toggle-btn:hover {
  color: var(--text-primary);
}

.toggle-btn.active {
  background-color: var(--primary);
  color: var(--primary-text);
}

.gh-tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 9px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
}

.gh-tool-btn:hover {
  background-color: var(--bg-subtle);
  color: var(--text-primary);
}

.gh-tool-btn.active {
  background-color: var(--primary-subtle);
  border-color: var(--primary);
  color: var(--primary);
}

.gh-badge-count {
  font-size: 10px;
  background-color: var(--bg-subtle);
  padding: 1px 5px;
  border-radius: 10px;
  color: var(--text-muted);
}

/* 状态体 */
.gh-loading-body,
.gh-error-body {
  padding: 60px 20px;
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

/* 文档主体分栏布局 */
.gh-body-layout {
  display: flex;
  position: relative;
  min-height: 500px;
}

/* 大纲目录抽屉 */
.gh-toc-panel {
  width: 250px;
  flex-shrink: 0;
  background-color: var(--bg-surface);
  border-right: 1px solid var(--border-default);
  padding: 16px;
  max-height: 80vh;
  overflow-y: auto;
}

.toc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-light);
}

.toc-close-btn {
  color: var(--text-muted);
  padding: 2px;
}

.toc-close-btn:hover {
  color: var(--text-primary);
}

.toc-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.toc-item a {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 3px 6px;
  border-radius: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toc-item a:hover {
  background-color: var(--bg-subtle);
  color: var(--primary);
}

.toc-level-1 a { font-weight: 600; }
.toc-level-2 a { padding-left: 14px; }
.toc-level-3 a { padding-left: 22px; font-size: 11px; color: var(--text-muted); }
.toc-level-4 a { padding-left: 30px; font-size: 11px; color: var(--text-faint); }

/* 内容视口 */
.gh-content-viewport {
  flex: 1;
  padding: 32px 40px;
  overflow-x: auto;
  background-color: var(--bg-surface);
}

/* Raw 源码视图 */
.gh-raw-viewer {
  display: flex;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  background-color: var(--bg-app);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  overflow-x: auto;
}

.raw-lines-col {
  padding: 12px 10px;
  text-align: right;
  color: var(--text-faint);
  background-color: var(--bg-subtle);
  border-right: 1px solid var(--border-default);
  user-select: none;
  display: flex;
  flex-direction: column;
}

.raw-code-col {
  padding: 12px 16px;
  margin: 0;
  color: var(--text-primary);
  overflow-x: auto;
  flex: 1;
}

/* ==========================================================================
   GitHub Markdown 正文官方视觉规范 (.markdown-body)
   ========================================================================== */
:deep(.markdown-body) {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  word-wrap: break-word;
}

:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3),
:deep(.markdown-body h4),
:deep(.markdown-body h5),
:deep(.markdown-body h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  color: var(--text-primary);
}

:deep(.markdown-body h1) {
  font-size: 1.8em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--border-default);
}

:deep(.markdown-body h2) {
  font-size: 1.4em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--border-default);
}

:deep(.markdown-body h3) {
  font-size: 1.2em;
}

:deep(.markdown-body h4) {
  font-size: 1em;
}

:deep(.markdown-body p) {
  margin-top: 0;
  margin-bottom: 16px;
}

:deep(.markdown-body hr) {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: var(--border-default);
  border: 0;
}

:deep(.markdown-body blockquote) {
  padding: 0 1em;
  color: var(--text-muted);
  border-left: 0.25em solid var(--border-strong);
  margin: 0 0 16px 0;
}

:deep(.markdown-body ul),
:deep(.markdown-body ol) {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
}

:deep(.markdown-body li) {
  margin-top: 0.25em;
}

:deep(.markdown-body .task-list-item) {
  list-style-type: none;
  margin-left: -1.5em;
}

:deep(.markdown-body .task-list-item-checkbox) {
  margin-right: 0.5em;
  vertical-align: middle;
}

/* GitHub 表格样式规范 */
:deep(.markdown-body table) {
  display: block;
  width: 100%;
  max-width: 100%;
  overflow: auto;
  margin-top: 0;
  margin-bottom: 16px;
  border-spacing: 0;
  border-collapse: collapse;
}

:deep(.markdown-body table th),
:deep(.markdown-body table td) {
  padding: 6px 13px;
  border: 1px solid var(--border-default);
  font-size: 13px;
}

:deep(.markdown-body table th) {
  font-weight: 600;
  background-color: var(--bg-subtle);
}

:deep(.markdown-body table tr:nth-child(2n)) {
  background-color: #fcfdfe;
}

/* 行内代码 */
:deep(.markdown-body .inline-code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  white-space: break-spaces;
  background-color: rgba(175, 184, 193, 0.2);
  border-radius: 4px;
  font-family: var(--font-mono);
}

/* 独立代码块 (带仿 GitHub 头部栏与复制按钮) */
:deep(.markdown-body .code-block-wrapper) {
  margin-bottom: 16px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  overflow: hidden;
  background-color: #f6f8fa;
}

:deep(.markdown-body .code-block-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background-color: #ebeef2;
  border-bottom: 1px solid var(--border-default);
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

:deep(.markdown-body .btn-copy-code) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  font-size: 11px;
  color: var(--text-secondary);
  background-color: #ffffff;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  cursor: pointer;
}

:deep(.markdown-body .btn-copy-code:hover) {
  background-color: #f3f4f6;
  color: var(--text-primary);
}

:deep(.markdown-body .code-content) {
  padding: 14px 16px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.45;
  background-color: #f6f8fa;
  margin: 0;
  font-family: var(--font-mono);
}

/* 锚点图标 */
:deep(.markdown-body .heading-anchor) {
  position: relative;
}

:deep(.markdown-body .heading-anchor .anchor) {
  float: left;
  padding-right: 4px;
  margin-left: -20px;
  line-height: 1;
  color: var(--text-muted);
  visibility: hidden;
  text-decoration: none;
}

:deep(.markdown-body .heading-anchor:hover .anchor) {
  visibility: visible;
}

/* 链接样式 */
:deep(.markdown-body .md-link) {
  color: var(--accent);
  text-decoration: none;
}

:deep(.markdown-body .md-link:hover) {
  text-decoration: underline;
}

/* GitHub Alert 样式规范 (Note / Tip / Important / Warning / Caution) */
:deep(.markdown-body .markdown-alert) {
  padding: 8px 16px;
  margin-bottom: 16px;
  color: inherit;
  border-left: 0.25em solid;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

:deep(.markdown-body .markdown-alert-title) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 4px;
  font-size: 13px;
}

:deep(.markdown-body .markdown-alert-content) {
  font-size: 13px;
}

:deep(.markdown-body .markdown-alert-content p) {
  margin-bottom: 4px;
}

/* NOTE (Blue) */
:deep(.markdown-body .markdown-alert-note) {
  border-left-color: #0969da;
  background-color: rgba(9, 105, 218, 0.04);
}
:deep(.markdown-body .markdown-alert-note .markdown-alert-title) {
  color: #0969da;
}

/* TIP (Green) */
:deep(.markdown-body .markdown-alert-tip) {
  border-left-color: #1a7f37;
  background-color: rgba(26, 127, 55, 0.04);
}
:deep(.markdown-body .markdown-alert-tip .markdown-alert-title) {
  color: #1a7f37;
}

/* IMPORTANT (Purple) */
:deep(.markdown-body .markdown-alert-important) {
  border-left-color: #8250df;
  background-color: rgba(130, 80, 223, 0.04);
}
:deep(.markdown-body .markdown-alert-important .markdown-alert-title) {
  color: #8250df;
}

/* WARNING (Amber) */
:deep(.markdown-body .markdown-alert-warning) {
  border-left-color: #9a6700;
  background-color: rgba(154, 103, 0, 0.04);
}
:deep(.markdown-body .markdown-alert-warning .markdown-alert-title) {
  color: #9a6700;
}

/* CAUTION (Red) */
:deep(.markdown-body .markdown-alert-caution) {
  border-left-color: #cf222e;
  background-color: rgba(207, 34, 46, 0.04);
}
:deep(.markdown-body .markdown-alert-caution .markdown-alert-title) {
  color: #cf222e;
}
</style>
