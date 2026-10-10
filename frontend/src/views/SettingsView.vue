<template>
  <div class="settings-viewport">
    <header class="settings-topbar">
      <div>
        <h2 class="page-title">{{ activeTab === 'model' ? '模型设置' : '系统工程设计文档' }}</h2>
        <p class="page-sub">
          {{
            activeTab === 'model'
              ? '集中配置与调优五大分工模型：对话问答、文件消化、向量编码、语义重排与查询扩展'
              : '查阅系统概要设计、详细设计、数据库设计与接口规范 (GitHub 风格实时预览)'
          }}
        </p>
      </div>

      <!-- 设置子导航切换器 -->
      <div class="settings-tab-group">
        <button
          :class="['settings-tab-btn', { active: activeTab === 'model' }]"
          @click="switchTab('model')"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <span>模型配置</span>
        </button>
        <button
          :class="['settings-tab-btn', { active: activeTab === 'docs' }]"
          @click="switchTab('docs')"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span>工程设计文档</span>
        </button>
      </div>
    </header>

    <div :class="['settings-scroll-area', { 'wide-layout': activeTab === 'docs' }]">
      <!-- 视图 1: 多模型分工配置 -->
      <template v-if="activeTab === 'model'">
        <!-- 全局默认主端点卡片 -->
        <section class="card global-provider-card">
          <div class="card-header">
            <div class="card-header-left">
              <div class="provider-icon">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="2" y1="12" x2="22" y2="12" />
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                </svg>
              </div>
              <div>
                <div class="card-title-row">
                  <h3 class="card-title">全局默认端点 (Default / Cloud Provider)</h3>
                  <span class="badge-role">主基准端点</span>
                </div>
                <p class="card-desc">所有未单独指定独立端点的模型角色将默认继承此处的 Base URL 和 API 密钥</p>
              </div>
            </div>

            <button class="btn btn-secondary btn-sm" :disabled="testingGlobal" @click="testGlobalConnection">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
              <span>{{ testingGlobal ? '连接中...' : '测试全局连通性' }}</span>
            </button>
          </div>

          <div class="form-layout">
            <!-- 全局 Base URL -->
            <div class="field half">
              <label class="field-label">
                <span>全局 API 基础端点 (Base URL)</span>
                <span class="mark-req">*</span>
              </label>
              <input
                type="text"
                v-model="config.base_url"
                class="field-input font-mono"
                placeholder="https://api.deepseek.com/v1"
              />
              <span class="field-hint">
                如 DeepSeek <code>https://api.deepseek.com/v1</code> 或 阿里百炼 <code>https://dashscope.aliyuncs.com/compatible-mode/v1</code>
              </span>
            </div>

            <!-- 全局 API Key -->
            <div class="field half">
              <label class="field-label">
                <span>全局 API Key</span>
                <span class="mark-req">*</span>
              </label>
              <div class="key-wrapper">
                <input
                  :type="showGlobalKey ? 'text' : 'password'"
                  v-model="config.api_key"
                  class="field-input font-mono"
                  placeholder="sk-..."
                />
                <button class="eye-toggle" @click="showGlobalKey = !showGlobalKey" type="button" :title="showGlobalKey ? '隐藏' : '显示'">
                  <svg v-if="!showGlobalKey" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                  <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                </button>
              </div>
              <span class="field-hint">凭证密钥持久化保存在 backend/config.yaml 中</span>
            </div>
          </div>
        </section>

        <!-- 五大功能模型角色配置导航区 -->
        <section class="card roles-section-card">
          <div class="section-title-bar">
            <div>
              <h3 class="card-title">五大功能模型角色矩阵</h3>
              <p class="card-desc">为对话、消化、向量、重排与扩展五个关键链路分别指定最合适的大/小模型与超参数</p>
            </div>
          </div>

          <!-- 角色切换胶囊栏 -->
          <div class="role-selector-pills">
            <button
              v-for="r in roleDefs"
              :key="r.key"
              :class="['role-pill', { active: currentRoleKey === r.key }]"
              @click="currentRoleKey = r.key"
            >
              <div class="pill-icon" v-html="r.icon"></div>
              <div class="pill-text">
                <span class="pill-name">{{ r.label }}</span>
                <span class="pill-model-tag" :title="getRoleModelName(r.key)">
                  {{ getRoleModelName(r.key) || '未指定' }}
                </span>
              </div>
              <span class="pill-endpoint-badge" :class="getRoleEndpointType(r.key)">
                {{ getRoleEndpointLabel(r.key) }}
              </span>
            </button>
          </div>

          <!-- 当前选中角色的专属配置面板 -->
          <div class="role-detail-panel" v-if="activeRoleDef && currentRoleConfig">
            <div class="panel-header">
              <div class="panel-header-left">
                <div class="panel-icon" v-html="activeRoleDef.icon"></div>
                <div>
                  <div class="panel-title-row">
                    <h4 class="panel-title">{{ activeRoleDef.label }}</h4>
                    <span class="role-code-tag">{{ activeRoleDef.key }}</span>
                  </div>
                  <p class="panel-desc">{{ activeRoleDef.description }}</p>
                </div>
              </div>

              <!-- 针对此角色的连通性测试 -->
              <button
                class="btn btn-secondary btn-sm"
                :disabled="testingRole"
                @click="testCurrentRoleConnection"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                </svg>
                <span>{{ testingRole ? '测试中...' : '测试该模型端点' }}</span>
              </button>
            </div>

            <!-- 端点模式切换单选 -->
            <div class="endpoint-mode-box">
              <div class="mode-header">
                <span class="mode-label">端点服务提供者：</span>
                <div class="mode-radios">
                  <label class="radio-chip" :class="{ selected: !hasCustomEndpoint }">
                    <input
                      type="radio"
                      :name="'endpoint_mode_' + activeRoleDef.key"
                      :value="false"
                      v-model="hasCustomEndpoint"
                    />
                    <span>继承全局默认端点</span>
                  </label>
                  <label class="radio-chip" :class="{ selected: hasCustomEndpoint }">
                    <input
                      type="radio"
                      :name="'endpoint_mode_' + activeRoleDef.key"
                      :value="true"
                      v-model="hasCustomEndpoint"
                    />
                    <span>独立端点 (如本地 Ollama)</span>
                  </label>
                </div>
              </div>

              <!-- 若启用自定义独立端点，展开独立 Base URL 与 API Key 输入 -->
              <div v-if="hasCustomEndpoint" class="custom-endpoint-row">
                <div class="field full">
                  <div class="label-row">
                    <label class="field-label">独立端点地址 (Base URL)</label>
                    <div class="quick-preset-btns">
                      <button
                        type="button"
                        class="preset-badge-btn"
                        @click="fillOllamaEndpoint"
                        title="填入本地 Docker Ollama API 地址"
                      >
                        填入本地 Ollama (11434)
                      </button>
                    </div>
                  </div>
                  <input
                    type="text"
                    v-model="currentRoleConfig.base_url"
                    class="field-input font-mono"
                    placeholder="http://localhost:11434/v1"
                  />
                  <span class="field-hint">
                    本地 Ollama 请填 <code>http://localhost:11434/v1</code> 或 <code>http://ollama:11434/v1</code>
                  </span>
                </div>

                <div class="field full">
                  <label class="field-label">独立 API 密钥 (API Key)</label>
                  <div class="key-wrapper">
                    <input
                      :type="showRoleKey ? 'text' : 'password'"
                      v-model="currentRoleConfig.api_key"
                      class="field-input font-mono"
                      placeholder="本地 Ollama 可选填 ollama 或留空"
                    />
                    <button class="eye-toggle" @click="showRoleKey = !showRoleKey" type="button" :title="showRoleKey ? '隐藏' : '显示'">
                      <svg v-if="!showRoleKey" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                      <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                        <line x1="1" y1="1" x2="23" y2="23" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 模型选择区域 -->
            <div class="form-layout role-form-layout">
              <!-- 下拉选择模型 -->
              <div class="field half">
                <div class="label-row">
                  <label class="field-label">
                    <span>从端点探测模型</span>
                    <span class="opt-tag" :class="{ 'tag-disabled': roleModelList.length === 0 }">
                      {{ roleModelList.length > 0 ? `${roleModelList.length} 个可用` : '未读取' }}
                    </span>
                  </label>
                  <button
                    class="text-btn"
                    type="button"
                    @click="refreshRoleModels"
                    :disabled="fetchingRoleModels"
                    title="从当前生效端点刷新模型列表"
                  >
                    <svg :class="{ spinning: fetchingRoleModels }" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="1 4 1 10 7 10" />
                      <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                    </svg>
                    <span>{{ fetchingRoleModels ? '探测中...' : '在线探测' }}</span>
                  </button>
                </div>
                <select
                  v-model="selectedRoleDropdownModel"
                  @change="onRoleDropdownChange"
                  class="field-select"
                  :disabled="fetchingRoleModels || roleModelList.length === 0"
                >
                  <option v-if="roleModelList.length === 0" value="" disabled>
                    {{ fetchingRoleModels ? '正在从端点拉取模型列表...' : '未拉取到列表 (请点击在线探测，或在右侧手动输入)' }}
                  </option>
                  <template v-else>
                    <option value="" disabled>-- 请下拉选择目标模型 (共 {{ roleModelList.length }} 个) --</option>
                    <option v-for="m in roleModelList" :key="m" :value="m">{{ m }}</option>
                  </template>
                </select>
                <span class="field-hint" v-if="roleModelList.length > 0">
                  选择后自动同步至右侧模型名称输入框
                </span>
                <span class="field-hint text-hint-disabled" v-else>
                  若端点不支持 /models 探测，可直接在右侧手动输入模型标识
                </span>
              </div>

              <!-- 手动输入模型标识 -->
              <div class="field half">
                <label class="field-label">
                  <span>模型标识名称 (Model Name)</span>
                  <span class="mark-req">*</span>
                </label>
                <input
                  type="text"
                  v-model="currentRoleConfig.name"
                  class="field-input font-mono"
                  placeholder="例如 deepseek-chat, bge-m3, qwen2.5:1.5b"
                />
                <!-- 国产推荐快捷胶囊 -->
                <div class="recommend-pills">
                  <span class="rec-label">推荐国产模型:</span>
                  <button
                    v-for="rec in activeRoleDef.recommendedModels"
                    :key="rec"
                    type="button"
                    class="rec-pill"
                    @click="currentRoleConfig.name = rec"
                  >
                    {{ rec }}
                  </button>
                </div>
              </div>

              <!-- 超参数：生成类模型专用 (Temperature / Max Tokens) -->
              <template v-if="activeRoleDef.hasTemperature">
                <div class="field half">
                  <div class="label-row">
                    <label class="field-label">采样温度 (Temperature)</label>
                    <span class="mono-badge">{{ currentRoleConfig.temperature ?? 0.7 }}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1.5"
                    step="0.05"
                    v-model.number="currentRoleConfig.temperature"
                    class="field-range"
                  />
                  <div class="scale-labels">
                    <span>0.0 (严谨精确)</span>
                    <span>0.7 (均衡)</span>
                    <span>1.5 (发散多样)</span>
                  </div>
                </div>
              </template>

              <template v-if="activeRoleDef.hasMaxTokens">
                <div class="field half">
                  <label class="field-label">最大生成 Token 数 (Max Tokens)</label>
                  <input
                    type="number"
                    min="256"
                    max="128000"
                    step="256"
                    v-model.number="currentRoleConfig.max_tokens"
                    class="field-input font-mono"
                    placeholder="4096"
                  />
                </div>
              </template>

              <!-- 超参数：向量模型专用 (向量维度) -->
              <template v-if="activeRoleDef.hasDimension">
                <div class="field half">
                  <label class="field-label">向量表征维度 (Embedding Dimension)</label>
                  <input
                    type="number"
                    min="128"
                    max="8192"
                    step="128"
                    v-model.number="currentRoleConfig.dimension"
                    class="field-input font-mono"
                    placeholder="1024"
                  />
                  <span class="field-hint">
                    如 <code>bge-m3</code> 为 1024 维；<code>bge-base-zh</code> 为 768 维；OpenAI 默认 1536 维
                  </span>
                </div>
              </template>

              <!-- 超参数：重排模型专用 (Top-N 精选截取数) -->
              <template v-if="activeRoleDef.hasTopN">
                <div class="field half">
                  <div class="label-row">
                    <label class="field-label">精选返回文档块数量 (Top-N)</label>
                    <span class="mono-badge">{{ currentRoleConfig.top_n ?? 5 }} 块</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    step="1"
                    v-model.number="currentRoleConfig.top_n"
                    class="field-range"
                  />
                  <div class="scale-labels">
                    <span>1 块 (极致精准)</span>
                    <span>5 块 (标准推荐)</span>
                    <span>20 块 (宽泛召回)</span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </section>

        <!-- 底部全局操作条 -->
        <div class="actions-strip">
          <div class="actions-left">
            <button class="btn btn-secondary" @click="applyHouseholdPreset">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
              <span>一键套用「家用机黄金组合」预设</span>
            </button>
            <button class="btn btn-secondary" @click="resetDefaults">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="1 4 1 10 7 10" />
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
              </svg>
              <span>恢复默认</span>
            </button>
          </div>

          <div class="actions-right">
            <button class="btn btn-primary" :disabled="saving" @click="saveSettings">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                <polyline points="17 21 17 13 7 13 7 21" />
                <polyline points="7 3 7 8 15 8" />
              </svg>
              <span>{{ saving ? '保存中...' : '保存全部模型配置' }}</span>
            </button>
          </div>
        </div>
      </template>

      <!-- 视图 2: 工程设计文档 GitHub README 风格预览 -->
      <template v-else>
        <DocsPreview />
      </template>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DocsPreview from '@/components/DocsPreview.vue'
