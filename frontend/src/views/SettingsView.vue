<template>
  <div class="settings-viewport">
    <header class="settings-topbar">
      <div>
        <h2 class="page-title">模型设置</h2>
        <p class="page-sub">管理 OpenAI 兼容协议的基础端点、凭证密钥及模型推理超参数</p>
      </div>
    </header>

    <div class="settings-scroll-area">
      <!-- OpenAI 配置卡片 -->
      <section class="card">
        <div class="card-header">
          <div class="card-header-left">
            <div class="provider-icon">
              <!-- 精细 OpenAI 矢量 Logo -->
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1683a.071.071 0 0 1 .038.052v5.5826a4.5045 4.5045 0 0 1-4.4945 4.4947zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4997 4.4997 0 0 1-6.1408-1.6464zM2.3428 7.897a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1683a.0757.0757 0 0 1-.071 0l-4.8303-2.7866A4.5045 4.5045 0 0 1 2.3428 7.897zm16.5991 3.8558L13.1038 8.384l2.0153-1.1636a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6726a.79.79 0 0 0-.4022-.6905zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2312V6.8988a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4997 4.4997 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1635a.0804.0804 0 0 1-.038-.0567V6.0748a4.4997 4.4997 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.4598a.7948.7948 0 0 0-.3927.6813l-.0048 6.7219zm1.3722-2.385l2.678-1.5474 2.6828 1.5474v3.0901l-2.6828 1.5474-2.678-1.5474z"/>
              </svg>
            </div>
            <div>
              <h3 class="card-title">OpenAI Compatible Provider</h3>
              <p class="card-desc">支持官方 OpenAI 及任何兼容端点 (DeepSeek / OneAPI / Ollama / FastChat)</p>
            </div>
          </div>

          <button class="btn btn-secondary btn-sm" :disabled="testing" @click="testConnection">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
            <span>{{ testing ? 'Connecting...' : '测试连通性' }}</span>
          </button>
        </div>

        <div class="form-layout">
          <!-- Base URL -->
          <div class="field full">
            <label class="field-label">
              <span>API 接口地址 (Base URL)</span>
              <span class="mark-req">*</span>
            </label>
            <input
              type="text"
              v-model="config.base_url"
              class="field-input font-mono"
              placeholder="https://api.openai.com/v1"
            />
            <span class="field-hint">
              官方地址为 <code>https://api.openai.com/v1</code>；若使用 DeepSeek 请填 <code>https://api.deepseek.com/v1</code>
            </span>
          </div>

          <!-- API Key -->
          <div class="field full">
            <label class="field-label">
              <span>API Key</span>
              <span class="mark-req">*</span>
            </label>
            <div class="key-wrapper">
              <input
                :type="showKey ? 'text' : 'password'"
                v-model="config.api_key"
                class="field-input font-mono"
                placeholder="sk-..."
              />
              <button class="eye-toggle" @click="showKey = !showKey" type="button" :title="showKey ? '隐藏' : '显示'">
                <svg v-if="!showKey" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
                <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
              </button>
            </div>
            <span class="field-hint">配置保存在 backend/config.yaml 中，支持热加载</span>
          </div>

          <!-- 元素 1: 仅读取接口模型列表下拉选择（读取不到时禁用交互） -->
          <div class="field half">
            <div class="label-row">
              <label class="field-label">
                <span>模型列表</span>
                <span class="opt-tag" :class="{ 'tag-disabled': fetchedModels.length === 0 }">
                  {{ fetchedModels.length > 0 ? `${fetchedModels.length} 个可用` : '未读取' }}
                </span>
              </label>
              <button class="text-btn" type="button" @click="refreshModels" :disabled="fetchingModels" title="从接口刷新模型列表">
                <svg :class="{ spinning: fetchingModels }" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="1 4 1 10 7 10" />
                  <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                </svg>
                <span>{{ fetchingModels ? '拉取中...' : '刷新列表' }}</span>
              </button>
            </div>
            <select
              v-model="selectedDropdownModel"
              @change="onDropdownChange"
              class="field-select"
              :disabled="fetchingModels || fetchedModels.length === 0"
            >
              <!-- 读取不到或拉取中状态 -->
              <option v-if="fetchedModels.length === 0" value="" disabled>
                {{ fetchingModels ? '正在从接口拉取模型列表...' : '未读取到模型 (下拉已禁用，请点击刷新列表)' }}
              </option>
              <!-- 读取到的接口模型选项 -->
              <template v-else>
                <option value="" disabled>-- 请下拉选择模型 (共 {{ fetchedModels.length }} 个) --</option>
                <option v-for="m in fetchedModels" :key="m" :value="m">{{ m }}</option>
              </template>
            </select>
            <span class="field-hint" v-if="fetchedModels.length > 0">
              已从接口成功读取 <code>{{ fetchedModels.length }}</code> 个模型。选择后自动填入右侧
            </span>
            <span class="field-hint text-hint-disabled" v-else>
              未读取到模型列表，下拉框已禁用交互。请点击右上角「刷新列表」，或在右侧直接手动输入
            </span>
          </div>

          <!-- 元素 2: 手动输入模型名字 -->
          <div class="field half">
            <label class="field-label">
              <span>手动输入模型名字 (Model)</span>
              <span class="mark-req">*</span>
            </label>
            <input
              type="text"
              v-model="config.model"
              @input="onModelInput"
              class="field-input font-mono"
              placeholder="例如 gpt-4o, deepseek-chat, 自定义模型名"
            />
            <span class="field-hint">最终生效的模型名称，支持直接手动键入私有微调或本地模型名</span>
          </div>

          <!-- 采样温度 Temperature -->
          <div class="field half">
            <div class="label-row">
              <label class="field-label">采样温度 (Temperature)</label>
              <span class="mono-badge">{{ config.temperature }}</span>
            </div>
            <input
              type="range"
              min="0"
              max="2"
              step="0.05"
              v-model.number="config.temperature"
              class="field-range"
            />
            <div class="scale-labels">
              <span>0.0 (确定严谨)</span>
              <span>1.0 (均衡)</span>
              <span>2.0 (发散)</span>
            </div>
          </div>

          <!-- Max Tokens -->
          <div class="field half">
            <label class="field-label">单次最大生成 Token (Max Tokens)</label>
            <input
              type="number"
              min="256"
              max="128000"
              step="256"
              v-model.number="config.max_tokens"
              class="field-input font-mono"
              placeholder="4096"
            />
          </div>

          <!-- Top P -->
          <div class="field half">
            <div class="label-row">
              <label class="field-label">核采样 (Top P)</label>
              <span class="mono-badge">{{ config.top_p }}</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1"
              step="0.05"
              v-model.number="config.top_p"
              class="field-range"
            />
            <div class="scale-labels">
              <span>0.1</span>
              <span>1.0</span>
            </div>
          </div>

          <!-- Organization ID -->
          <div class="field half">
            <label class="field-label">
              <span>组织 ID (Organization ID)</span>
              <span class="opt-tag">Optional</span>
            </label>
            <input
              type="text"
              v-model="config.organization"
              class="field-input font-mono"
              placeholder="org-..."
            />
          </div>

          <!-- Project ID -->
          <div class="field half">
            <label class="field-label">
              <span>项目 ID (Project ID)</span>
              <span class="opt-tag">Optional</span>
            </label>
            <input
              type="text"
              v-model="config.project_id"
              class="field-input font-mono"
              placeholder="proj_..."
            />
          </div>
        </div>
      </section>

      <!-- 底部保存条 -->
      <div class="actions-strip">
        <button class="btn btn-secondary" @click="resetDefaults">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          <span>恢复默认</span>
        </button>
        <button class="btn btn-primary" :disabled="saving" @click="saveSettings">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
            <polyline points="17 21 17 13 7 13 7 21" />
            <polyline points="7 3 7 8 15 8" />
          </svg>
          <span>{{ saving ? '保存中...' : '保存配置' }}</span>
        </button>
      </div>
    </div>

    <!-- Toast 提示 -->
    <transition name="toast">
      <div v-if="toastMessage" class="toast-card">
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  fetchModelConfig,
  saveModelConfig,
  testModelConnection,
  fetchRemoteModels,
  OpenAIConfig,
} from '@/api/settings'

