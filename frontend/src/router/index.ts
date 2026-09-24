import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import FileManagerView from '../views/FileManagerView.vue'
import SettingsView from '../views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/chat',
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
      meta: { title: '智能问答' },
    },
    {
      path: '/files',
      name: 'files',
      component: FileManagerView,
      meta: { title: '文件管理' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { title: '设置' },
    },
  ],
})

export default router