import {
  fetchModelConfig,
  saveModelConfig,
  testModelConnection,
  fetchRemoteModels,
  OpenAIConfig,
  ModelRoleConfig,
} from '@/api/settings'

const route = useRoute()
const router = useRouter()
const activeTab = ref<'model' | 'docs'>((route.query.tab as 'model' | 'docs') || 'model')

function switchTab(tab: 'model' | 'docs') {
  activeTab.value = tab
  router.replace({ query: { ...route.query, tab } })
}

watch(
  () => route.query.tab,
  (newTab) => {
    if (newTab === 'docs' || newTab === 'model') {
      activeTab.value = newTab
    }
  }
)

// 角色元数据定义
interface RoleDef {
  key: 'chat' | 'digest' | 'embedding' | 'rerank' | 'expansion'
  label: string
  description: string
  icon: string
  recommendedModels: string[]
  hasTemperature?: boolean
  hasMaxTokens?: boolean
  hasDimension?: boolean
  hasTopN?: boolean
}

const roleDefs: RoleDef[] = [
  {
    key: 'chat',
    label: '对话主模型',
    description: '面向用户直接交互，负责多轮问答、事实核查与综合推理，建议使用云端旗舰或 14B+ 大模型',
    icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
    recommendedModels: ['deepseek-chat', 'qwen-max', 'qwen2.5:72b', 'gpt-4o'],
    hasTemperature: true,
    hasMaxTokens: true,
  },
  {
    key: 'digest',
    label: '文件消化模型',
    description: '文档上传后负责长文本解析、段落总结、核心概念提炼与实体结构化知识库抽取',
    icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
    recommendedModels: ['qwen-plus', 'deepseek-chat', 'gpt-4o-mini', 'qwen2.5:14b'],
    hasTemperature: true,
    hasMaxTokens: true,
  },
  {
    key: 'embedding',
    label: '向量编码模型',
    description: '将文档切片转化为密集嵌入向量（Dense Embedding），支撑毫秒级粗排语义检索召回',
    icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`,
    recommendedModels: ['bge-m3', 'bge-base-zh', 'text-embedding-3-small'],
    hasDimension: true,
  },
  {
    key: 'rerank',
    label: '语义重排模型',
    description: '基于 Cross-Encoder 架构对初筛候选文本块打分，精准过滤 80% 无关噪声碎片',
    icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
    recommendedModels: ['bge-reranker-v2-m3', 'bge-reranker-large'],
    hasTopN: true,
  },
  {
    key: 'expansion',
    label: '查询扩展模型',
    description: '将用户口语提问进行多角度扩写、专业同义词丰富与子问题拆解，快如闪电',
    icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>`,
    recommendedModels: ['qwen2.5:1.5b', 'qwen2.5:3b', 'qwen2.5:0.5b'],
    hasTemperature: true,
  },
]

