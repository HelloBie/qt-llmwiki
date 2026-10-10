/**
 * 高保真 GitHub 风格 Markdown 渲染与大纲提取器
 * 支持折叠式 YAML Frontmatter 头部美化、文档属性卡片与图标对应
 */

export interface TocItem {
  id: string
  text: string
  level: number
}

export interface MarkdownParseResult {
  html: string
  toc: TocItem[]
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function slugify(text: string, existingSlugs: Set<string>): string {
  let base = text
    .toLowerCase()
    .replace(/<[^>]+>/g, '') // 去除 HTML 标签
    .replace(/[^\w\u4e00-\u9fa5\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')

  if (!base) base = 'section'

  let slug = base
  let counter = 1
  while (existingSlugs.has(slug)) {
    slug = `${base}-${counter}`
    counter++
  }
  existingSlugs.add(slug)
  return slug
}

/**
 * 转换单行行内元素：加粗、斜体、删除线、行内代码、链接、图片
 */
function parseInline(text: string): string {
  let out = escapeHtml(text)

  // 1. 行内代码 `code`
  out = out.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')

  // 2. 图片 ![alt](url)
  out = out.replace(/!\[(.*?)\]\((.*?)\)/g, '<img src="$2" alt="$1" class="md-img" />')

  // 3. 链接 [text](url)
  out = out.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="md-link">$1</a>')

  // 4. 加粗与斜体 ***bold italic***
  out = out.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>')

  // 5. 加粗 **bold**
  out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // 6. 斜体 *italic*
  out = out.replace(/\*(.*?)\*/g, '<em>$1</em>')

  // 7. 删除线 ~~del~~
  out = out.replace(/~~(.*?)~~/g, '<del>$1</del>')

  return out
}

/**
 * GitHub Alert 提示框图标映射 (纯 SVG 矢量图标)
 */
const ALERT_ICONS: Record<string, string> = {
  NOTE: `<svg class="octicon" viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8Zm8-6.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM6.5 7.75A.75.75 0 0 1 7.25 7h1a.75.75 0 0 1 .75.75v2.75h.25a.75.75 0 0 1 0 1.5h-2.5a.75.75 0 0 1 0-1.5h.25v-2h-.25a.75.75 0 0 1-.75-.75ZM8 6a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z"></path></svg>`,
  TIP: `<svg class="octicon" viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M8 1.5c-2.363 0-4 1.69-4 3.75 0 .984.424 1.625.984 2.304l.214.253c.223.264.47.556.673.91.24.417.379.882.379 1.533v.25h3.5v-.25c0-.651.139-1.116.379-1.533.203-.354.45-.646.673-.91l.214-.253c.56-.679.984-1.32.984-2.304 0-2.06-1.637-3.75-4-3.75ZM5.75 12h4.5a.75.75 0 0 1 0 1.5h-4.5a.75.75 0 0 1 0-1.5Zm.75 2.5h3a.75.75 0 0 1 0 1.5h-3a.75.75 0 0 1 0-1.5Z"></path></svg>`,
  IMPORTANT: `<svg class="octicon" viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M0 1.75C0 .784.784 0 1.75 0h12.5C15.216 0 16 .784 16 1.75v12.5A1.75 1.75 0 0 1 14.25 16H1.75A1.75 1.75 0 0 1 0 14.25ZM1.75 1.5a.25.25 0 0 0-.25.25v12.5c0 .138.112.25.25.25h12.5a.25.25 0 0 0 .25-.25V1.75a.25.25 0 0 0-.25-.25ZM7.25 4a.75.75 0 0 1 1.5 0v5a.75.75 0 0 1-1.5 0ZM8 12a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z"></path></svg>`,
  WARNING: `<svg class="octicon" viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M6.457 1.047c.659-1.234 2.427-1.234 3.086 0l6.082 11.378A1.75 1.75 0 0 1 14.082 15H1.918a1.75 1.75 0 0 1-1.543-2.575Zm1.763.707a.25.25 0 0 0-.44 0L1.698 13.132a.25.25 0 0 0 .22.368h12.164a.25.25 0 0 0 .22-.368Zm.53 3.996v2.5a.75.75 0 0 1-1.5 0v-2.5a.75.75 0 0 1 1.5 0ZM9 11a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"></path></svg>`,
  CAUTION: `<svg class="octicon" viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M4.47.04c.37-.04.74-.04 1.11 0l6.95 1.48c.34.07.65.24.89.48l2.1 2.1c.24.24.41.55.48.89l1.48 6.95c.04.37.04.74 0 1.11l-1.48 6.95a2.25 2.25 0 0 1-.48.89l-2.1 2.1a2.25 2.25 0 0 1-.89.48l-6.95 1.48a2.6 2.6 0 0 1-1.11 0l-6.95-1.48a2.25 2.25 0 0 1-.89-.48l-2.1-2.1a2.25 2.25 0 0 1-.48-.89l-1.48-6.95a2.6 2.6 0 0 1 0-1.11l1.48-6.95c.07-.34.24-.65.48-.89l2.1-2.1c.24-.24.55-.41.89-.48ZM8 4a.75.75 0 0 0-.75.75v3.5a.75.75 0 0 0 1.5 0v-3.5A.75.75 0 0 0 8 4Zm0 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z"></path></svg>`,
}

/**
 * 元数据各字段对应的 SVG 矢量图标库
 */
const FIELD_ICONS: Record<string, string> = {
  // 书签图标（针对标签 tags、category）
  bookmark: `<svg class="fm-icon-svg fm-bookmark-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>`,
  // 文档编号 ID 图标
  id: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg>`,
  // 标题 / 文档图标
  title: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
  // 原始素材 / 文件夹
  source: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`,
  // 全文目标文件
  target: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>`,
  // 文件格式 / 类型
  type: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
  // 文件大小
  size: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`,
  // 字符统计
  count: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><line x1="21" y1="6" x2="3" y2="6"/><line x1="15" y1="12" x2="3" y2="12"/><line x1="17" y1="18" x2="3" y2="18"/></svg>`,
  // 转换信息 / 引擎
  converter: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  // 日期 / 时间
  time: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
  // 作者 / 维护者 / 架构师
  author: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
  // 版本 / Revision
  version: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>`,
  // 状态 / 校验
  status: `<svg class="fm-icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
}

interface FrontmatterEntry {
  key: string
  label: string
  rawVal: any
  icon: string
  isTag?: boolean
  isId?: boolean
  isCode?: boolean
}

/**
 * 解析 YAML Frontmatter 内容为键值字典与列表
 */
function parseYaml(lines: string[]): Record<string, any> {
  const data: Record<string, any> = {}
  let currentKey = ''
  let currentList: string[] = []

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue

    // 列表项格式：- item
    if (trimmed.startsWith('- ') && currentKey) {
      const itemVal = trimmed.slice(2).trim().replace(/^["']|["']$/g, '')
      currentList.push(itemVal)
      data[currentKey] = currentList
      continue
    }

    // 键值格式：key: value
    const match = trimmed.match(/^([\w-]+)\s*:\s*(.*)$/)
    if (match) {
      currentKey = match[1]
      let val = match[2].trim()

      if (!val) {
        currentList = []
        data[currentKey] = currentList
      } else if (val.startsWith('[') && val.endsWith(']')) {
        // 内联数组 [a, b, c]
        const items = val
          .slice(1, -1)
          .split(',')
          .map((s) => s.trim().replace(/^["']|["']$/g, ''))
          .filter(Boolean)
        data[currentKey] = items
        currentList = items
      } else {
        val = val.replace(/^["']|["']$/g, '')
        data[currentKey] = val
        currentList = []
      }
    }
  }

  return data
}

/**
 * 智能为文档提取或生成标签列表
 */
function extractDocTags(data: Record<string, any>): string[] {
  let tags: string[] = []

  if (data.tags) {
    if (Array.isArray(data.tags)) tags = [...data.tags]
    else if (typeof data.tags === 'string') {
      tags = data.tags.split(/[,，、 ]/).map((s) => s.trim()).filter(Boolean)
    }
  } else if (data.tag) {
    tags = [String(data.tag)]
  } else if (data.category) {
    tags = [String(data.category)]
  }

  // 若无标签，智能从类型和标题提取
  if (tags.length === 0) {
    if (data.file_type) tags.push(String(data.file_type).toUpperCase())
    const title = String(data.title || '')
    const candidates = ['岗位说明', '总体设计', '测控', '飞行控制', '明细', '架构', '数据库', '接口规范', '设计文档']
    for (const c of candidates) {
      if (title.includes(c)) tags.push(c)
    }
  }

  return Array.from(new Set(tags))
}

/**
 * 构造折叠式 Frontmatter 美化卡片 HTML
 */
function renderFrontmatterCard(data: Record<string, any>): string {
  const tags = extractDocTags(data)
  const docId = data.doc_id || data.file_number || null
  const fileType = data.file_type ? String(data.file_type).toUpperCase() : ''
  const fileSize = data.file_size || ''
  const charCount = data.char_count ? `${data.char_count} 字符` : ''

  // 摘要栏胶囊
  const summaryPills: string[] = []
  if (docId) {
    summaryPills.push(`<span class="fm-summary-badge fm-badge-id">ID: ${escapeHtml(String(docId))}</span>`)
  }
  if (fileType) {
    summaryPills.push(`<span class="fm-summary-badge">${escapeHtml(fileType)}</span>`)
  }
  if (fileSize) {
    summaryPills.push(`<span class="fm-summary-badge">${escapeHtml(String(fileSize))}</span>`)
  }
  if (charCount) {
    summaryPills.push(`<span class="fm-summary-badge">${escapeHtml(charCount)}</span>`)
  }
  if (tags.length > 0) {
    summaryPills.push(
      `<span class="fm-summary-badge fm-badge-tag">${FIELD_ICONS.bookmark}${tags.length} 标签</span>`
    )
  }

  // 组织网格项
  const items: FrontmatterEntry[] = []

  // 1. 文档编号
  if (docId) {
    items.push({
      key: 'doc_id',
      label: '文件编号',
      rawVal: docId,
      icon: FIELD_ICONS.id,
      isId: true,
    })
  }

  // 2. 文档标题
  if (data.title) {
    items.push({
      key: 'title',
      label: '文档标题',
      rawVal: data.title,
      icon: FIELD_ICONS.title,
    })
  }

  // 3. 文档标签 (带书签图标)
  if (tags.length > 0) {
    items.push({
      key: 'tags',
      label: '文档标签',
      rawVal: tags,
      icon: FIELD_ICONS.bookmark,
      isTag: true,
    })
  }

  // 4. 原始文件 / 路径
  if (data.source_file || data.source_path) {
    items.push({
      key: 'source_path',
      label: '原始素材',
      rawVal: data.source_path || data.source_file,
      icon: FIELD_ICONS.source,
      isCode: true,
    })
  }

  // 5. 目标 Markdown 路径
  if (data.target_file || data.target_path) {
    items.push({
      key: 'target_path',
      label: '全文目标',
      rawVal: data.target_path || data.target_file,
      icon: FIELD_ICONS.target,
      isCode: true,
    })
  }

  // 6. 格式类型
  if (fileType) {
    items.push({
      key: 'file_type',
      label: '文件格式',
      rawVal: fileType,
      icon: FIELD_ICONS.type,
    })
  }

  // 7. 文件大小
  if (fileSize) {
    items.push({
      key: 'file_size',
      label: '文件大小',
      rawVal: fileSize,
      icon: FIELD_ICONS.size,
    })
  }

  // 8. 字符统计
  if (charCount) {
    items.push({
      key: 'char_count',
      label: '字符统计',
      rawVal: charCount,
      icon: FIELD_ICONS.count,
    })
  }

  // 9. 转换时间与引擎
  if (data.converted_at || data.converter) {
    const convStr = [data.converter ? `引擎: ${data.converter}` : '', data.converted_at]
      .filter(Boolean)
      .join(' · ')
    items.push({
      key: 'converted_at',
      label: '转换信息',
      rawVal: convStr,
      icon: FIELD_ICONS.converter,
    })
  }

  // 10. 创建与修改时间
  const timeStr = data.modified_at || data.created_at || data.modified || data.created
  if (timeStr) {
    items.push({
      key: 'time',
      label: '时间记录',
      rawVal: timeStr,
      icon: FIELD_ICONS.time,
    })
  }

  // 11. 作者与维护者
  const authorStr = data.author || data.creator || data.lastModifiedBy || data['架构师']
  if (authorStr && authorStr !== 'Un-named') {
    items.push({
      key: 'author',
      label: '维护人员',
      rawVal: authorStr,
      icon: FIELD_ICONS.author,
    })
  }

  // 12. 版本号
  const versionStr = data.version || data.revision || data['文档版本']
  if (versionStr) {
    items.push({
      key: 'version',
      label: '版本号',
      rawVal: versionStr,
      icon: FIELD_ICONS.version,
    })
  }

  // 13. 状态
  const statusStr = data.status || data['文档状态']
  if (statusStr) {
    items.push({
      key: 'status',
      label: '文档状态',
      rawVal: statusStr,
      icon: FIELD_ICONS.status,
    })
  }

  // 生成网格项 HTML
  const gridHtml = items
    .map((item) => {
      let valHtml = ''
      if (item.isTag) {
        const tagArr = Array.isArray(item.rawVal) ? item.rawVal : [item.rawVal]
        valHtml = `<div class="fm-tag-list">${tagArr
          .map(
            (t) =>
              `<span class="fm-tag-chip">${FIELD_ICONS.bookmark}<span>${escapeHtml(String(t))}</span></span>`
          )
          .join('')}</div>`
      } else if (item.isId) {
        valHtml = `<span class="fm-id-chip">ID: ${escapeHtml(String(item.rawVal))}</span>`
      } else if (item.isCode) {
        valHtml = `<code>${escapeHtml(String(item.rawVal))}</code>`
      } else {
        valHtml = `<span>${escapeHtml(String(item.rawVal))}</span>`
      }

      return (
        `<div class="fm-item">` +
          `<div class="fm-item-icon">${item.icon}</div>` +
          `<div class="fm-item-content">` +
            `<span class="fm-item-label">${escapeHtml(item.label)}</span>` +
            `<div class="fm-item-val">${valHtml}</div>` +
          `</div>` +
        `</div>`
      )
    })
    .join('')

  return (
    `<details class="md-frontmatter-card">` +
      `<summary class="md-fm-summary">` +
        `<div class="fm-summary-left">` +
          `<div class="fm-summary-icon">` +
            `<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2">` +
              `<path d="M4 21v-7"/><path d="M4 10V3"/><path d="M12 21v-9"/><path d="M12 8V3"/><path d="M20 21v-5"/><path d="M20 12V3"/><path d="M1 14h6"/><path d="M9 8h6"/><path d="M17 16h6"/>` +
            `</svg>` +
          `</div>` +
          `<span class="fm-summary-title">文档信息头 (Metadata)</span>` +
          `<div class="fm-summary-pills">${summaryPills.join('')}</div>` +
        `</div>` +
        `<div class="fm-summary-right">` +
          `<span class="fm-collapse-hint fm-hint-expand">点击展开详情</span>` +
          `<span class="fm-collapse-hint fm-hint-collapse">点击折叠</span>` +
          `<svg class="fm-chevron" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">` +
            `<polyline points="6 9 12 15 18 9"/>` +
          `</svg>` +
        `</div>` +
      `</summary>` +
      `<div class="md-fm-content">` +
        `<div class="fm-grid">${gridHtml}</div>` +
      `</div>` +
    `</details>`
  )
}

/**
 * 主解析函数：将 Markdown 文本转换为带 GitHub 类名的 HTML
 */
export function parseMarkdown(markdown: string): MarkdownParseResult {
  if (!markdown) {
    return { html: '', toc: [] }
  }

  const lines = markdown.split(/\r?\n/)
  const toc: TocItem[] = []
  const existingSlugs = new Set<string>()
  const output: string[] = []

  let i = 0
  const n = lines.length

  // =========================================================================
  // 1. 探测并解析 YAML Frontmatter 头部 (--- ... ---)
  // =========================================================================
  let startIdx = 0
  while (startIdx < n && lines[startIdx].trim().length === 0) {
    startIdx++
  }

  if (startIdx < n && lines[startIdx].trim() === '---') {
    let closeIdx = -1
    for (let j = startIdx + 1; j < n; j++) {
      if (lines[j].trim() === '---') {
        closeIdx = j
        break
      }
    }
    if (closeIdx > startIdx) {
      const frontmatterLines = lines.slice(startIdx + 1, closeIdx)
      const fmData = parseYaml(frontmatterLines)
      output.push(renderFrontmatterCard(fmData))
      i = closeIdx + 1

      // 跳过紧随其后的冗余文件编号引用块与重复编号行
      while (i < n) {
        const nextTrim = lines[i].trim()
        if (nextTrim.length === 0) {
          i++
          continue
        }
        if (nextTrim.startsWith('> **文件编号**') || nextTrim.startsWith('**文件编号**：')) {
          i++
          continue
        }
        break
      }
    }
  }

  // =========================================================================
  // 2. 主体 Markdown 逐行解析
  // =========================================================================
  while (i < n) {
    const line = lines[i]

    // 2.1 代码块 ```lang
    if (line.trim().startsWith('```')) {
      const lang = line.trim().slice(3).trim()
      const codeLines: string[] = []
      i++
      while (i < n && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      i++ // 跳过闭合 ```
      const rawCode = codeLines.join('\n')
      const safeCode = escapeHtml(rawCode)
      output.push(
        `<div class="code-block-wrapper">` +
          `<div class="code-block-header">` +
            `<span class="code-lang-label">${escapeHtml(lang || 'text')}</span>` +
            `<button class="btn-copy-code" data-code="${encodeURIComponent(rawCode)}" title="复制代码">` +
              `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>` +
              `<span>Copy</span>` +
            `</button>` +
          `</div>` +
          `<pre class="code-content"><code class="language-${escapeHtml(lang)}">${safeCode}</code></pre>` +
        `</div>`
      )
      continue
    }

    // 2.2 标题 # ~ ######
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/)
    if (headingMatch) {
      const level = headingMatch[1].length
      const titleRaw = headingMatch[2].trim()
      const slug = slugify(titleRaw, existingSlugs)
      const parsedTitle = parseInline(titleRaw)

      toc.push({
        id: slug,
        text: titleRaw,
        level,
      })

      output.push(
        `<h${level} id="${slug}" class="heading-anchor">` +
          `<a class="anchor" href="#${slug}" aria-hidden="true">` +
            `<svg class="octicon-link" viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="m7.775 3.275 1.25-1.25a3.5 3.5 0 1 1 4.95 4.95l-2.5 2.5a3.5 3.5 0 0 1-4.95 0 .751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018 1.998 1.998 0 0 0 2.83 0l2.5-2.5a2.002 2.002 0 0 0-2.83-2.83l-1.25 1.25a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042Zm-4.69 9.64a1.998 1.998 0 0 0 2.83 0l1.25-1.25a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042l-1.25 1.25a3.5 3.5 0 1 1-4.95-4.95l2.5-2.5a3.5 3.5 0 0 1 4.95 0 .751.751 0 0 1-.018 1.042.751.751 0 0 1-1.042.018 1.998 1.998 0 0 0-2.83 0l-2.5 2.5a1.998 1.998 0 0 0 0 2.83Z"></path></svg>` +
          `</a>` +
          `${parsedTitle}` +
        `</h${level}>`
      )
      i++

      // 检查标题后是否紧跟若干行 **元数据** (如文档版本、编写日期等)
      const metaLines: string[] = []
      let k = i
      while (k < n && lines[k].trim().length === 0) k++
      while (k < n && /^\*\*([^*：:]+)\*\*[:：]\s*(.+)$/.test(lines[k].trim())) {
        metaLines.push(lines[k].trim())
        k++
      }

      if (metaLines.length >= 2) {
        // 将连续 2 行以上的元数据转换为折叠式属性卡片
        const docMetaData: Record<string, any> = {}
        for (const ml of metaLines) {
          const m = ml.match(/^\*\*([^*：:]+)\*\*[:：]\s*(.+)$/)
          if (m) {
            docMetaData[m[1].trim()] = m[2].trim()
          }
        }
        output.push(renderFrontmatterCard(docMetaData))
        i = k
      }

      continue
    }

    // 2.3 水平分割线 --- 或 ***
    if (/^(\*{3,}|-{3,}|_{3,})$/.test(line.trim())) {
      output.push('<hr />')
      i++
      continue
    }

    // 2.4 GitHub 引用块与 Alert Callouts (> [!NOTE] 等)
    if (line.trim().startsWith('>')) {
      const quoteLines: string[] = []
      while (i < n && lines[i].trim().startsWith('>')) {
        quoteLines.push(lines[i].replace(/^>\s?/, ''))
        i++
      }

      const firstLine = quoteLines[0].trim()
      const alertMatch = firstLine.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]$/i)

      if (alertMatch) {
        const type = alertMatch[1].toUpperCase()
        const contentLines = quoteLines.slice(1)
        const innerHtml = contentLines
          .filter((l) => l.trim().length > 0)
          .map((l) => `<p>${parseInline(l)}</p>`)
          .join('')

        const icon = ALERT_ICONS[type] || ALERT_ICONS.NOTE
        const typeLabel = type.charAt(0) + type.slice(1).toLowerCase()

        output.push(
          `<div class="markdown-alert markdown-alert-${type.toLowerCase()}">` +
            `<p class="markdown-alert-title">${icon}${typeLabel}</p>` +
            `<div class="markdown-alert-content">${innerHtml}</div>` +
          `</div>`
        )
      } else {
        // 普通 blockquote
        const innerHtml = quoteLines
          .map((l) => parseInline(l))
          .join('<br />')
        output.push(`<blockquote><p>${innerHtml}</p></blockquote>`)
      }
      continue
    }

    // 2.5 GFM 表格 (| col1 | col2 |)
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      const tableLines: string[] = []
      while (i < n && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
        tableLines.push(lines[i].trim())
        i++
      }

      if (tableLines.length >= 2) {
        const headerCells = tableLines[0]
          .slice(1, -1)
          .split('|')
          .map((c) => c.trim())

        const alignRow = tableLines[1]
          .slice(1, -1)
          .split('|')
          .map((c) => {
            const s = c.trim()
            if (s.startsWith(':') && s.endsWith(':')) return 'center'
            if (s.endsWith(':')) return 'right'
            if (s.startsWith(':')) return 'left'
            return 'left'
          })

        let tableHtml = '<table><thead><tr>'
        headerCells.forEach((th, idx) => {
          const align = alignRow[idx] || 'left'
          tableHtml += `<th align="${align}">${parseInline(th)}</th>`
        })
        tableHtml += '</tr></thead><tbody>'

        for (let r = 2; r < tableLines.length; r++) {
          const rowCells = tableLines[r]
            .slice(1, -1)
            .split('|')
            .map((c) => c.trim())
          tableHtml += '<tr>'
          rowCells.forEach((td, idx) => {
            const align = alignRow[idx] || 'left'
            tableHtml += `<td align="${align}">${parseInline(td)}</td>`
          })
          tableHtml += '</tr>'
        }
        tableHtml += '</tbody></table>'
        output.push(tableHtml)
        continue
      }
    }

