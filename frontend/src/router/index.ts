/**
 * 路由配置。
 *
 * 4 个路由：AgentConsole（主页面）、DocumentUpload、EvalResult、RunDetail。
 */
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'AgentConsole',
      component: () => import('@/views/AgentConsole.vue'),
    },
    {
      path: '/documents',
      name: 'Documents',
      component: () => import('@/views/DocumentUpload.vue'),
    },
    {
      path: '/eval',
      name: 'Eval',
      component: () => import('@/views/EvalResult.vue'),
    },
    {
      path: '/runs/:id',
      name: 'RunDetail',
      component: () => import('@/views/RunDetail.vue'),
    },
  ],
})

export default router