type RoleKey = 'chat' | 'digest' | 'embedding' | 'rerank' | 'expansion'
const currentRoleKey = ref<RoleKey>('chat')

const showGlobalKey = ref(false)
const showRoleKey = ref(false)
const testingGlobal = ref(false)
const testingRole = ref(false)
const saving = ref(false)
const fetchingRoleModels = ref(false)
const toastMessage = ref('')

// 模型列表缓存字典 (以 endpoint url 为 key)
const endpointModelsCache = ref<Record<string, string[]>>({})
const selectedRoleDropdownModel = ref('')

// 主配置对象
const config = ref<OpenAIConfig>({
  base_url: 'https://api.deepseek.com/v1',
  api_key: '',
  model: 'deepseek-chat',
  temperature: 0.7,
  max_tokens: 4096,
  top_p: 1.0,
  organization: '',
  project_id: '',
  chat: {
    name: 'deepseek-chat',
    base_url: '',
    api_key: '',
    temperature: 0.7,
    max_tokens: 4096,
    description: '主问答对话模型',
  },
  digest: {
    name: 'qwen-plus',
    base_url: '',
    api_key: '',
    temperature: 0.3,
    max_tokens: 4096,
    description: '文件消化解析模型',
  },
  embedding: {
    name: 'bge-m3',
    base_url: 'http://localhost:11434/v1',
    api_key: 'ollama',
    dimension: 1024,
    description: '向量嵌入模型',
  },
  rerank: {
    name: 'bge-reranker-v2-m3',
    base_url: 'http://localhost:11434',
    api_key: 'ollama',
    top_n: 5,
    description: '语义重排模型',
  },
  expansion: {
    name: 'qwen2.5:1.5b',
    base_url: 'http://localhost:11434/v1',
    api_key: 'ollama',
    temperature: 0.3,
    description: '查询扩展模型',
  },
})

