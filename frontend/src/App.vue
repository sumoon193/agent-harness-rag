<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { healthCheck } from '@/api/client'
import type { HealthResponse } from '@/types'

const router = useRouter()
const route = useRoute()
const health = ref<HealthResponse | null>(null)
const healthFailed = ref(false)

const activePath = computed(() => (route.path.startsWith('/runs/') ? '/' : route.path))

const pageTitle = computed(() => {
  if (route.path.startsWith('/runs/')) return 'Run 审计详情'
  const titles: Record<string, string> = {
    '/': 'Agent 运行台',
    '/documents': '文档入库',
    '/eval': '评测看板',
  }
  return titles[route.path] ?? '控制台'
})

const apiModeLabel = computed(() => {
  if (healthFailed.value) return 'API unavailable'
  return health.value?.mode === 'full' ? 'Full API' : 'Fallback API'
})

const envMeta = computed(() => {
  if (!health.value) return ['HR V1', 'Checking']
  if (health.value.mode !== 'full') return ['HR V1', 'In-memory']

  const services = Object.values(health.value.services ?? {})
  const upCount = services.filter((service) => service.status === 'up').length
  return [`${upCount}/${services.length} services`, health.value.status === 'ok' ? 'Ready' : 'Degraded']
})

const envDotClass = computed(() => ({
  'env-dot--down': healthFailed.value || health.value?.status !== 'ok',
}))

onMounted(async () => {
  try {
    health.value = await healthCheck()
  } catch {
    healthFailed.value = true
  }
})

function handleSelect(path: string) {
  if (path !== route.path) {
    router.push(path)
  }
}
</script>

<template>
  <div class="app-shell">
    <aside class="workspace-rail">
      <div class="brand-block">
        <div class="brand-mark">
          <el-icon><Monitor /></el-icon>
        </div>
        <div class="brand-copy">
          <span>Agent Harness RAG</span>
          <strong>EnterpriseMind</strong>
        </div>
      </div>

      <el-menu
        :default-active="activePath"
        class="rail-menu"
        @select="handleSelect"
      >
        <el-menu-item index="/">
          <el-icon><ChatDotRound /></el-icon>
          <span>Agent 运行台</span>
        </el-menu-item>
        <el-menu-item index="/documents">
          <el-icon><Document /></el-icon>
          <span>文档入库</span>
        </el-menu-item>
        <el-menu-item index="/eval">
          <el-icon><DataAnalysis /></el-icon>
          <span>评测看板</span>
        </el-menu-item>
      </el-menu>

      <div class="rail-footer">
        <p class="rail-label">当前环境</p>
        <div class="env-line">
          <span class="env-dot" :class="envDotClass" />
          <span>{{ apiModeLabel }}</span>
        </div>
        <div class="env-meta">
          <span>{{ envMeta[0] }}</span>
          <span>{{ envMeta[1] }}</span>
        </div>
      </div>
    </aside>

    <section class="workspace">
      <header class="workspace-header">
        <div>
          <p class="workspace-kicker">Enterprise operations console</p>
          <h1>{{ pageTitle }}</h1>
        </div>

        <div class="status-strip" aria-label="系统状态">
          <div class="status-item">
            <span class="status-label">审批策略</span>
            <strong>Write gated</strong>
          </div>
          <div class="status-item">
            <span class="status-label">证据约束</span>
            <strong>Citations</strong>
          </div>
          <div class="status-item">
            <span class="status-label">权限边界</span>
            <strong>ACL first</strong>
          </div>
        </div>
      </header>

      <main class="app-main">
        <router-view />
      </main>
    </section>
  </div>
</template>
