<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { EditOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useRoute, useRouter } from 'vue-router'
import { WorkerApi } from '@/api/worker'
import type { WorkerInfo, WorkerListQuery, WorkerStatus, WorkerUpdatePayload } from '@/types/worker'
import { formatDateTime } from '@/utils/tools'

type WorkerFormState = {
  status: WorkerStatus
  capacity: number
  scheduling_weight: number
  tagsText: string
  metadataText: string
}

const loading = ref(false)
const drawerVisible = ref(false)
const submitting = ref(false)
const currentWorkerId = ref('')
const route = useRoute()
const router = useRouter()

const statusOptions: Array<{ label: string; value: WorkerStatus }> = [
  { label: '在线', value: 'online' },
  { label: '忙碌', value: 'busy' },
  { label: '降级', value: 'degraded' },
  { label: '离线', value: 'offline' },
  { label: '已禁用', value: 'disabled' },
]

const state = reactive({
  workers: [] as WorkerInfo[],
  total: 0,
  query: {
    page: 1,
    page_size: 10,
    worker_id: '',
    status: undefined as WorkerStatus | undefined,
    tag: '',
  } as WorkerListQuery,
  formData: {
    status: 'online',
    capacity: 1,
    scheduling_weight: 100,
    tagsText: '',
    metadataText: '{}',
  } as WorkerFormState,
})

const columns = [
  { title: '节点 ID', dataIndex: 'worker_id', key: 'worker_id', width: 180 },
  { title: '节点地址', dataIndex: 'address', key: 'address' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '负载', key: 'load', width: 120 },
  { title: '标签', dataIndex: 'tags', key: 'tags', width: 220 },
  { title: '版本', dataIndex: 'version', key: 'version', width: 120 },
  { title: '最近心跳', dataIndex: 'last_heartbeat_at', key: 'last_heartbeat_at', width: 180 },
  { title: '最近错误', dataIndex: 'last_seen_error', key: 'last_seen_error' },
]

const paginationTotal = computed(() => state.total || 0)

const statusColorMap: Record<WorkerStatus, string> = {
  online: 'green',
  busy: 'blue',
  degraded: 'orange',
  offline: 'default',
  disabled: 'red',
}

const statusLabelMap: Record<WorkerStatus, string> = {
  online: '在线',
  busy: '忙碌',
  degraded: '降级',
  offline: '离线',
  disabled: '已禁用',
}

const fetchWorkers = async () => {
  loading.value = true
  try {
    const response = await WorkerApi.workerList({
      ...state.query,
      worker_id: state.query.worker_id || undefined,
      tag: state.query.tag || undefined,
    })
    state.workers = response.data?.results || []
    state.total = response.data?.total || 0
  } finally {
    loading.value = false
  }
}

const syncRouteQuery = () => {
  router.replace({
    path: route.path,
    query: {
      ...route.query,
      tab: 'workers',
      workerStatus: state.query.status,
      workerId: state.query.worker_id || undefined,
      workerTag: state.query.tag || undefined,
      workerPage: String(state.query.page),
    },
  })
}

const resetFilters = async () => {
  state.query = {
    page: 1,
    page_size: 10,
    worker_id: '',
    status: undefined,
    tag: '',
  }
  syncRouteQuery()
  await fetchWorkers()
}

const openEditDrawer = (worker: WorkerInfo) => {
  currentWorkerId.value = worker.worker_id
  state.formData = {
    status: worker.status,
    capacity: worker.capacity,
    scheduling_weight: worker.scheduling_weight,
    tagsText: (worker.tags || []).join(', '),
    metadataText: JSON.stringify(worker.metadata_json || {}, null, 2),
  }
  drawerVisible.value = true
}

const buildUpdatePayload = (): WorkerUpdatePayload => {
  let metadata_json: Record<string, unknown> | undefined
  const trimmedMetadata = state.formData.metadataText.trim()
  if (trimmedMetadata) {
    try {
      metadata_json = JSON.parse(trimmedMetadata) as Record<string, unknown>
    } catch {
      throw new Error('元数据必须是合法的 JSON。')
    }
  }

  return {
    worker_id: currentWorkerId.value,
    status: state.formData.status,
    capacity: Number(state.formData.capacity),
    scheduling_weight: Number(state.formData.scheduling_weight),
    tags: state.formData.tagsText
      .split(',')
      .map(item => item.trim())
      .filter(Boolean),
    metadata_json,
  }
}