// 计算当前角色的元数据与配置
const activeRoleDef = computed(() => {
  return roleDefs.find((r) => r.key === currentRoleKey.value) || roleDefs[0]
})

const currentRoleConfig = computed<ModelRoleConfig>(() => {
  const key = currentRoleKey.value
  if (!config.value[key]) {
    config.value[key] = {
      name: '',
      base_url: '',
      api_key: '',
      temperature: 0.7,
    }
  }
  return config.value[key]!
})

// 当前角色是否使用独立端点
const hasCustomEndpoint = computed<boolean>({
  get() {
    return !!(currentRoleConfig.value.base_url && currentRoleConfig.value.base_url.trim().length > 0)
  },
  set(val: boolean) {
    if (!val) {
      currentRoleConfig.value.base_url = ''
      currentRoleConfig.value.api_key = ''
    } else {
      if (!currentRoleConfig.value.base_url) {
        if (currentRoleKey.value === 'rerank') {
          currentRoleConfig.value.base_url = 'http://localhost:11434'
        } else if (['embedding', 'expansion'].includes(currentRoleKey.value)) {
          currentRoleConfig.value.base_url = 'http://localhost:11434/v1'
        } else {
          currentRoleConfig.value.base_url = config.value.base_url || 'http://localhost:11434/v1'
        }
      }
    }
  },
})

