<template>
  <section class="detail-hero">
    <div class="hero-copy">
      <div class="hero-eyebrow">任务详情</div>
      <div class="title-row">
        <h1 class="hero-title">{{ taskInfo?.name || `任务 ${taskId}` }}</h1>
        <span class="status-chip">{{ statusLabel }}</span>
      </div>
      <p class="hero-desc">
        {{ taskInfo?.description || '查看任务定义、场景与用例、执行历史，以及任务的多次运行结果。' }}
      </p>

      <div class="hero-tags">
        <span class="hero-tag">{{ taskInfo?.project || '未关联项目' }}</span>
        <span class="hero-tag">{{ taskInfo?.execution_strategy || '未设置执行策略' }}</span>
        <span class="hero-tag hero-tag-host" :title="taskInfo?.host || '-'">{{ taskInfo?.host || '未设置目标主机' }}</span>
        <span class="hero-tag">最近运行 {{ latestRunTime }}</span>
      </div>
    </div>

    <div class="hero-actions">
      <a-button @click="$emit('back')">返回列表</a-button>
      <a-button @click="$emit('open-monitor')">进入监控</a-button>
      <a-button type="primary" :loading="startLoading" @click="$emit('start-task')">开始任务</a-button>
    </div>
  </section>

  <section class="hero-metrics">
    <div class="metric-card">
      <span class="metric-label">目标主机</span>
        <a-tooltip :title="taskInfo?.host || '-' ">
          <strong class="metric-value metric-host" :title="taskInfo?.host || '-'">{{ taskInfo?.host || '-' }}</strong>
        </a-tooltip>
      <span class="metric-foot">当前任务的默认请求入口</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">默认并发</span>
      <strong class="metric-value">{{ taskInfo?.users ?? 0 }}</strong>
      <span class="metric-foot">任务启动后的虚拟用户规模</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">加压速度</span>
      <strong class="metric-value">{{ taskInfo?.spawn_rate ?? 0 }}/s</strong>
      <span class="metric-foot">每秒新增虚拟用户数量</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">持续时长</span>
      <strong class="metric-value">{{ durationText }}</strong>
      <span class="metric-foot">任务默认执行时长</span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { STATE_NAMES } from '@/layout/type'
import { formatDateTime } from '@/utils/tools'
import type { TaskInfo, TaskRunHistoryItem } from '@/types/task'

const props = defineProps<{
  taskId: number
  taskInfo: TaskInfo | null
  latestRun: TaskRunHistoryItem | null
  startLoading: boolean
}>()

defineEmits<{
  (e: 'back'): void
  (e: 'open-monitor'): void
  (e: 'start-task'): void
}>()

const statusLabel = computed(() => {
  const status = (props.taskInfo?.status || 'pending') as keyof typeof STATE_NAMES
  return STATE_NAMES[status] || '状态未知'
})

const latestRunTime = computed(() => {
  if (!props.latestRun?.started_at) {
    return '暂无'
  }
  return formatDateTime(props.latestRun.started_at)
})

const durationText = computed(() => {
  if (!props.taskInfo?.duration) {
    return '不限时'
  }
  return `${props.taskInfo.duration}s`
})
</script>

<style scoped>
.detail-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 30px;
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background:
    radial-gradient(circle at top right, rgba(191, 219, 254, 0.62), transparent 34%),
    linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  box-shadow: 0 22px 48px rgba(15, 23, 42, 0.08);
}

.hero-copy {
  flex: 1;
  min-width: 0;
}

.hero-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #64748b;
}

.title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
}

.hero-title {
  margin: 0;
  font-size: 32px;
  line-height: 1.12;
  color: #0f172a;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(219, 234, 254, 0.9);
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 700;
}

.hero-desc {
  max-width: 760px;
  margin: 12px 0 0;
  color: #64748b;
  line-height: 1.7;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.hero-tag {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  font-size: 13px;
}

.hero-tag-host {
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 132px;
  padding: 22px 24px;
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.06);
}

.metric-label {
  color: #64748b;
  font-size: 13px;
}

.metric-value {
  color: #0f172a;
  font-size: 26px;
  line-height: 1.2;
}

.metric-host {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metric-foot {
  color: #94a3b8;
  font-size: 12px;
}
</style>