const showKey = ref(false)
const testing = ref(false)
const saving = ref(false)
const fetchingModels = ref(false)
const toastMessage = ref('')
const selectedDropdownModel = ref('')
const fetchedModels = ref<string[]>([])

const config = ref<OpenAIConfig>({
  base_url: 'https://api.openai.com/v1',
  api_key: '',
  model: 'gpt-4o',
  temperature: 0.7,
  max_tokens: 4096,
  top_p: 1.0,
  organization: '',
  project_id: '',
})

function syncDropdownSelection() {
  const currentModel = config.value.model?.trim()
  if (currentModel && fetchedModels.value.includes(currentModel)) {
    selectedDropdownModel.value = currentModel
  } else {
    selectedDropdownModel.value = ''
  }
}

async function loadConfig() {
  try {
    const data = await fetchModelConfig()
    config.value = { ...data }
    syncDropdownSelection()
    // 若已有配置好的基础端点与密钥，尝试在线读取模型列表
    if (config.value.base_url && config.value.api_key) {
      fetchModelsOnline(true)
    }
  } catch (err: any) {
    showToast(`加载 config.yaml 失败: ${err.message}`)
  }
}

onMounted(() => {
  loadConfig()
})

function onDropdownChange() {
  if (selectedDropdownModel.value) {
    config.value.model = selectedDropdownModel.value
  }
}

function onModelInput() {
  syncDropdownSelection()
}

function showToast(msg: string) {
  toastMessage.value = msg
  setTimeout(() => {
    toastMessage.value = ''
  }, 2800)
}