    // 2.6 列表 (有序 / 无序 / 任务列表)
    const isUnordered = /^(\s*)[-*+]\s+(.+)$/.test(line)
    const isOrdered = /^(\s*)\d+\.\s+(.+)$/.test(line)

    if (isUnordered || isOrdered) {
      const listTag = isOrdered ? 'ol' : 'ul'
      const listItems: string[] = []

      while (i < n) {
        const curLine = lines[i]
        const uMatch = curLine.match(/^(\s*)[-*+]\s+(.+)$/)
        const oMatch = curLine.match(/^(\s*)\d+\.\s+(.+)$/)

        if (isOrdered && oMatch) {
          listItems.push(renderListItem(oMatch[2]))
          i++
        } else if (!isOrdered && uMatch) {
          listItems.push(renderListItem(uMatch[2]))
          i++
        } else if (curLine.trim().length === 0) {
          if (i + 1 < n && (lines[i + 1].match(/^(\s*)[-*+]\s+/) || lines[i + 1].match(/^(\s*)\d+\.\s+/))) {
            i++
            continue
          }
          break
        } else {
          break
        }
      }

      output.push(`<${listTag}>${listItems.join('')}</${listTag}>`)
      continue
    }

    // 2.7 空行
    if (line.trim().length === 0) {
      i++
      continue
    }

