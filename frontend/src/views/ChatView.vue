<template>
  <div class="chat-viewport">
    <!-- 顶部状态工具条 -->
    <header class="chat-topbar">
      <div class="topbar-left">
        <h2 class="chat-title">智能问答</h2>
        <div class="model-tag">
          <span class="model-indicator"></span>
          <span class="model-text">deepseek-chat</span>
        </div>
        <span v-if="chatStore.threadId" class="session-badge" :title="chatStore.threadId">
          session: {{ chatStore.threadId.substring(0, 8) }}
        </span>
      </div>

      <div class="topbar-right">
        <label class="toggle-control">
          <input type="checkbox" v-model="chatStore.useStreaming" />
          <span class="toggle-slider"></span>
          <span class="toggle-label">流式打字</span>
        </label>

        <button class="action-btn" @click="chatStore.resetSession" title="新建会话">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          <span>新建会话</span>
        </button>
      </div>
    </header>

    <!-- 消息对话流容器 -->
    <main class="chat-stream" ref="messagesContainer">
      <!-- 空状态欢迎卡片 -->
      <div v-if="chatStore.messages.length === 0" class="empty-welcome">
        <div class="welcome-badge">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v4" />
            <path d="M12 18v4" />
            <path d="M4.93 4.93l2.83 2.83" />
            <path d="M16.24 16.24l2.83 2.83" />
            <path d="M2 12h4" />
            <path d="M18 12h4" />
            <path d="M4.93 19.07l2.83-2.83" />
            <path d="M16.24 7.76l2.83-2.83" />
          </svg>
        </div>
        <h3 class="welcome-title">知识库智能问答工作台</h3>
        <p class="welcome-desc">基于 FastAPI 与 LangGraph 智能体状态机编排，连接企业私有 raw/origin 资料库。</p>

        <div class="prompts-grid">
          <button class="prompt-chip" @click="quickAsk('介绍一下系统当前的架构设计与核心技术栈')">
            <div class="chip-title">系统架构概览</div>
            <div class="chip-sub">了解前后端与智能体运行时</div>
          </button>
          <button class="prompt-chip" @click="quickAsk('查询当前系统的准确日期与时间')">
            <div class="chip-title">工具调用测试</div>
            <div class="chip-sub">触发时间查询 Agent Tool</div>
          </button>
          <button class="prompt-chip" @click="quickAsk('在本地知识库中检索关于 RAG 向量切片的规范')">
            <div class="chip-title">资料库检索</div>
            <div class="chip-sub">测试知识库检索接口</div>
          </button>
        </div>
      </div>

      <!-- 消息气泡列表 -->
      <div
        v-for="(msg, index) in chatStore.messages"
        :key="index"
        :class="['message-node', msg.role === 'user' ? 'node-user' : 'node-assistant']"
      >
        <div class="avatar-box">
          <svg v-if="msg.role === 'user'" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <circle cx="12" cy="5" r="2" />
            <path d="M12 7v4" />
            <line x1="8" y1="16" x2="8" y2="16" />
            <line x1="16" y1="16" x2="16" y2="16" />
          </svg>
        </div>

        <div class="bubble-body">
          <div class="node-meta">
            <span class="node-author">{{ msg.role === 'user' ? 'You' : 'Assistant' }}</span>
          </div>

          <div class="bubble-card">
            <!-- 加载打字点动效 -->
            <div v-if="!msg.content && chatStore.sending && index === chatStore.messages.length - 1" class="loading-dots">
              <span></span><span></span><span></span>
            </div>
            <!-- 正文文本 -->
            <div v-else class="text-rendered">{{ msg.content }}</div>
          </div>
        </div>
      </div>

      <!-- 工具调用面板 (线性极简折叠器) -->
      <div v-if="chatStore.toolLogs.length > 0" class="tool-accordion">
        <button class="tool-header" @click="isToolPanelOpen = !isToolPanelOpen">
          <div class="tool-header-left">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
            </svg>
            <span>Agent 工具执行日志 ({{ chatStore.toolLogs.length }})</span>
          </div>
          <svg class="chevron-icon" :class="{ open: isToolPanelOpen }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>

        <div v-if="isToolPanelOpen" class="tool-content">
          <div v-for="(log, idx) in chatStore.toolLogs" :key="idx" class="tool-entry">
            <div class="entry-meta">
              <span class="tool-badge">{{ log.name }}</span>
              <span class="entry-time">{{ log.timestamp }}</span>
            </div>
            <div v-if="log.args" class="entry-row">
              <span class="entry-label">Input:</span>
              <code class="code-inline">{{ JSON.stringify(log.args) }}</code>
            </div>
            <div v-if="log.content" class="entry-row">
              <span class="entry-label">Output:</span>
              <span class="entry-val">{{ log.content }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 异常提示条 -->
      <div v-if="chatStore.error" class="error-notice">
        <div class="error-text">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{{ chatStore.error }}</span>
        </div>
        <button class="error-close" @click="chatStore.error = null">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </main>

    <!-- 底部输入框 -->
    <footer class="chat-input-wrapper">
      <div class="input-panel">
        <textarea
          ref="inputArea"
          v-model="inputContent"
          rows="1"
          placeholder="输入您的问题或指令... (Enter 发送，Shift+Enter 换行)"
          @keydown="handleKeydown"
          @input="autoResize"
        ></textarea>

        <div class="input-toolbar">
          <div class="toolbar-hint">按 Enter 发送</div>
          <button
            v-if="chatStore.sending"
            class="submit-btn stop-state"
            @click="chatStore.stop"
            title="停止生成"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="6" width="12" height="12" rx="2" />
            </svg>
          </button>
          <button
            v-else
            class="submit-btn"
            :disabled="!inputContent.trim()"
            @click="handleSend"
            title="发送消息"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const inputContent = ref('')
const isToolPanelOpen = ref(true)
const messagesContainer = ref<HTMLElement | null>(null)
const inputArea = ref<HTMLTextAreaElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(
  () => chatStore.messages,
  () => scrollToBottom(),
  { deep: true }
)

function autoResize() {
  if (inputArea.value) {
    inputArea.value.style.height = 'auto'
    inputArea.value.style.height = `${Math.min(inputArea.value.scrollHeight, 160)}px`
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleSend() {
  const text = inputContent.value.trim()
  if (!text || chatStore.sending) return
  chatStore.sendMessage(text)
  inputContent.value = ''
  if (inputArea.value) {
    inputArea.value.style.height = 'auto'
  }
  scrollToBottom()
}

function quickAsk(text: string) {
  inputContent.value = text
  handleSend()
}
</script>

<style scoped>
.chat-viewport {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-app);
}

/* 顶栏 */
.chat-topbar {
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

.chat-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.model-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-default);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
}

.model-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--success);
}