// 计算当前角色有效端点地址
const currentEffectiveEndpoint = computed(() => {
  if (currentRoleConfig.value.base_url?.trim()) {
    return currentRoleConfig.value.base_url.trim()
  }
  return config.value.base_url.trim()
})

const currentEffectiveApiKey = computed(() => {
  if (currentRoleConfig.value.base_url?.trim()) {
    return currentRoleConfig.value.api_key?.trim() || ''
  }
  return config.value.api_key.trim()
})

// 当前角色可用的模型下拉选项
const roleModelList = computed(() => {
  const url = currentEffectiveEndpoint.value
  return endpointModelsCache.value[url] || []
})

// 监听角色切换或模型改变，同步下拉框选中状态
watch(
  [() => currentRoleKey.value, () => currentRoleConfig.value.name, roleModelList],
  () => {
    const name = currentRoleConfig.value.name?.trim() || ''
    if (name && roleModelList.value.includes(name)) {
      selectedRoleDropdownModel.value = name
    } else {
      selectedRoleDropdownModel.value = ''
    }
  },
  { immediate: true }
)

function getRoleModelName(roleKey: RoleKey): string {
  return config.value[roleKey]?.name || ''
}

function getRoleEndpointType(roleKey: RoleKey): string {
  const customUrl = config.value[roleKey]?.base_url?.trim() || ''
  if (customUrl) {
    if (customUrl.includes('11434')) return 'type-ollama'
    return 'type-custom'
  }
  return 'type-global'
}

