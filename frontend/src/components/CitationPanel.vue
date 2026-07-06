<!--
  CitationPanel 组件：结构化展示证据来源。
-->
<script setup lang="ts">
interface Citation {
  id?: number
  document_name?: string
  section?: string
  page?: number
  chunk_text?: string
  score?: number
  rerank_score?: number
}

defineProps<{
  citations: Citation[]
}>()
</script>

<template>
  <div v-if="citations.length > 0" class="citation-panel" data-testid="citation-panel">
    <header class="panel-title">
      <span>
        <el-icon><DocumentCopy /></el-icon>
        引用来源
      </span>
      <b>{{ citations.length }}</b>
    </header>

    <div class="citation-list">
      <article
        v-for="(citation, idx) in citations"
        :key="idx"
        class="citation-item"
      >
        <div class="citation-index">[{{ citation.id ?? idx + 1 }}]</div>
        <div class="citation-content">
          <div class="citation-header">
            <strong>{{ citation.document_name ?? '未知文档' }}</strong>
            <span v-if="citation.section">{{ citation.section }}</span>
            <span v-if="citation.page">第{{ citation.page }}页</span>
          </div>
          <p v-if="citation.chunk_text" class="chunk-text">{{ citation.chunk_text }}</p>
          <div class="scores">
            <span v-if="citation.score != null">检索 {{ citation.score.toFixed(2) }}</span>
            <span v-if="citation.rerank_score != null">重排 {{ citation.rerank_score.toFixed(2) }}</span>
          </div>
        </div>
      </article>
    </div>
  </div>
  <el-empty v-else description="暂无引用" :image-size="60" />
</template>

<style scoped>
.citation-panel {
  display: grid;
  gap: 12px;
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--color-text);
  font-size: 14px;
  font-weight: 800;
}

.panel-title span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.panel-title b {
  padding: 2px 8px;
  border-radius: 999px;
  color: var(--color-primary-strong);
  background: var(--color-green-soft);
  font-size: 12px;
}

.citation-list {
  display: grid;
  gap: 10px;
}

.citation-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: #ffffff;
}

.citation-index {
  color: var(--color-primary);
  font-weight: 800;
  font-size: 12px;
}

.citation-content {
  min-width: 0;
}

.citation-header {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  align-items: center;
  margin-bottom: 8px;
}

.citation-header strong {
  color: var(--color-text);
  font-size: 13px;
}

.citation-header span {
  color: var(--color-muted);
  font-size: 12px;
}

.chunk-text {
  margin: 0;
  padding: 9px 10px;
  border-left: 3px solid var(--color-primary);
  border-radius: var(--radius-sm);
  background: var(--color-panel-muted);
  color: #394556;
  font-size: 13px;
  line-height: 1.55;
}

.scores {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.scores span {
  padding: 3px 7px;
  border-radius: 999px;
  color: var(--color-muted);
  background: #edf2f6;
  font-size: 11px;
}
</style>
