<template>
  <section class="history-panel">
    <div class="panel-head">
      <div>
        <div class="panel-eyebrow">运行历史</div>
        <h2 class="panel-title">任务运行记录</h2>
      </div>
      <div class="panel-actions">
        <a-button @click="$emit('open-compare')">运行对比</a-button>
        <a-button @click="$emit('refresh')">刷新</a-button>
      </div>
    </div>

    <TaskRunRecordTable
      :runs="runs"
      :columns="columns"
      :loading="loading"
      :scroll-x="1380"
      @open-report="$emit('open-report', $event)"
      @open-monitor="$emit('open-monitor')"
    />
  </section>
</template>

<script setup lang="ts">
import TaskRunRecordTable from '@/views/task/components/TaskRunRecordTable.vue'
import type { TableColumnType } from 'ant-design-vue'
import type { TaskRunHistoryItem } from '@/types/task'

defineProps<{
  runs: TaskRunHistoryItem[]
  loading: boolean
}>()

defineEmits<{
  (e: 'refresh'): void
  (e: 'open-compare'): void
  (e: 'open-report', runId: number): void
  (e: 'open-monitor'): void
}>()

const columns: TableColumnType<TaskRunHistoryItem>[] = [
  { title: '运行 ID', dataIndex: 'id', key: 'id', width: 130 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 110 },
  { title: '开始时间', dataIndex: 'started_at', key: 'started_at', width: 180 },
  { title: '结束时间', dataIndex: 'finished_at', key: 'finished_at', width: 180 },
  { title: '运行时长', dataIndex: 'runtime_seconds', key: 'runtime_seconds', width: 120 },
  { title: '总请求数', dataIndex: 'total_requests', key: 'total_requests', width: 120 },
  { title: '失败数', dataIndex: 'fail_count', key: 'fail_count', width: 100 },
  { title: '成功率', dataIndex: 'success_ratio', key: 'success_ratio', width: 100 },
  { title: '最近错误', dataIndex: 'latest_error', key: 'latest_error', ellipsis: true },
  { title: '操作', key: 'actions', width: 170, fixed: 'right' },
]
</script>

<style scoped>
.history-panel {
  padding: 22px;
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.06);
  overflow: hidden;
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

.panel-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