function getRoleEndpointLabel(roleKey: RoleKey): string {
  const customUrl = config.value[roleKey]?.base_url?.trim() || ''
  if (customUrl) {
    if (customUrl.includes('11434')) return '本地 Ollama'
    return '独立端点'
  }
  return '继承全局'
}

function onRoleDropdownChange() {
  if (selectedRoleDropdownModel.value) {
    currentRoleConfig.value.name = selectedRoleDropdownModel.value
  }
}

function fillOllamaEndpoint() {
  if (currentRoleKey.value === 'rerank') {
    currentRoleConfig.value.base_url = 'http://localhost:11434'
  } else {
    currentRoleConfig.value.base_url = 'http://localhost:11434/v1'
  }
  currentRoleConfig.value.api_key = 'ollama'
  showToast('已填入本地 Ollama 端点地址')
}

function showToast(msg: string) {
  toastMessage.value = msg
  setTimeout(() => {
    toastMessage.value = ''
  }, 3000)
}

// 刷新指定端点的模型列表
async function fetchModelsForUrl(url: string, apiKey: string, silent = false): Promise<string[]> {
  if (!url) return []
  try {
    const res = await fetchRemoteModels({ base_url: url, api_key: apiKey })
    if (res.success && res.models && res.models.length > 0) {
      endpointModelsCache.value[url] = res.models
      if (!silent) {
        showToast(`成功探测到 ${res.models.length} 个可用模型`)
      }
      return res.models
    } else {
      endpointModelsCache.value[url] = []
      if (!silent) {
        showToast(res.message || '端点未返回可用模型列表')
      }
    }
  } catch (err: any) {
    endpointModelsCache.value[url] = []
    if (!silent) {
      showToast(`模型探测失败: ${err.message}`)
    }
  }
  return []
}

async function refreshRoleModels() {
  const url = currentEffectiveEndpoint.value
  const key = currentEffectiveApiKey.value
  if (!url) {
    showToast('请先配置该角色的端点地址')
    return
  }
  fetchingRoleModels.value = true
  try {
    await fetchModelsForUrl(url, key, false)
  } finally {
    fetchingRoleModels.value = false
  }
}

async function testGlobalConnection() {
  if (!config.value.base_url) {
    showToast('请先填写全局 API 基础端点 (Base URL)')
    return
  }
  testingGlobal.value = true
  try {
    const res = await testModelConnection({
      base_url: config.value.base_url,
      api_key: config.value.api_key,
      model: config.value.chat?.name || config.value.model,
    })
    if (res.success) {
      if (res.models && res.models.length > 0) {
        endpointModelsCache.value[config.value.base_url] = res.models
      }
      showToast(`全局端点连通成功 (${res.latency_ms}ms): ${res.message}`)
    } else {
      showToast(`连通失败: ${res.message}`)
    }
  } catch (err: any) {
    showToast(`连接测试出错: ${err.message}`)
  } finally {
    testingGlobal.value = false
  }
}