.model-text {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.session-badge {
  font-size: 11px;
  color: var(--text-faint);
  font-family: var(--font-mono);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toggle-control {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.toggle-control input {
  display: none;
}

.toggle-slider {
  width: 32px;
  height: 18px;
  background-color: var(--border-strong);
  border-radius: 9999px;
  position: relative;
  transition: all 0.2s ease;
}

.toggle-slider:before {
  content: "";
  position: absolute;
  width: 14px;
  height: 14px;
  left: 2px;
  top: 2px;
  background-color: #ffffff;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.toggle-control input:checked + .toggle-slider {
  background-color: var(--primary);
}

.toggle-control input:checked + .toggle-slider:before {
  transform: translateX(14px);
}

.toggle-label {
  font-size: 12px;
  color: var(--text-muted);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.action-btn:hover {
  background-color: var(--bg-subtle);
  color: var(--text-primary);
}

/* 消息流主体 */
.chat-stream {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

/* 欢迎区 */
.empty-welcome {
  margin: auto;
  text-align: center;
  max-width: 580px;
  padding: 32px 0;
}

.welcome-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
}

.welcome-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.2px;
}

.welcome-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 6px;
  line-height: 1.6;
}

.prompts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 28px;
}

.prompt-chip {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-shadow: var(--shadow-sm);
}

.prompt-chip:hover {
  border-color: var(--border-strong);
  background-color: var(--bg-subtle);
}

.chip-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.chip-sub {
  font-size: 11px;
  color: var(--text-muted);
}

/* 消息气泡节点 */
.message-node {
  display: flex;
  gap: 14px;
  max-width: 88%;
}

.node-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.node-assistant {
  align-self: flex-start;
}

.avatar-box {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
}

.node-user .avatar-box {
  background-color: var(--primary);
  color: var(--primary-text);
  border-color: var(--primary);
}

.bubble-body {
  display: flex;
  flex-direction: column;
}

.node-meta {
  font-size: 11px;
  color: var(--text-faint);
  margin-bottom: 4px;
}

.node-user .node-meta {
  text-align: right;
}

.bubble-card {
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.node-user .bubble-card {
  background-color: var(--primary);
  color: var(--primary-text);
  border-top-right-radius: 2px;
}

.node-assistant .bubble-card {
  background-color: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-sm);
  border-top-left-radius: 2px;
}

/* 工具面板 */
.tool-accordion {
  border: 1px solid var(--border-default);
  background-color: var(--bg-surface);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.tool-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background-color: var(--bg-subtle);
  border-bottom: 1px solid var(--border-default);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.tool-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chevron-icon {
  transition: transform 0.2s ease;
}

.chevron-icon.open {
  transform: rotate(180deg);
}

.tool-content {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tool-entry {
  background-color: var(--bg-app);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: 12px;
}

.entry-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.tool-badge {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--accent);
}

.entry-time {
  color: var(--text-faint);
  font-size: 11px;
}

.entry-row {
  display: flex;
  gap: 6px;
  margin-top: 3px;
  line-height: 1.4;
}

.entry-label {
  color: var(--text-muted);
  font-weight: 500;
}

.code-inline {
  font-family: var(--font-mono);
  background-color: var(--bg-subtle);
  padding: 1px 4px;
  border-radius: 4px;
  color: var(--text-secondary);
}

.entry-val {
  color: var(--text-secondary);
}

/* 异常条 */
.error-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background-color: var(--danger-subtle);
  border: 1px solid var(--danger-border);
  color: var(--danger);
  border-radius: var(--radius-md);
  font-size: 12px;
}

.error-text {
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-close {
  color: var(--danger);
}

/* 底部输入框 */
.chat-input-wrapper {
  padding: 16px 32px 24px 32px;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

.input-panel {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg);
  padding: 10px 14px;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: border-color 0.15s;
}

.input-panel:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary);
}

.input-panel textarea {
  border: none;
  background: transparent;
  resize: none;
  font-size: 13px;
  line-height: 1.5;
  max-height: 150px;
  outline: none;
}

.input-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 4px;
}

.toolbar-hint {
  font-size: 11px;
  color: var(--text-faint);
}

.submit-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background-color: var(--primary);
  color: var(--primary-text);
  display: flex;
  align-items: center;
  justify-content: center;
}

.submit-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.submit-btn.stop-state {
  background-color: var(--danger);
}

/* 极简等待动效 */
.loading-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.loading-dots span {
  width: 5px;
  height: 5px;
  background-color: var(--text-muted);
  border-radius: 50%;
  animation: pulse 1s infinite alternate;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse {
  0% { opacity: 0.3; transform: scale(0.8); }
  100% { opacity: 1; transform: scale(1); }
}
</style>
