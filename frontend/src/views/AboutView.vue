<template>
  <div class="about-container">
    <div class="about-card">
      <div class="about-header">
        <h2>系统状态与服务信息</h2>
        <button class="btn btn-secondary btn-sm" @click="fetchData" :disabled="loading">
          {{ loading ? '刷新中...' : '刷新状态' }}
        </button>
      </div>

      <!-- 服务状态概览 -->
      <section class="section">
        <h3>服务健康状态</h3>
        <div v-if="health" class="info-grid">
          <div class="info-item">
            <span class="label">服务名称</span>
            <span class="value">{{ health.app }}</span>
          </div>
          <div class="info-item">
            <span class="label">运行环境</span>
            <span class="value badge">{{ health.env }}</span>
          </div>
          <div class="info-item">
            <span class="label">健康状态</span>
            <span :class="['value', 'status-tag', health.status]">
              {{ health.status === 'healthy' ? '正常 (Healthy)' : '降级 (Degraded)' }}
            </span>
          </div>
          <div class="info-item">
            <span class="label">LLM API Key</span>
            <span :class="['value', health.llm_configured ? 'text-success' : 'text-warning']">
              {{ health.llm_configured ? '已配置' : '未配置 (需在设置中填写)' }}
            </span>
          </div>
          <div class="info-item">
            <span class="label">预置模型</span>
            <span class="value"><code>{{ health.llm_model }}</code></span>
          </div>
          <div class="info-item">
            <span class="label">已挂载工具</span>
            <span class="value">{{ health.tools_count }} 个</span>
          </div>
        </div>
        <div v-else-if="error" class="error-box">
          无法连接到后端服务: {{ error }}
        </div>
      </section>

      <!-- 就绪测试探针 -->
      <section class="section">
        <h3>运行时就绪探针 (/health/ready)</h3>
        <div class="ready-panel">
          <button class="btn btn-primary btn-sm" @click="testReady" :disabled="testingReady">
            {{ testingReady ? '检测中...' : '触发就绪探针' }}
          </button>
          <span v-if="readyResult" :class="['ready-msg', readyResult.ready ? 'text-success' : 'text-danger']">
            {{ readyResult.message }}
          </span>
        </div>
      </section>

      <!-- 注册工具一览 -->
      <section class="section">
        <h3>已注册智能体工具列表</h3>
        <div v-if="tools.length > 0" class="tool-list">
          <div v-for="t in tools" :key="t.name" class="tool-card">
            <div class="tool-card-head">
              <span class="tool-badge">Tool</span>
              <strong>{{ t.name }}</strong>
            </div>
            <p class="tool-desc">{{ t.description }}</p>
            <div class="tool-schema">
              <span class="schema-label">参数约束:</span>
              <pre>{{ JSON.stringify(t.parameters, null, 2) }}</pre>
            </div>
          </div>
        </div>
        <div v-else class="empty-text">暂无挂载的工具</div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getHealth, getTools, getReady, HealthData, ToolInfo, ReadyData } from '@/api/chat'

const health = ref<HealthData | null>(null)
const tools = ref<ToolInfo[]>([])
const readyResult = ref<ReadyData | null>(null)
const loading = ref(false)
const testingReady = ref(false)
const error = ref<string | null>(null)

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const [h, t] = await Promise.all([getHealth(), getTools()])
    health.value = h
    tools.value = t
  } catch (err: any) {
    error.value = err.message || '获取数据失败'
  } finally {
    loading.value = false
  }
}

async function testReady() {
  testingReady.value = true
  try {
    readyResult.value = await getReady()
  } catch (err: any) {
    readyResult.value = { ready: false, message: err.message }
  } finally {
    testingReady.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.about-container {
  padding: 32px 24px;
  overflow-y: auto;
  height: 100%;
  display: flex;
  justify-content: center;
}

.about-card {
  max-width: 860px;
  width: 100%;
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  padding: 32px;
  box-shadow: var(--shadow-sm);
}

.about-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 16px;
  margin-bottom: 24px;
}

.about-header h2 {
  font-size: 20px;
  color: #0f172a;
}

.section {
  margin-bottom: 32px;
}

.section h3 {
  font-size: 16px;
  color: #334155;
  margin-bottom: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: var(--radius-md);
  border: 1px solid #f1f5f9;
}

.info-item .label {
  color: #64748b;
  font-size: 14px;
}

.info-item .value {
  font-weight: 500;
  font-size: 14px;
}

.text-success {
  color: var(--success-color);
}

.text-warning {
  color: var(--warning-color);
}

.text-danger {
  color: var(--danger-color);
}

.badge {
  background: #e2e8f0;
  padding: 2px 8px;
  border-radius: 4px;
}

.ready-panel {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #f8fafc;
  padding: 16px;
  border-radius: var(--radius-md);
}

.ready-msg {
  font-size: 14px;
  font-weight: 500;
}

.tool-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tool-card {
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-md);
  padding: 16px;
  background: #fafbfc;
}

.tool-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.tool-badge {
  background: #dbeafe;
  color: #1e40af;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.tool-desc {
  font-size: 13px;
  color: #475569;
  margin-bottom: 12px;
}

.tool-schema {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px 12px;
}

.schema-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
}

.tool-schema pre {
  font-size: 12px;
  color: #334155;
  margin-top: 4px;
  overflow-x: auto;
}

.error-box {
  background: #fef2f2;
  color: #b91c1c;
  padding: 12px;
  border-radius: var(--radius-md);
  font-size: 14px;
}

.empty-text {
  color: #94a3b8;
  font-size: 14px;
}

.btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
}
</style>