async function testCurrentRoleConnection() {
  const url = currentEffectiveEndpoint.value
  const key = currentEffectiveApiKey.value
  if (!url) {
    showToast('请先配置该角色的端点地址')
    return
  }
  testingRole.value = true
  try {
    const res = await testModelConnection({
      base_url: url,
      api_key: key,
      model: currentRoleConfig.value.name,
    })
    if (res.success) {
      if (res.models && res.models.length > 0) {
        endpointModelsCache.value[url] = res.models
      }
      showToast(`[${activeRoleDef.value.label}] 端点连通成功 (${res.latency_ms}ms)`)
    } else {
      showToast(`连通失败: ${res.message}`)
    }
  } catch (err: any) {
    showToast(`连接测试出错: ${err.message}`)
  } finally {
    testingRole.value = false
  }
}

async function loadConfig() {
  try {
    const data = await fetchModelConfig()
    config.value = {
      ...data,
      chat: data.chat || { name: data.model || 'deepseek-chat', temperature: 0.7, max_tokens: 4096 },
      digest: data.digest || { name: 'qwen-plus', temperature: 0.3, max_tokens: 4096 },
      embedding: data.embedding || { name: 'bge-m3', base_url: 'http://localhost:11434/v1', api_key: 'ollama', dimension: 1024 },
      rerank: data.rerank || { name: 'bge-reranker-v2-m3', base_url: 'http://localhost:11434', api_key: 'ollama', top_n: 5 },
      expansion: data.expansion || { name: 'qwen2.5:1.5b', base_url: 'http://localhost:11434/v1', api_key: 'ollama', temperature: 0.3 },
    }

    // 静默尝试探测全局端点模型列表
    if (config.value.base_url) {
      fetchModelsForUrl(config.value.base_url, config.value.api_key, true)
    }
  } catch (err: any) {
    showToast(`加载 config.yaml 失败: ${err.message}`)
  }
}

onMounted(() => {
  loadConfig()
})

async function saveSettings() {
  if (!config.value.base_url) {
    showToast('全局 Base URL 不能为空')
    return
  }
  if (!config.value.chat?.name) {
    showToast('对话主模型名称不能为空')
    return
  }
  saving.value = true
  try {
    // 确保根 model 字段与 chat.name 同步
    config.value.model = config.value.chat.name
    await saveModelConfig(config.value)
    showToast('全部模型角色配置已成功保存写入 config.yaml，实时生效！')
  } catch (err: any) {
    showToast(`保存失败: ${err.message}`)
  } finally {
    saving.value = false
  }
}

function applyHouseholdPreset() {
  config.value.base_url = 'https://api.deepseek.com/v1'
  config.value.chat = {
    name: 'deepseek-chat',
    base_url: '',
    api_key: '',
    temperature: 0.7,
    max_tokens: 4096,
    description: '主问答对话模型',
  }
  config.value.digest = {
    name: 'qwen-plus',
    base_url: '',
    api_key: '',
    temperature: 0.3,
    max_tokens: 4096,
    description: '文件消化解析模型',
  }
  config.value.embedding = {
    name: 'bge-m3',
    base_url: 'http://localhost:11434/v1',
    api_key: 'ollama',
    dimension: 1024,
    description: '向量嵌入模型',
  }
  config.value.rerank = {
    name: 'bge-reranker-v2-m3',
    base_url: 'http://localhost:11434',
    api_key: 'ollama',
    top_n: 5,
    description: '语义重排模型',
  }
  config.value.expansion = {
    name: 'qwen2.5:1.5b',
    base_url: 'http://localhost:11434/v1',
    api_key: 'ollama',
    temperature: 0.3,
    description: '查询扩展模型',
  }
  showToast('已套用「家用机黄金组合」预设（云端 DeepSeek + 本地 Ollama 三小模型），请点击保存！')
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
    chat: {
      name: 'gpt-4o',
      base_url: '',
      api_key: '',
      temperature: 0.7,
      max_tokens: 4096,
    },
    digest: {
      name: 'gpt-4o-mini',
      base_url: '',
      api_key: '',
      temperature: 0.3,
      max_tokens: 4096,
    },
    embedding: {
      name: 'text-embedding-3-small',
      base_url: '',
      api_key: '',
      dimension: 1536,
    },
    rerank: {
      name: 'bge-reranker-v2-m3',
      base_url: 'http://localhost:11434',
      api_key: 'ollama',
      top_n: 5,
    },
    expansion: {
      name: 'gpt-4o-mini',
      base_url: '',
      api_key: '',
      temperature: 0.3,
    },
  }
  showToast('已重置为官方标准配置，点击保存后写入 config.yaml')
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
  justify-content: space-between;
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