const submitWorkerUpdate = async () => {
  if (!currentWorkerId.value) {
    return
  }
  submitting.value = true
  try {
    const payload = buildUpdatePayload()
    await WorkerApi.updateWorker(payload)
    message.success('节点更新成功。')
    drawerVisible.value = false
    await fetchWorkers()
  } catch (error) {
    if (error instanceof Error) {
      message.error(error.message)
    } else {
      message.error('节点更新失败。')
    }
  } finally {
    submitting.value = false
  }
}

const onTableChange = async (page: number, pageSize: number) => {
  state.query.page = page
  state.query.page_size = pageSize
  syncRouteQuery()
  await fetchWorkers()
}

onMounted(() => {
  const queryStatus = route.query.workerStatus as WorkerStatus | undefined
  const queryWorkerId = route.query.workerId as string | undefined
  const queryTag = route.query.workerTag as string | undefined
  const queryPage = Number(route.query.workerPage || 1)

  if (queryStatus && ['online', 'busy', 'degraded', 'offline', 'disabled'].includes(queryStatus)) {
    state.query.status = queryStatus
  }
  if (queryWorkerId) {
    state.query.worker_id = queryWorkerId
  }
  if (queryTag) {
    state.query.tag = queryTag
  }
  if (Number.isFinite(queryPage) && queryPage > 0) {
    state.query.page = queryPage
  }

  fetchWorkers()
})
</script>

<template>
  <div class="worker-management">

    <a-card title="节点列表">
      <a-table
        :columns="columns"
        :data-source="state.workers"
        :loading="loading"
        :pagination="false"
        :scroll="{ x: 1280 }"
        row-key="worker_id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-space>
              <a-badge :status="record.is_timeout ? 'error' : 'processing'" />
              <a-tag :color="statusColorMap[record.status]">
                {{ statusLabelMap[record.status] }}
              </a-tag>
            </a-space>
          </template>

          <template v-else-if="column.key === 'load'">
            {{ record.running_tasks }} / {{ record.capacity }}
          </template>

          <template v-else-if="column.key === 'tags'">
            <a-space wrap>
              <a-tag v-for="tag in record.tags || []" :key="tag">
                {{ tag }}
              </a-tag>
              <span v-if="!(record.tags || []).length">-</span>
            </a-space>
          </template>

          <template v-else-if="column.key === 'last_heartbeat_at'">
            {{ formatDateTime(record.last_heartbeat_at) }}
          </template>

          <template v-else-if="column.key === 'last_seen_error'">
            <span class="error-text">{{ record.last_seen_error || '-' }}</span>
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-button type="link" @click="openEditDrawer(record)">
              <template #icon><EditOutlined /></template>
              编辑
            </a-button>
          </template>
        </template>
      </a-table>

      <div class="pagination">
        <a-pagination
          v-model:current="state.query.page"
          v-model:pageSize="state.query.page_size"
          :total="paginationTotal"
          show-size-changer
          @change="onTableChange"
        />
      </div>
    </a-card>

    <a-drawer
      title="编辑节点"
      :open="drawerVisible"
      width="520"
      @close="drawerVisible = false"
    >
      <a-form :model="state.formData" layout="vertical">
        <a-form-item label="节点 ID">
          <a-input :value="currentWorkerId" disabled />
        </a-form-item>

        <a-form-item label="状态">
          <a-select v-model:value="state.formData.status">
            <a-select-option
              v-for="option in statusOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="容量">
          <a-input-number v-model:value="state.formData.capacity" :min="1" style="width: 100%" />
        </a-form-item>

        <a-form-item label="调度权重">
          <a-input-number
            v-model:value="state.formData.scheduling_weight"
            :min="1"
            style="width: 100%"
          />
        </a-form-item>

        <a-form-item label="标签">
          <a-input
            v-model:value="state.formData.tagsText"
            placeholder="多个标签用逗号分隔，例如 local,smoke"
          />
        </a-form-item>

        <a-form-item label="元数据 JSON">
          <a-textarea
            v-model:value="state.formData.metadataText"
            :auto-size="{ minRows: 6, maxRows: 12 }"
            placeholder="{&quot;zone&quot;:&quot;local&quot;}"
          />
        </a-form-item>
      </a-form>

      <template #footer>
        <a-space>
          <a-button @click="drawerVisible = false">取消</a-button>
          <a-button type="primary" :loading="submitting" @click="submitWorkerUpdate">
            保存
          </a-button>
        </a-space>
      </template>
    </a-drawer>
  </div>
</template>

<style scoped>
.worker-management {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-card {
  margin-bottom: 4px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.error-text {
  color: rgba(0, 0, 0, 0.65);
  word-break: break-word;
}
</style>
