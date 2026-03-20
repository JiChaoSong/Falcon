<template>
  <a-table
    row-key="id"
    :columns="columns"
    :data-source="runs"
    :pagination="false"
    :loading="loading"
    :scroll="scroll"
    :row-selection="rowSelection"
    :size="size"
    class="task-run-record-table"
  >
    <template #bodyCell="{ column, record, text }">
      <template v-if="column.key === 'status'">
        <a-tag class="status-tag" :color="getStatusColor(record.status)">
          {{ getStatusName(record.status) }}
        </a-tag>
      </template>
      <template v-else-if="column.key === 'started_at'">
        {{ formatDateTime(record.started_at) }}
      </template>
      <template v-else-if="column.key === 'finished_at'">
        {{ formatDateTime(record.finished_at) }}
      </template>
      <template v-else-if="column.key === 'runtime_seconds'">
        {{ formatRuntime(record.runtime_seconds) }}
      </template>
      <template v-else-if="column.key === 'success_ratio'">
        {{ formatPercent(record.success_ratio) }}
      </template>
      <template v-else-if="column.key === 'latest_error'">
        <span class="error-text" :title="text || '-'">{{ text || '-' }}</span>
      </template>
      <template v-else-if="column.key === 'actions'">
        <div class="table-actions">
          <a-button type="link" size="small" @click="$emit('open-report', record.id)">查看报告</a-button>
<!--          <a-button type="link" size="small" @click="$emit('open-monitor')">进入监控</a-button>-->
        </div>
      </template>
    </template>
  </a-table>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { STATE_COLORS, STATE_NAMES, STATE_UNKNOWN } from '@/layout/type'
import { formatDateTime, formatPercent } from '@/utils/tools'
import type { TableColumnType } from 'ant-design-vue'
import type { TaskRunHistoryItem } from '@/types/task'

type TableSize = 'small' | 'middle' | 'large'

const props = withDefaults(defineProps<{
  runs: TaskRunHistoryItem[]
  columns: TableColumnType<TaskRunHistoryItem>[]
  loading?: boolean
  scrollX?: number
  scrollY?: number
  size?: TableSize
  rowSelection?: Record<string, unknown>
}>(), {
  loading: false,
  scrollX: 1380,
  size: 'middle',
})

defineEmits<{
  (e: 'open-report', runId: number): void
  (e: 'open-monitor'): void
}>()

const scroll = computed(() => {
  if (props.scrollY) {
    return { x: props.scrollX, y: props.scrollY }
  }
  return { x: props.scrollX }
})

const getStatusName = (status: string) =>
  STATE_NAMES[(status in STATE_NAMES ? status : STATE_UNKNOWN) as keyof typeof STATE_NAMES] || status || '状态未知'

const getStatusColor = (status: string) =>
  STATE_COLORS[(status in STATE_COLORS ? status : STATE_UNKNOWN) as keyof typeof STATE_COLORS] || 'default'

const formatRuntime = (seconds: number | null | undefined) => {
  if (!seconds || seconds <= 0) {
    return '-'
  }

  if (seconds < 60) {
    return `${seconds}s`
  }

  const minutes = Math.floor(seconds / 60)
  const remainSeconds = seconds % 60
  if (minutes < 60) {
    return `${minutes}m ${remainSeconds}s`
  }

  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60
  return `${hours}h ${remainMinutes}m`
}
</script>

<style scoped>
.task-run-record-table {
  width: 100%;
}

.task-run-record-table :deep(.ant-table) {
  border-radius: 18px;
}

.task-run-record-table :deep(.ant-table-container) {
  overflow-x: auto;
}

.task-run-record-table :deep(.ant-table-content) {
  overflow-x: auto !important;
}

.task-run-record-table :deep(.ant-tag) {
  margin-inline-end: 0;
}

.status-tag {
  padding-inline: 10px;
  border-radius: 999px;
  font-weight: 700;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.error-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #b91c1c;
}
</style>
