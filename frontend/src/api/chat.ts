import { apiClient } from './client'

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string
}

export interface ChatRequest {
  messages: ChatMessage[]
  thread_id?: string
}

export interface ChatResponse {
  thread_id: string
  content: string
  messages: ChatMessage[]
  elapsed_ms: number
}

export interface ToolInfo {
  name: string
  description: string
  parameters: Record<string, any>
}

export interface HealthData {
  status: 'healthy' | 'degraded' | 'unhealthy'
  app: string
  env: string
  llm_configured: boolean
  llm_model: string
  tools_count: number
}

export interface ReadyData {
  ready: boolean
  message: string
}

export interface SSECallbacks {
  onStart?: (data: { thread_id: string }) => void
  onToken?: (data: { node: string; text: string }) => void
  onToolCall?: (data: { node: string; name: string; args: any }) => void
  onToolResult?: (data: { node: string; name: string; content: string }) => void
  onDone?: (data: { thread_id: string }) => void
  onError?: (err: Error) => void
}

/** 同步一轮对话 */
export async function sendChatSync(req: ChatRequest): Promise<ChatResponse> {
  return apiClient.post('/chat', req)
}

/** 获取服务健康状态 */
export async function getHealth(): Promise<HealthData> {
  return apiClient.get('/health')
}

/** 触发就绪探针 */
export async function getReady(): Promise<ReadyData> {
  return apiClient.get('/health/ready')
}

/** 获取已注册工具 */
export async function getTools(): Promise<ToolInfo[]> {
  return apiClient.get('/chat/tools')
}

/** fetch 版 SSE 流式客户端，支持 AbortController 取消 */
export async function streamChat(
  req: ChatRequest,
  callbacks: SSECallbacks,
  signal?: AbortSignal
): Promise<void> {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  const url = `${baseURL}/chat/stream`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(req),
    signal,
  })

  if (!response.ok) {
    let errorMsg = `HTTP 错误 ${response.status}`
    try {
      const errJson = await response.json()
      if (errJson.detail) errorMsg = errJson.detail
    } catch {
      // 保持 status 提示
    }
    const err = new Error(errorMsg)
    callbacks.onError?.(err)
    throw err
  }

  if (!response.body) {
    const err = new Error('响应未返回 ReadableStream 流式内容')
    callbacks.onError?.(err)
    throw err
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      // 保留末尾可能未闭合的一帧
      buffer = lines.pop() || ''

      for (const block of lines) {
        if (!block.trim()) continue
        const subLines = block.split('\n')
        let eventName = 'message'
        let dataStr = ''

        for (const line of subLines) {
          if (line.startsWith('event:')) {
            eventName = line.substring(6).trim()
          } else if (line.startsWith('data:')) {
            dataStr = line.substring(5).trim()
          }
        }

        if (!dataStr) continue

        try {
          const parsed = JSON.parse(dataStr)
          switch (eventName) {
            case 'start':
              callbacks.onStart?.(parsed)
              break
            case 'token':
              callbacks.onToken?.(parsed)
              break
            case 'tool_call':
              callbacks.onToolCall?.(parsed)
              break
            case 'tool_result':
              callbacks.onToolResult?.(parsed)
              break
            case 'done':
              callbacks.onDone?.(parsed)
              break
            case 'error':
              callbacks.onError?.(new Error(parsed.message || '未知流式错误'))
              break
          }
        } catch (e) {
          console.warn('解析 SSE 帧失败:', dataStr, e)
        }
      }
    }
  } catch (err: any) {
    if (signal?.aborted) {
      // 主动取消
      return
    }
    callbacks.onError?.(err)
    throw err
  }
}