.settings-tab-group {
  display: flex;
  align-items: center;
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 2px;
  gap: 2px;
}

.settings-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  border-radius: 4px;
  transition: all 0.15s ease;
}

.settings-tab-btn:hover {
  color: var(--text-primary);
}

.settings-tab-btn.active {
  background-color: var(--bg-surface);
  color: var(--primary);
  box-shadow: var(--shadow-sm);
  font-weight: 600;
}

.settings-scroll-area {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
  max-width: 980px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  transition: max-width 0.2s ease;
}

.settings-scroll-area.wide-layout {
  max-width: 1240px;
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
  margin-bottom: 16px;
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

.card-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.badge-role {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.06);
  color: var(--text-secondary);
}

.card-desc {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
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

/* 角色导航胶囊栏 */
.roles-section-card {
  padding-bottom: 24px;
}

.section-title-bar {
  margin-bottom: 16px;
}

.role-selector-pills {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-bottom: 20px;
}

.role-pill {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 10px 12px;
  background-color: var(--bg-subtle);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.role-pill:hover {
  border-color: var(--border-strong);
  background-color: var(--bg-surface);
}

.role-pill.active {
  background-color: var(--bg-surface);
  border-color: var(--primary);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.pill-icon {
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  margin-bottom: 2px;
}

.role-pill.active .pill-icon {
  color: var(--primary);
}

.pill-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
  min-width: 0;
}

.pill-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.pill-model-tag {
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pill-endpoint-badge {
  font-size: 9px;
  font-weight: 500;
  padding: 1px 5px;
  border-radius: 3px;
  margin-top: 4px;
}

.pill-endpoint-badge.type-global {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--text-muted);
}

.pill-endpoint-badge.type-ollama {
  background-color: rgba(16, 185, 129, 0.1);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.pill-endpoint-badge.type-custom {
  background-color: rgba(59, 130, 246, 0.1);
  color: #2563eb;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

/* 角色详情面板 */
.role-detail-panel {
  background-color: var(--bg-app);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 18px 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}

.panel-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.panel-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.role-code-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  background-color: var(--bg-subtle);
  padding: 1px 4px;
  border-radius: 3px;
}

.panel-desc {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 1px;
}

/* 端点模式切换 */
.endpoint-mode-box {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  margin-bottom: 16px;
}

.mode-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.mode-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.mode-radios {
  display: flex;
  align-items: center;
  gap: 8px;
}

.radio-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
  padding: 3px 9px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  cursor: pointer;
  background-color: var(--bg-app);
  transition: all 0.15s ease;
}

.radio-chip.selected {
  border-color: var(--primary);
  color: var(--text-primary);
  background-color: var(--bg-subtle);
  font-weight: 600;
}

.radio-chip input {
  accent-color: var(--primary);
  margin: 0;
}

.custom-endpoint-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-light);
}

.preset-badge-btn {
  font-size: 10px;
  color: #059669;
  background-color: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 3px;
  padding: 1px 6px;
  cursor: pointer;
}

.preset-badge-btn:hover {
  background-color: rgba(16, 185, 129, 0.18);
}

/* 推荐模型胶囊列表 */
.recommend-pills {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.rec-label {
  font-size: 10px;
  color: var(--text-faint);
}

.rec-pill {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-secondary);
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  padding: 1px 6px;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.rec-pill:hover {
  border-color: var(--primary);
  color: var(--primary);
}

/* 底部操作条 */
.actions-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  gap: 12px;
}

.actions-left,
.actions-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn {
  padding: 7px 14px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.btn-primary {
  background-color: var(--primary);
  color: var(--primary-text);
  border: 1px solid transparent;
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

@media (max-width: 860px) {
  .role-selector-pills {
    grid-template-columns: repeat(2, 1fr);
  }
  .form-layout {
    grid-template-columns: 1fr;
  }
  .actions-strip {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