    // 2.8 普通段落
    const paraLines: string[] = []
    while (
      i < n &&
      lines[i].trim().length > 0 &&
      !lines[i].trim().startsWith('```') &&
      !lines[i].trim().startsWith('#') &&
      !lines[i].trim().startsWith('>') &&
      !(lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) &&
      !lines[i].match(/^(\s*)[-*+]\s+/) &&
      !lines[i].match(/^(\s*)\d+\.\s+/) &&
      !/^(\*{3,}|-{3,}|_{3,})$/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i])
      i++
    }

    if (paraLines.length > 0) {
      const paraHtml = paraLines.map((l) => parseInline(l)).join('<br />')
      output.push(`<p>${paraHtml}</p>`)
    }
  }

  return {
    html: output.join('\n'),
    toc,
  }
}

/**
 * 渲染单个列表项，并识别 `- [ ]` / `- [x]` 任务列表复选框
 */
function renderListItem(content: string): string {
  if (content.startsWith('[ ] ')) {
    return `<li class="task-list-item"><input type="checkbox" disabled class="task-list-item-checkbox" /> ${parseInline(content.slice(4))}</li>`
  }
  if (content.startsWith('[x] ') || content.startsWith('[X] ')) {
    return `<li class="task-list-item"><input type="checkbox" checked disabled class="task-list-item-checkbox" /> ${parseInline(content.slice(4))}</li>`
  }
  return `<li>${parseInline(content)}</li>`
}
