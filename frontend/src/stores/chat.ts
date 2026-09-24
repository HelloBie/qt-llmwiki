import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  ChatMessage,
  sendChatSync,
  streamChat,
} from '@/api/chat'

export interface ToolLogEntry {
  node: string
  name: string
  args?: any
  content?: string
  timestamp: string
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const threadId = ref<string>('')
  const sending = ref<boolean>(false)
  const error = ref<string | null>(null)
  const useStreaming = ref<boolean>(true)
  const toolLogs = ref<ToolLogEntry[]>([])

  let abortController: AbortController | null = null

  function resetSession() {
    stop()
    messages.value = []
    threadId.value = ''
    error.value = null
    toolLogs.value = []
  }

  function stop() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    sending.value = false
  }

  async function sendMessage(userText: string) {
    const trimmed = userText.trim()
    if (!trimmed || sending.value) return

    error.value = null
    sending.value = true

    // 添加用户消息
    messages.value.push({ role: 'user', content: trimmed })

    if (useStreaming.value) {
      abortController = new AbortController()
      let assistantMsgIndex = messages.value.length
      // 先占位一个空的 assistant 消息
      messages.value.push({ role: 'assistant', content: '' })

      try {
        await streamChat(
          {
            messages: messages.value.slice(0, assistantMsgIndex),
            thread_id: threadId.value || undefined,
          },
          {
            onStart: (data) => {
              if (data.thread_id) threadId.value = data.thread_id
            },
            onToken: (data) => {
              messages.value[assistantMsgIndex].content += data.text
            },
            onToolCall: (data) => {
              toolLogs.value.push({
                node: data.node,
                name: data.name,
                args: data.args,
                timestamp: new Date().toLocaleTimeString(),
              })
            },
            onToolResult: (data) => {
              const last = toolLogs.value.find((l) => l.name === data.name && !l.content)
              if (last) {
                last.content = data.content
              } else {
                toolLogs.value.push({
                  node: data.node,
                  name: data.name,
                  content: data.content,
                  timestamp: new Date().toLocaleTimeString(),
                })
              }
            },
            onDone: (data) => {
              if (data.thread_id) threadId.value = data.thread_id
              sending.value = false
            },
            onError: (err) => {
              error.value = err.message
              sending.value = false
            },
          },
          abortController.signal
        )
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          error.value = err.message || '发送失败'
        }
      } finally {
        sending.value = false
        abortController = null
      }
    } else {
      // 非流式
      try {
        const res = await sendChatSync({
          messages: messages.value,
          thread_id: threadId.value || undefined,
        })
        threadId.value = res.thread_id
        messages.value.push({ role: 'assistant', content: res.content })
      } catch (err: any) {
        error.value = err.message || '发送失败'
      } finally {
        sending.value = false
      }
    }
  }

  return {
    messages,
    threadId,
    sending,
    error,
    useStreaming,
    toolLogs,
    sendMessage,
    stop,
    resetSession,
  }
})
