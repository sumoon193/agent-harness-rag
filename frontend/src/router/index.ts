/**
 * 路由配置。
 *
 * Case 运维台是主页面，单轮 Agent Run 保留为兼容视图。
 */
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Cases',
      component: () => import('@/views/CaseConsole.vue'),
    },
    {
      path: '/runs',
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