async function fetchModelsOnline(silent = false) {
  if (!config.value.base_url) {
    if (!silent) showToast('请先填写 API 接口地址 (Base URL)')
    return
  }
  fetchingModels.value = true
  try {
    const res = await fetchRemoteModels({
      base_url: config.value.base_url,
      api_key: config.value.api_key,
    })
    if (res.success && res.models && res.models.length > 0) {
      fetchedModels.value = res.models
      // 若当前未填写模型名称，则默认选中第一个
      if (!config.value.model) {
        config.value.model = res.models[0]
      }
      syncDropdownSelection()
      if (!silent) {
        showToast(`成功读取到 ${res.models.length} 个可用模型，已更新下拉选项！`)
      }
    } else {
      fetchedModels.value = []
      syncDropdownSelection()
      if (!silent) {
        showToast(res.message || '端点未返回可用模型列表，下拉框已禁用')
      }
    }
  } catch (err: any) {
    fetchedModels.value = []
    syncDropdownSelection()
    if (!silent) {
      showToast(`拉取模型失败: ${err.message}`)
    }
  } finally {
    fetchingModels.value = false
  }
}

function refreshModels() {
  fetchModelsOnline(false)
}

async function testConnection() {
  if (!config.value.base_url) {
    showToast('请先填写 API 接口地址 (Base URL)')
    return
  }
  testing.value = true
  try {
    const res = await testModelConnection({
      base_url: config.value.base_url,
      api_key: config.value.api_key,
      model: config.value.model,
    })
    if (res.success) {
      if (res.models && res.models.length > 0) {
        fetchedModels.value = res.models
        syncDropdownSelection()
      }
      showToast(`连通成功 (${res.latency_ms}ms): ${res.message}`)
    } else {
      showToast(`连通失败: ${res.message}`)
    }
  } catch (err: any) {
    showToast(`连接测试出错: ${err.message}`)
  } finally {
    testing.value = false
  }
}

async function saveSettings() {
  if (!config.value.base_url || !config.value.model) {
    showToast('Base URL 和模型名称不能为空')
    return
  }
  saving.value = true
  try {
    const res = await saveModelConfig(config.value)
    showToast(`配置已成功写入 config.yaml，并对对话即刻生效！`)
  } catch (err: any) {
    showToast(`保存失败: ${err.message}`)
  } finally {
    saving.value = false
  }
}

function resetDefaults() {
  config.value = {
    base_url: 'https://api.openai.com/v1',
    api_key: '',
    model: 'gpt-4o',
    temperature: 0.7,
    max_tokens: 4096,
    top_p: 1.0,
    organization: '',
    project_id: '',
  }
  fetchedModels.value = []
  syncDropdownSelection()
  showToast('已重置为默认配置，点击保存后写入 config.yaml')
}
</script>

<style scoped>
.settings-viewport {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-app);
}

.settings-topbar {
  height: 54px;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  padding: 0 24px;
}

.page-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.page-sub {
  font-size: 11px;
  color: var(--text-muted);
}

.settings-scroll-area {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-card);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border-light);
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.provider-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background-color: var(--primary);
  color: var(--primary-text);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.card-desc {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 1px;
}

.form-layout {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field.full {
  grid-column: span 2;
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.mark-req {
  color: var(--danger);
}

.opt-tag {
  font-size: 10px;
  font-weight: normal;
  color: var(--text-faint);
  background-color: var(--bg-subtle);
  padding: 1px 4px;
  border-radius: 3px;
}

.text-btn {
  font-size: 11px;
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 4px;
  border-radius: 4px;
  cursor: pointer;
}

.text-btn:hover:not(:disabled) {
  color: var(--primary);
  background-color: var(--bg-subtle);
}

.text-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.field-hint {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.4;
}

.field-hint code {
  font-family: var(--font-mono);
  background-color: var(--bg-subtle);
  padding: 1px 4px;
  border-radius: 3px;
  color: var(--text-secondary);
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mono-badge {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--primary);
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-default);
  padding: 1px 5px;
  border-radius: 4px;
}

.field-input,
.field-select {
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 7px 10px;
  font-size: 12px;
  background-color: var(--bg-app);
  outline: none;
  transition: all 0.15s ease;
}

.font-mono {
  font-family: var(--font-mono);
}

.field-input:focus,
.field-select:focus {
  border-color: var(--primary);
  background-color: var(--bg-surface);
  box-shadow: 0 0 0 1px var(--primary);
}

.field-select:disabled {
  background-color: var(--bg-subtle);
  color: var(--text-faint);
  cursor: not-allowed;
  opacity: 0.75;
  border-style: dashed;
}

.opt-tag.tag-disabled {
  color: var(--text-faint);
  opacity: 0.7;
}

.text-hint-disabled {
  color: var(--text-faint);
}

.model-select-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.key-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.key-wrapper input {
  width: 100%;
  padding-right: 32px;
}

.eye-toggle {
  position: absolute;
  right: 8px;
  color: var(--text-muted);
  padding: 2px;
}

.eye-toggle:hover {
  color: var(--text-primary);
}

.field-range {
  accent-color: var(--primary);
  cursor: pointer;
  margin-top: 4px;
}

.scale-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-faint);
  font-family: var(--font-mono);
}

.actions-strip {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 30px;
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
