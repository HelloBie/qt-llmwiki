/**
 * 高保真 GitHub 风格 Markdown 渲染与大纲提取器
 * 零第三方外部重型依赖，完全兼容 Vite 与 Docker 构建
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

  while (i < n) {
    const line = lines[i]

    // 1. 代码块 ```lang
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

    // 2. 标题 # ~ ######
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
      continue
    }

    // 3. 水平分割线 --- 或 ***
    if (/^(\*{3,}|-{3,}|_{3,})$/.test(line.trim())) {
      output.push('<hr />')
      i++
      continue
    }

    // 4. GitHub 引用块与 Alert Callouts (> [!NOTE] 等)
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

    // 5. GFM 表格 (| col1 | col2 |)
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

    // 6. 列表 (有序 / 无序 / 任务列表)
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
          // 遇到空行判断是否继续
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

    // 7. 空行
    if (line.trim().length === 0) {
      i++
      continue
    }

    // 8. 段落
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
