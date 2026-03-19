<template>
  <div class="task-detail-page">
    <TaskDetailHeader
      :task-id="taskId"
      :task-info="taskInfo"
      :latest-run="latestRun"
      :start-loading="startLoading"
      @back="handleBack"
      @open-monitor="handleOpenMonitor"
      @start-task="handleStartTask"
    />

    <div class="detail-layout">
      <TaskStructurePanel class="structure-column" :scenarios="taskInfo?.scenarios || []" />

      <div class="detail-main">
        <TaskRunHistoryTable
          :runs="taskRuns"
          :loading="loading"
          @refresh="refreshPage"
          @open-compare="openCompareModal"
          @open-report="handleOpenReport"
          @open-monitor="handleOpenMonitor"
        />

        <TaskInsightPanel :compare-reports="compareReports" />
      </div>
    </div>

    <a-modal
      v-model:open="compareModalOpen"
      title="任务运行差异分析"
      width="1440px"
      :footer="null"
      destroy-on-close
      wrap-class-name="task-compare-modal"
    >
      <div class="compare-modal-layout">
        <div class="compare-modal-side">
          <div class="compare-side-head">
            <div class="compare-side-title">选择对比运行记录</div>
            <div class="compare-side-note">最多选择 2 次运行，左侧记录和主列表使用同一套表格组件，只按当前场景展示不同列。</div>
          </div>

          <TaskRunRecordTable
            :runs="taskRuns"
            :columns="compareColumns"
            size="small"
            :row-selection="compareRowSelection"
            :scroll-x="900"
            :scroll-y="620"
          />
        </div>

        <div class="compare-modal-main">
          <TaskRunComparePanel :compare-reports="compareReports" />
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { TaskApi } from '@/api/task'
import TaskDetailHeader from '@/views/task/components/TaskDetailHeader.vue'
import TaskStructurePanel from '@/views/task/components/TaskStructurePanel.vue'
import TaskRunHistoryTable from '@/views/task/components/TaskRunHistoryTable.vue'
import TaskRunRecordTable from '@/views/task/components/TaskRunRecordTable.vue'
import TaskRunComparePanel from '@/views/task/components/TaskRunComparePanel.vue'
import TaskInsightPanel from '@/views/task/components/TaskInsightPanel.vue'
import type { TaskInfo, TaskReportData, TaskRunHistoryItem } from '@/types/task'
import type { TableColumnType } from 'ant-design-vue'

const route = useRoute()
const router = useRouter()

const taskId = ref<number>(Number(route.params.taskId) || 0)
const loading = ref(false)
const startLoading = ref(false)
const compareModalOpen = ref(false)
const taskInfo = ref<TaskInfo | null>(null)
const taskRuns = ref<TaskRunHistoryItem[]>([])
const selectedRunIds = ref<number[]>([])
const compareReports = ref<TaskReportData[]>([])

const latestRun = computed(() => taskRuns.value[0] || null)

const compareColumns: TableColumnType<TaskRunHistoryItem>[] = [
  { title: '运行 ID', dataIndex: 'id', key: 'id', width: 90, fixed: 'left' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 110 },
  { title: '开始时间', dataIndex: 'started_at', key: 'started_at', width: 178 },
  { title: '运行时长', dataIndex: 'runtime_seconds', key: 'runtime_seconds', width: 120 },
  { title: '失败数', dataIndex: 'fail_count', key: 'fail_count', width: 100 },
  { title: '成功率', dataIndex: 'success_ratio', key: 'success_ratio', width: 100 },
  { title: '最近错误', dataIndex: 'latest_error', key: 'latest_error', width: 300 },
]

const compareRowSelection = computed(() => ({
  selectedRowKeys: selectedRunIds.value,
  onChange: (selectedRowKeys: Array<string | number>) => {
    void handleCompareSelection(selectedRowKeys.map(item => Number(item)).slice(0, 2))
  },
  getCheckboxProps: (record: TaskRunHistoryItem) => ({
    disabled: selectedRunIds.value.length >= 2 && !selectedRunIds.value.includes(record.id),
  }),
}))

const fetchTaskInfo = async () => {
  const response = await TaskApi.getTaskInfo({ id: taskId.value })
  taskInfo.value = response.data
}

const fetchTaskRuns = async () => {
  const response = await TaskApi.getTaskRuns({ task_id: taskId.value })
  taskRuns.value = response.data.runs || []
}

const refreshCompareReports = async () => {
  if (selectedRunIds.value.length !== 2) {
    compareReports.value = []
    return
  }

  const reports = await Promise.all(
    selectedRunIds.value.map(runId => TaskApi.getTaskReport({ task_id: taskId.value, task_run_id: runId }))
  )
  compareReports.value = reports.map(item => item.data)
}

const refreshPage = async () => {
  if (!taskId.value) {
    return
  }

  loading.value = true
  try {
    await Promise.all([fetchTaskInfo(), fetchTaskRuns()])
    await refreshCompareReports()
  } catch (error) {
    console.error('加载任务详情失败:', error)
    message.error('加载任务详情失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

const handleCompareSelection = async (value: number[]) => {
  selectedRunIds.value = value
  try {
    await refreshCompareReports()
  } catch (error) {
    console.error('加载对比报告失败:', error)
    message.error('加载对比报告失败，请稍后重试。')
  }
}

const openCompareModal = () => {
  compareModalOpen.value = true
}

const handleBack = () => {
  router.push('/task')
}

const handleOpenMonitor = () => {
  router.push(`/monitor/${taskId.value}`)
}

const handleOpenReport = (runId: number) => {
  router.push({
    path: `/report/${taskId.value}`,
    query: runId ? { taskRunId: String(runId) } : undefined,
  })
}

const handleStartTask = async () => {
  startLoading.value = true
  try {
    await TaskApi.runTask({ task_id: taskId.value })
    message.success('任务已启动，正在跳转到监控页面。')
    router.push(`/monitor/${taskId.value}`)
  } catch (error) {
    console.error('启动任务失败:', error)
    message.error('启动任务失败，请稍后重试。')
  } finally {
    startLoading.value = false
  }
}

watch(
  () => route.params.taskId,
  async value => {
    taskId.value = Number(value) || 0
    selectedRunIds.value = []
    compareReports.value = []
    compareModalOpen.value = false
    await refreshPage()
  }
)

onMounted(async () => {
  await refreshPage()
})
</script>

<style scoped>
.task-detail-page {
  min-height: 100vh;
  padding: 28px;
  background:
    radial-gradient(circle at top left, rgba(219, 234, 254, 0.4), transparent 24%),
    linear-gradient(180deg, #f8fbff 0%, #f3f7fb 100%);
}

.detail-layout {
  grid-template-columns: 560px minmax(0, 1fr);
  gap: 20px;
  margin-top: 20px;
  align-items: start;
}

.structure-column {
  position: sticky;
  margin: 20px 0;
}

.detail-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.compare-modal-layout {
  display: grid;
  grid-template-columns: 460px minmax(0, 1fr);
  gap: 20px;
  min-height: 680px;
}

.compare-modal-side,
.compare-modal-main {
  min-width: 0;
}

.compare-modal-side {
  display: flex;
  flex-direction: column;
  min-height: 680px;
}

.compare-side-head {
  margin-bottom: 12px;
}

.compare-side-title {
  color: #0f172a;
  font-size: 16px;
  font-weight: 700;
}

.compare-side-note {
  margin-top: 4px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
}
</style>
