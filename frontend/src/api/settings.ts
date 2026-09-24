import { apiClient } from './client'

export interface OpenAIConfig {
  base_url: string
  api_key: string
  model: string
  temperature: number
  max_tokens: number
  top_p: number
  organization?: string
  project_id?: string
}

export interface TestConnectionResult {
  success: boolean
  message: string
  latency_ms: number
  status_code?: number
  available_models_count?: number
  models?: string[]
}

/** 从后端读取 config.yaml 中的模型配置 */
export async function fetchModelConfig(): Promise<OpenAIConfig> {
  return apiClient.get('/settings/config')
}

/** 保存模型配置并持久化写入 config.yaml */
export async function saveModelConfig(config: OpenAIConfig): Promise<{ success: boolean; message: string }> {
  return apiClient.post('/settings/config', config)
}

/** 测试与大模型端点的实际网络连通性，并带回模型列表 */
export async function testModelConnection(data: {
  base_url: string
  api_key: string
  model?: string
}): Promise<TestConnectionResult> {
  return apiClient.post('/settings/test-connection', data)
}

/** 从大模型端点在线拉取全部可用模型列表 */
export async function fetchRemoteModels(data: {
  base_url: string
  api_key: string
}): Promise<TestConnectionResult> {
  return apiClient.post('/settings/models', data)
}
