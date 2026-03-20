<template>
  <section class="insight-panel">
    <div class="panel-head">
      <div>
        <div class="panel-eyebrow">分析结论</div>
        <h2 class="panel-title">规则版 AI 洞察</h2>
      </div>
      <span class="panel-tag" :class="insightTone">{{ insightLevel }}</span>
    </div>

    <div class="insight-content">
      <article class="insight-card insight-card-primary">
        <h3>总体结论</h3>
        <p>{{ overviewText }}</p>
      </article>
      <article class="insight-card">
        <h3>关键变化</h3>
        <ul class="insight-list">
          <li v-for="item in changeItems" :key="item">{{ item }}</li>
        </ul>
      </article>
      <article class="insight-card">
        <h3>建议动作</h3>
        <ul class="insight-list">
          <li v-for="item in actionItems" :key="item">{{ item }}</li>
        </ul>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatNumber, formatPercent } from '@/utils/tools'
import type { TaskReportData } from '@/types/task'

const props = defineProps<{
  compareReports: TaskReportData[]
}>()

const hasCompare = computed(() => props.compareReports.length === 2)
const currentReport = computed(() => props.compareReports[0] || null)
const previousReport = computed(() => props.compareReports[1] || null)

const failDelta = computed(() => (currentReport.value && previousReport.value ? currentReport.value.fail_count - previousReport.value.fail_count : 0))
const p95Delta = computed(() => (currentReport.value && previousReport.value ? currentReport.value.p95 - previousReport.value.p95 : 0))
const successDelta = computed(() => (currentReport.value && previousReport.value ? currentReport.value.success_ratio - previousReport.value.success_ratio : 0))

const insightLevel = computed(() => {
  if (!hasCompare.value) {
    return '等待对比'
  }
  if (failDelta.value > 0 || p95Delta.value > 100 || successDelta.value < -0.01) {
    return '需要关注'
  }
  if (failDelta.value <= 0 && p95Delta.value <= 0 && successDelta.value >= 0) {
    return '整体改善'
  }
  return '基本稳定'
})

const insightTone = computed(() => {
  if (insightLevel.value === '需要关注') {
    return 'danger'
  }
  if (insightLevel.value === '整体改善') {
    return 'success'
  }
  return 'default'
})

const overviewText = computed(() => {
  if (!hasCompare.value || !currentReport.value || !previousReport.value) {
    return '当前已经具备任务详情、执行历史和运行对比能力。接下来最适合继续沉淀规则分析，再逐步扩展成模型化总结。'
  }

  if (insightLevel.value === '需要关注') {
    return `本次运行相较对比运行出现明显波动。成功率变化 ${formatPercent(successDelta.value)}，P95 变化 ${formatNumber(p95Delta.value)} ms，建议优先检查失败接口和风险接口。`
  }

  if (insightLevel.value === '整体改善') {
    return `本次运行整体优于对比运行。成功率提升 ${formatPercent(successDelta.value)}，P95 下降 ${formatNumber(Math.abs(p95Delta.value))} ms，可以作为新的基线候选。`
  }

  return `本次运行整体接近对比运行。成功率变化 ${formatPercent(successDelta.value)}，P95 变化 ${formatNumber(p95Delta.value)} ms，建议继续关注接口级细节。`
})

const changeItems = computed(() => {
  if (!hasCompare.value || !currentReport.value || !previousReport.value) {
    return [
      '先选择两次运行，系统会自动生成关键指标变化摘要。',
      '推荐优先比较成功率、P95 和风险接口。',
      '后续可以继续叠加热点接口和错误样本分析。',
    ]
  }

  return [
    `成功率从 ${formatPercent(previousReport.value.success_ratio)} 变化到 ${formatPercent(currentReport.value.success_ratio)}。`,
    `P95 从 ${formatNumber(previousReport.value.p95)} ms 变化到 ${formatNumber(currentReport.value.p95)} ms。`,
    `失败数从 ${previousReport.value.fail_count} 变化到 ${currentReport.value.fail_count}。`,
    `热点接口 ${currentReport.value.hottest_endpoint?.name || '暂无'}，风险接口 ${currentReport.value.riskiest_endpoint?.name || '暂无'}。`,
  ]
})

const actionItems = computed(() => {
  if (!hasCompare.value || !currentReport.value || !previousReport.value) {
    return [
      '先从执行历史中选择两次运行，建立对比上下文。',
      '优先查看同一任务在相近配置下的两次运行。',
      '如果要做 AI 分析，建议后续补接口级聚合和错误样本摘要。',
    ]
  }

  const actions = []

  if (currentReport.value.fail_count > previousReport.value.fail_count) {
    actions.push('失败数上升，先查看风险接口和最近错误。')
  }
  if (currentReport.value.p95 > previousReport.value.p95) {
    actions.push('P95 恶化，优先排查热点接口的下游依赖或资源瓶颈。')
  }
  if ((currentReport.value.hottest_endpoint?.name || '') !== (previousReport.value.hottest_endpoint?.name || '')) {
    actions.push('热点接口发生变化，建议确认流量分布或场景编排是否调整。')
  }
  if (currentReport.value.latest_error) {
    actions.push(`可先根据最近错误继续排查：${currentReport.value.latest_error}`)
  }

  if (!actions.length) {
    actions.push('本次运行没有明显恶化，可将本次结果作为基线候选继续观察。')
  }

  return actions
})
</script>

<style scoped>
.insight-panel {
  padding: 22px;
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.06);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #64748b;
}

.panel-title {
  margin: 8px 0 0;
  font-size: 22px;
  color: #0f172a;
}

.panel-tag {
  display: inline-flex;
  align-items: center;
  height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.panel-tag.success {
  background: #dcfce7;
  color: #166534;
}

.panel-tag.danger {
  background: #fee2e2;
  color: #b91c1c;
}

.insight-content {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.insight-card {
  min-height: 188px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(248, 250, 252, 0.96);
}

.insight-card-primary {
  background:
    radial-gradient(circle at top right, rgba(239, 246, 255, 0.8), transparent 34%),
    rgba(248, 250, 252, 0.96);
}

.insight-card h3 {
  margin: 0 0 10px;
  color: #0f172a;
  font-size: 16px;
}

.insight-card p {
  margin: 0;
  color: #475569;
  line-height: 1.8;
}

.insight-list {
  margin: 0;
  padding-left: 18px;
  color: #475569;
  line-height: 1.8;
}
</style>
