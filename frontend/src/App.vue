<template>
  <div class="spa-layout">
    <!-- 左侧极简现代侧边栏 -->
    <aside class="sidebar">
      <!-- 品牌标识区 -->
      <div class="sidebar-header">
        <div class="brand-mark">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <div class="brand-text">
          <span class="brand-name">qtllmwiki</span>
          <span class="brand-version">v0.1.0</span>
        </div>
      </div>

      <!-- 核心导航模块 -->
      <nav class="nav-menu">
        <div class="menu-group-label">WORKSPACE</div>

        <RouterLink to="/chat" class="menu-item" active-class="active">
          <svg class="menu-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span class="menu-label">智能问答</span>
        </RouterLink>

        <RouterLink to="/files" class="menu-item" active-class="active">
          <svg class="menu-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
          <span class="menu-label">文件管理</span>
        </RouterLink>

        <RouterLink to="/settings" class="menu-item" active-class="active">
          <svg class="menu-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <span class="menu-label">模型设置</span>
        </RouterLink>
      </nav>

      <!-- 侧边栏底部状态与文档链接 -->
      <div class="sidebar-footer">
        <div class="status-indicator">
          <span class="pulse-dot"></span>
          <span class="status-text">FastAPI Online</span>
        </div>

        <a href="http://127.0.0.1:8000/docs" target="_blank" class="footer-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span>API Reference</span>
          <svg class="ext-svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="7" y1="17" x2="17" y2="7" />
            <polyline points="7 7 17 7 17 17" />
          </svg>
        </a>
      </div>
    </aside>

    <!-- 右侧内容主视口 -->
    <main class="main-viewport">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<style scoped>
.spa-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: var(--bg-app);
}

/* 侧边栏 */
.sidebar {
  width: 220px;
  background-color: var(--bg-surface);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  user-select: none;
}

.sidebar-header {
  height: 54px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--border-light);
}

.brand-mark {
  width: 30px;
  height: 30px;
  background-color: var(--primary);
  color: var(--primary-text);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.brand-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.2px;
}

.brand-version {
  font-size: 11px;
  color: var(--text-faint);
  font-family: var(--font-mono);
}

.nav-menu {
  flex: 1;
  padding: 16px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-group-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-faint);
  letter-spacing: 0.05em;
  padding: 6px 10px 4px 10px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
  text-decoration: none;
}

.menu-item:hover {
  background-color: var(--bg-subtle);
  color: var(--text-primary);
}

.menu-item.active {
  background-color: var(--primary-subtle);
  color: var(--primary);
  font-weight: 600;
}

.menu-svg {
  flex-shrink: 0;
  color: var(--text-muted);
}

.menu-item.active .menu-svg {
  color: var(--primary);
}

.sidebar-footer {
  padding: 12px 14px;
  border-top: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 4px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--success);
}

.status-text {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.footer-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-muted);
  text-decoration: none;
  transition: all 0.15s ease;
}

.footer-link:hover {
  background-color: var(--bg-subtle);
  color: var(--text-primary);
}

.ext-svg {
  margin-left: auto;
  opacity: 0.6;
}

/* 主视口 */
.main-viewport {
  flex: 1;
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg-app);
}
</style>
