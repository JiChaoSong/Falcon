<template>
  <div class="app-container">
    <div class="page-header">
      <div class="page-title-section">
        <h1 class="page-title">任务管理</h1>
        <p class="page-subtitle">维护压测任务、执行参数和关联场景，为后续执行与监控提供任务入口。</p>
      </div>

      <Button type="primary" @click="showAddModal">
        <template #icon><PlusOutlined /></template>
        新增任务
      </Button>
    </div>

    <ACard title="任务筛选" class="filter-card">
      <template #extra><FilterOutlined /></template>

      <Row :gutter="16">
        <Col :span="6">
          <Input
            v-model:value="state.searchFilters.name"
            placeholder="输入任务名称"
            allow-clear
            @pressEnter="applyFilters"
          />
        </Col>
        <Col :span="6">
          <Select
            v-model:value="state.searchFilters.status"
            placeholder="任务状态"
            allow-clear
            style="width: 100%"
          >
            <Select.Option value="">全部状态</Select.Option>
            <Select.Option value="pending">待执行</Select.Option>
            <Select.Option value="running">执行中</Select.Option>
            <Select.Option value="stopping">停止中</Select.Option>
            <Select.Option value="completed">已完成</Select.Option>
            <Select.Option value="failed">执行失败</Select.Option>
            <Select.Option value="canceled">已取消</Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
            v-model:value="state.searchFilters.project_id"
            placeholder="所属项目"
            allow-clear
            style="width: 100%"
            @change="handleFilterProjectChange"
          >
            <Select.Option :value="undefined">全部项目</Select.Option>
            <Select.Option
              v-for="project in state.projectOptions"
              :key="project.id"
              :value="project.id"
            >
              {{ project.name }}
            </Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
            v-model:value="state.searchFilters.scenario_id"
            :placeholder="state.searchFilters.project_id ? '所属场景' : '请先选择项目'"
            :disabled="!state.searchFilters.project_id"
            allow-clear
            style="width: 100%"
          >
            <Select.Option :value="undefined">全部场景</Select.Option>
            <Select.Option
              v-for="scenario in state.scenarioFilterOptions"
              :key="scenario.id"
              :value="scenario.id"
            >
              {{ scenario.name }}
            </Select.Option>
          </Select>
        </Col>
      </Row>

      <Divider />

      <Row justify="space-between">
        <Col>
          <Button @click="resetFilters">
            <template #icon><RedoOutlined /></template>
            重置
          </Button>
        </Col>
        <Col>
          <Button type="primary" @click="applyFilters">
            <template #icon><SearchOutlined /></template>
            查询
          </Button>
        </Col>
      </Row>
    </ACard>

    <ACard>
      <Table
        :columns="columns"
        :data-source="state.tasks"
        :pagination="false"
        :loading="state.listLoading"
        row-key="id"
        :scroll="{ x: 1400 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="statusMap[record.status]?.color || 'default'">
              {{ statusMap[record.status]?.text || record.status }}
            </Tag>
          </template>

          <template v-if="column.key === 'owner'">
            <Space>
              <Avatar size="small" style="background-color: #1677ff">
                {{ (record.owner || '?').charAt(0) }}
              </Avatar>
              <span>{{ record.owner }}</span>
            </Space>
          </template>

          <template v-if="column.key === 'scenarios'">
            <div>
              <div>{{ record.scenarios.length }} 个场景</div>
              <div class="subtle-text">
                {{ record.scenarios.slice(0, 2).map(item => item.scenario).join('，') || '暂无场景' }}
                <template v-if="record.scenarios.length > 2"> ...</template>
              </div>
            </div>
          </template>

          <template v-if="column.key === 'created_at'">
            {{ formatDateTime(record.created_at) }}
          </template>

          <template v-if="column.key === 'start_time'">
            {{ formatDateTime(record.start_time) }}
          </template>

          <template v-if="column.key === 'finished_at'">
            {{ formatDateTime(record.finished_at) }}
          </template>

          <template v-if="column.key === 'actions'">
            <Space size="small">
              <Tooltip title="预览">
                <Button type="link" size="small" @click="router.push(`/task/detail/${record.id}`)">
                  <EyeOutlined />
                </Button>
              </Tooltip>
              <Tooltip v-if="!['running', 'stopping'].includes(record.status)" title="开始执行">
                <Button type="link" size="small" @click="updateTaskStatus(record.id, 'running')">
                  <PlayCircleOutlined />
                </Button>
              </Tooltip>
              <Tooltip v-else title="停止任务">
                <Button type="link" size="small" danger :disabled="record.status === 'stopping'" @click="updateTaskStatus(record.id, 'canceled')">
                  <StopOutlined />
                </Button>
              </Tooltip>
              <Tooltip title="监控">
                <Button type="link" size="small" @click="viewMonitor(record.id)">
                  <LineChartOutlined />
                </Button>
              </Tooltip>
              <Tooltip title="编辑">
                <Button type="link" size="small" @click="showEditModal(record.id)">
                  <EditOutlined />
                </Button>
              </Tooltip>
              <Tooltip title="删除">
                <Button type="link" size="small" danger @click="deleteTask(record.id)">
                  <DeleteOutlined />
                </Button>
              </Tooltip>
            </Space>
          </template>
        </template>

        <template #emptyText>
          <div class="empty-state">
            <div class="empty-icon">
              <ScheduleOutlined />
            </div>
            <h3>暂无任务数据</h3>
            <p>当前没有找到符合条件的任务，可以先创建一个任务开始联调。</p>
          </div>
        </template>
      </Table>
    </ACard>

    <div class="pagination-container" v-if="state.total > 0">
      <Pagination
        v-model:current="state.currentPage"
        v-model:pageSize="state.pageSize"
        :total="state.total"
        :page-size-options="['8', '16', '24', '48']"
        show-quick-jumper
        show-size-changer
        @change="handlePageChange"
        :show-total="(total: number) => `共 ${total} 条`"
      />
    </div>

    <Modal
      v-model:open="state.modalVisible"
      :title="state.modalTitle"
      width="1060px"
      :confirm-loading="state.submitLoading"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    >
      <Form layout="vertical">
        <Form.Item label="任务名称" required>
          <Input v-model:value="state.formData.name" placeholder="例如：双十一大促压测" />
        </Form.Item>

        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="所属项目" required>
              <Select
                v-model:value="state.formData.project_id"
                placeholder="请选择项目"
                @change="handleProjectChange"
              >
                <Select.Option
                  v-for="project in state.projectOptions"
                  :key="project.id"
                  :value="project.id"
                >
                  {{ project.name }}
                </Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="负责人" required>
              <Select
                v-model:value="state.formData.owner_id"
                placeholder="请选择负责人"
                @change="handleOwnerChange"
              >
                <Select.Option
                  v-for="user in state.ownerOptions"
                  :key="user.id"
                  :value="user.id"
                >
                  {{ user.name }} ({{ user.username }})
                </Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="目标地址" required>
              <Input v-model:value="state.formData.host" placeholder="例如：https://api.example.com" />
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="任务状态">
              <Select v-model:value="state.formData.status">
                <Select.Option value="pending">待执行</Select.Option>
                <Select.Option value="running">执行中</Select.Option>
                <Select.Option value="stopping">停止中</Select.Option>
                <Select.Option value="completed">已完成</Select.Option>
                <Select.Option value="failed">执行失败</Select.Option>
                <Select.Option value="canceled">已取消</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Divider>压测参数</Divider>

        <Row :gutter="16">
          <Col :span="8">
            <Form.Item label="虚拟用户数" required>
              <InputNumber v-model:value="state.formData.users" :min="1" style="width: 100%" />
            </Form.Item>
          </Col>
          <Col :span="8">
            <Form.Item label="生成速率 (个/秒)" required>
              <InputNumber v-model:value="state.formData.spawn_rate" :min="1" style="width: 100%" />
            </Form.Item>
          </Col>
          <Col :span="8">
            <Form.Item label="压测时长 (秒)" required>
              <InputNumber v-model:value="state.formData.duration" :min="1" style="width: 100%" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="执行策略">
          <Select v-model:value="state.formData.execution_strategy">
            <Select.Option value="sequential">顺序执行</Select.Option>
            <Select.Option value="weighted">按权重分配</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="任务描述">
          <Input.TextArea
            v-model:value="state.formData.description"
            placeholder="描述任务的压测目标、注意事项"
            :rows="3"
          />
        </Form.Item>

        <Form.Item label="场景编排" required>
          <div class="scenario-board">
            <div class="scenario-board-head">
              <div>
                <div class="scenario-board-title">任务场景链路</div>
                <div class="scenario-board-subtitle">
                  请先选择所属项目，再从该项目下加载场景并编排执行顺序。
                </div>
              </div>
              <Button type="dashed" @click="addScenarioRow" :disabled="!state.formData.project_id">
                <template #icon><PlusOutlined /></template>
                添加场景
              </Button>
            </div>

            <div class="scenario-summary">
              <div class="scenario-summary-item">
                <span class="scenario-summary-label">执行策略</span>
                <span class="scenario-summary-value">
                  {{ executionStrategyMap[state.formData.execution_strategy] || state.formData.execution_strategy }}
                </span>
              </div>
              <div class="scenario-summary-item">
                <span class="scenario-summary-label">已编排场景</span>
                <span class="scenario-summary-value">{{ selectedScenarioCount }}</span>
              </div>
              <div class="scenario-summary-item">
                <span class="scenario-summary-label">权重合计</span>
                <span class="scenario-summary-value">
                  {{ state.formData.execution_strategy === 'weighted' ? totalScenarioWeight : '-' }}
                </span>
              </div>
            </div>

            <div class="config-tips">
              <span>
                {{ state.formData.execution_strategy === 'weighted'
                  ? '当前策略会按场景权重挑选执行目标，可选填目标用户数限制。'
                  : '当前策略会按编排顺序依次执行全部场景。' }}
              </span>
            </div>

            <div class="scenario-list">
              <div
                v-for="(scenarioBind, index) in state.formData.scenarios"
                :key="scenarioBind.row_key"
                class="scenario-row"
              >
                <div class="scenario-row-head">
                  <div class="scenario-row-title">
                    <div class="sequence-chip">#{{ index + 1 }}</div>
                    <div>
                      <div class="scenario-card-title">第 {{ index + 1 }} 个执行场景</div>
                      <div class="scenario-card-hint">
                        {{ getScenarioDisplayName(scenarioBind.scenario_id) }}
                      </div>
                    </div>
                  </div>
                  <div class="scenario-row-actions">
                    <Button size="small" :disabled="index === 0" @click="moveScenarioRow(index, 'up')">
                      <template #icon><ArrowUpOutlined /></template>
                    </Button>
                    <Button
                      size="small"
                      :disabled="index === state.formData.scenarios.length - 1"
                      @click="moveScenarioRow(index, 'down')"
                    >
                      <template #icon><ArrowDownOutlined /></template>
                    </Button>
                    <Button
                      danger
                      size="small"
                      :disabled="state.formData.scenarios.length <= 1"
                      @click="removeScenarioRow(index)"
                    >
                      <template #icon><DeleteOutlined /></template>
                    </Button>
                  </div>
                </div>

                <Row :gutter="12">
                  <Col :span="12">
                    <Form.Item label="选择场景" class="scenario-inline-item">
                      <Select
                        v-model:value="scenarioBind.scenario_id"
                        :disabled="!state.formData.project_id"
                        placeholder="请选择场景"
                        style="width: 100%"
                      >
                        <Select.Option
                          v-for="scenario in getAvailableScenarioOptions(scenarioBind.scenario_id)"
                          :key="scenario.id"
                          :value="scenario.id"
                        >
                          {{ scenario.name }}
                        </Select.Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col :span="4">
                    <Form.Item label="执行顺序" class="scenario-inline-item">
                      <div class="order-chip">顺序 {{ index + 1 }}</div>
                    </Form.Item>
                  </Col>
                  <Col :span="4">
                    <Form.Item label="权重" class="scenario-inline-item">
                      <InputNumber
                        v-model:value="scenarioBind.weight"
                        :min="0"
                        :disabled="state.formData.execution_strategy !== 'weighted'"
                        style="width: 100%"
                      />
                    </Form.Item>
                  </Col>
                  <Col :span="4">
                    <Form.Item label="目标用户数" class="scenario-inline-item">
                      <InputNumber
                        v-model:value="scenarioBind.target_users"
                        :min="1"
                        placeholder="不限"
                        style="width: 100%"
                      />
                    </Form.Item>
                  </Col>
                </Row>
              </div>
            </div>
          </div>
        </Form.Item>
      </Form>
    </Modal>

    <Modal
      v-model:open="state.previewVisible"
      title="任务详情预览"
      width="1020px"
      :footer="null"
    >
      <div v-if="state.previewLoading" class="preview-loading">
        <Spin tip="正在加载任务详情..." />
      </div>

      <Descriptions v-else-if="state.previewData" :column="2" bordered>
        <Descriptions.Item label="任务ID">{{ state.previewData.id }}</Descriptions.Item>
        <Descriptions.Item label="任务名称">{{ state.previewData.name }}</Descriptions.Item>
        <Descriptions.Item label="所属项目">{{ state.previewData.project }}</Descriptions.Item>
        <Descriptions.Item label="负责人">{{ state.previewData.owner }}</Descriptions.Item>
        <Descriptions.Item label="任务状态">
          <Tag :color="statusMap[state.previewData.status]?.color || 'default'">
            {{ statusMap[state.previewData.status]?.text || state.previewData.status }}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="目标地址">{{ state.previewData.host }}</Descriptions.Item>
        <Descriptions.Item label="虚拟用户数">{{ state.previewData.users }}</Descriptions.Item>
        <Descriptions.Item label="生成速率">{{ state.previewData.spawn_rate }}</Descriptions.Item>
        <Descriptions.Item label="时长(秒)">{{ state.previewData.duration || '-' }}</Descriptions.Item>
        <Descriptions.Item label="执行策略">
          {{ executionStrategyMap[state.previewData.execution_strategy] || state.previewData.execution_strategy }}
        </Descriptions.Item>
        <Descriptions.Item label="开始时间">{{ formatDateTime(state.previewData.start_time) }}</Descriptions.Item>
        <Descriptions.Item label="结束时间">{{ formatDateTime(state.previewData.finished_at) }}</Descriptions.Item>
        <Descriptions.Item label="任务描述" :span="2">
          {{ state.previewData.description || '-' }}
        </Descriptions.Item>
        <Descriptions.Item label="关联场景" :span="2">
          <div class="preview-scenario-list">
            <div
              v-for="scenario in state.previewData.scenarios"
              :key="`${scenario.scenario_id}-${scenario.order}`"
              class="preview-scenario-item"
            >
              <span>{{ scenario.scenario }}</span>
              <span class="subtle-text">
                顺序 {{ scenario.order }}
                <template v-if="state.previewData.execution_strategy === 'weighted'">
                  / 权重 {{ scenario.weight }}
                </template>
                <template v-if="scenario.target_users">
                  / 目标用户 {{ scenario.target_users }}
                </template>
              </span>
            </div>
          </div>
        </Descriptions.Item>
      </Descriptions>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Card as ACard,
  Row,
  Col,
  Button,
  Input,
  InputNumber,
  Select,
  Table,
  Tag,
  Avatar,
  Modal,
  Form,
  Pagination,
  Space,
  Divider,
  Tooltip,
  Descriptions,
  Spin,
  message,
} from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  RedoOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  ScheduleOutlined,
  PlayCircleOutlined,
  StopOutlined,
  LineChartOutlined,
  FilterOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/store/modules/user'
import { TaskApi } from '@/api/task'
import { ProjectApi } from '@/api/project'
import { ScenarioApi } from '@/api/scenario'
import { UserApi } from '@/api/user'
import {formatDateTime, generateUUID} from '@/utils/tools'
import type { ProjectInfo } from '@/types/project'
import type { ScenarioInfo } from '@/types/scenario'
import type { UserOption } from '@/types/user'
import type { TaskInfo, TaskScenarioBind } from '@/types/task'

type FormScenarioBind = TaskScenarioBind & { row_key: string }

const userStore = useUserStore()

const route = useRoute()
const router = useRouter()

const createDefaultScenarioRow = (): FormScenarioBind => ({
  row_key: generateUUID(),
  scenario_id: undefined as unknown as number,
  order: 1,
  weight: 0,
  target_users: null,
})

const createDefaultFormData = () => ({
  name: '',
  description: '',
  owner: userStore.name || '',
  owner_id: userStore.userId || undefined,
  project_id: undefined as number | undefined,
  project: '',
  host: '',
  users: 10,
  spawn_rate: 2,
  duration: 60,
  execution_strategy: 'sequential',
  status: 'pending',
  scenarios: [createDefaultScenarioRow()],
})

const state = reactive({
  tasks: [] as TaskInfo[],
  projectOptions: [] as ProjectInfo[],
  scenarioOptions: [] as ScenarioInfo[],
  scenarioFilterOptions: [] as ScenarioInfo[],
  ownerOptions: [] as UserOption[],
  currentPage: 1,
  pageSize: 8,
  total: 0,
  listLoading: false,
  submitLoading: false,
  modalVisible: false,
  modalTitle: '创建新任务',
  isEditing: false,
  currentEditId: null as number | null,
  previewVisible: false,
  previewLoading: false,
  previewData: null as TaskInfo | null,
  searchFilters: {
    name: '',
    status: '',
    project_id: undefined as number | undefined,
    scenario_id: undefined as number | undefined,
  },
  formData: createDefaultFormData(),
})

const statusMap: Record<string, { text: string; color: string }> = {
  pending: { text: '待执行', color: 'default' },
  running: { text: '执行中', color: 'green' },
  stopping: { text: '停止中', color: 'orange' },
  completed: { text: '已完成', color: 'blue' },
  failed: { text: '执行失败', color: 'red' },
  canceled: { text: '已取消', color: 'orange' },
}

const executionStrategyMap: Record<string, string> = {
  sequential: '顺序执行',
  weighted: '按权重分配',
}

const selectedScenarioCount = computed(
  () => state.formData.scenarios.filter(item => item.scenario_id).length
)

const totalScenarioWeight = computed(
  () => state.formData.scenarios.reduce((sum, item) => sum + Number(item.weight || 0), 0)
)

const columns = [
  { title: '任务ID', dataIndex: 'id', key: 'id', width: 130 },
  { title: '任务名称', dataIndex: 'name', key: 'name', width: 180 },
  { title: '所属项目', dataIndex: 'project', key: 'project', width: 140 },
  { title: '关联场景', key: 'scenarios', width: 220 },
  { title: '负责人', dataIndex: 'owner', key: 'owner', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 110 },
  { title: '创建时间', key: 'created_at', width: 180 },
  { title: '开始时间', key: 'start_time', width: 180 },
  { title: '结束时间', key: 'finished_at', width: 180 },
  { title: '操作', key: 'actions', width: 220, fixed: 'right' },
]

const syncScenarioOrders = () => {
  state.formData.scenarios = state.formData.scenarios.map((item, index) => ({
    ...item,
    order: index + 1,
  }))
}

const getAvailableScenarioOptions = (currentScenarioId?: number) => {
  const selectedIds = state.formData.scenarios
    .map(item => item.scenario_id)
    .filter((id): id is number => Boolean(id) && id !== currentScenarioId)

  return state.scenarioOptions.filter(item => !selectedIds.includes(item.id) || item.id === currentScenarioId)
}

const getScenarioDisplayName = (scenarioId?: number) => {
  if (!scenarioId) {
    return '请选择当前任务要执行的场景'
  }
  return state.scenarioOptions.find(item => item.id === scenarioId)?.name || `场景 #${scenarioId}`
}

const normalizeTask = (task: TaskInfo): TaskInfo => ({
  ...task,
  status: task.status?.toLowerCase() || 'pending',
  scenarios: Array.isArray(task.scenarios) ? task.scenarios : [],
})

const fetchProjectOptions = async () => {
  const response = await ProjectApi.getProjectList({ page: 1, page_size: 200 })
  state.projectOptions = response.data.results
}

const fetchOwnerOptions = async () => {
  const response = await UserApi.userOptions()
  state.ownerOptions = response.data
}

const fetchScenarioOptions = async (projectId?: number) => {
  if (!projectId) {
    state.scenarioOptions = []
    return
  }
  const response = await ScenarioApi.getScenarioList({
    page: 1,
    page_size: 200,
    project_id: projectId,
  })
  state.scenarioOptions = response.data.results
}

const fetchScenarioFilterOptions = async () => {
  const response = await ScenarioApi.getScenarioList({
    page: 1,
    page_size: 200,
    project_id: state.searchFilters.project_id,
  })
  state.scenarioFilterOptions = response.data.results
}

const fetchTaskList = async () => {
  state.listLoading = true
  try {
    const response = await TaskApi.getTaskList({
      page: state.currentPage,
      page_size: state.pageSize,
      name: state.searchFilters.name || undefined,
      status: state.searchFilters.status || undefined,
      project_id: state.searchFilters.project_id,
      scenario_id: state.searchFilters.scenario_id,
    })
    state.tasks = response.data.results.map(normalizeTask)
    state.total = response.data.total
  } catch (error) {
    console.error('获取任务列表失败:', error)
    message.error('任务列表加载失败，请稍后重试')
  } finally {
    state.listLoading = false
  }
}

const applyFilters = async () => {
  state.currentPage = 1
  await router.replace({
    path: route.path,
    query: {
      ...route.query,
      name: state.searchFilters.name || undefined,
      status: state.searchFilters.status || undefined,
      project_id: state.searchFilters.project_id ? String(state.searchFilters.project_id) : undefined,
      scenario_id: state.searchFilters.scenario_id ? String(state.searchFilters.scenario_id) : undefined,
      page: '1',
    },
  })
  await fetchTaskList()
}

const resetFilters = async () => {
  state.searchFilters = {
    name: '',
    status: '',
    project_id: undefined,
    scenario_id: undefined,
  }
  state.currentPage = 1
  await router.replace({ path: route.path })
  await fetchScenarioFilterOptions()
  await fetchTaskList()
}

const handleFilterProjectChange = async () => {
  state.searchFilters.scenario_id = undefined
  await fetchScenarioFilterOptions()
}

const handlePageChange = async (page: number, pageSize: number) => {
  state.currentPage = page
  state.pageSize = pageSize
  await fetchTaskList()
}

const handleProjectChange = async (projectId: number) => {
  const project = state.projectOptions.find(item => item.id === projectId)
  state.formData.project_id = project?.id
  state.formData.project = project?.name || ''
  state.formData.scenarios = [createDefaultScenarioRow()]
  syncScenarioOrders()
  await fetchScenarioOptions(projectId)
}

const handleOwnerChange = (ownerId: number) => {
  const owner = state.ownerOptions.find(item => item.id === ownerId)
  state.formData.owner_id = owner?.id
  state.formData.owner = owner?.name || ''
}

const addScenarioRow = () => {
  state.formData.scenarios.push(createDefaultScenarioRow())
  syncScenarioOrders()
}

const removeScenarioRow = (index: number) => {
  state.formData.scenarios.splice(index, 1)
  syncScenarioOrders()
}

const moveScenarioRow = (index: number, direction: 'up' | 'down') => {
  const targetIndex = direction === 'up' ? index - 1 : index + 1
  if (targetIndex < 0 || targetIndex >= state.formData.scenarios.length) {
    return
  }
  const [current] = state.formData.scenarios.splice(index, 1)
  state.formData.scenarios.splice(targetIndex, 0, current)
  syncScenarioOrders()
}

const showAddModal = async () => {
  state.modalTitle = '创建新任务'
  state.isEditing = false
  state.currentEditId = null
  state.formData = createDefaultFormData()
  syncScenarioOrders()
  state.scenarioOptions = []
  state.modalVisible = true
}

const showEditModal = async (taskId: number) => {
  try {
    const response = await TaskApi.getTaskInfo({ id: taskId })
    const task = normalizeTask(response.data)
    state.modalTitle = '编辑任务'
    state.isEditing = true
    state.currentEditId = taskId
    state.formData = {
      name: task.name,
      description: task.description || '',
      owner: task.owner,
      owner_id: task.owner_id,
      project_id: task.project_id,
      project: task.project,
      host: task.host,
      users: task.users,
      spawn_rate: task.spawn_rate,
      duration: task.duration || 60,
      execution_strategy: task.execution_strategy || 'sequential',
      status: task.status,
      scenarios: task.scenarios.length
        ? task.scenarios.map(item => ({ ...item, row_key: generateUUID() }))
        : [createDefaultScenarioRow()],
    }
    syncScenarioOrders()
    state.modalVisible = true
    await fetchScenarioOptions(task.project_id)
  } catch (error) {
    console.error('获取任务详情失败:', error)
    message.error('任务详情加载失败，请稍后重试')
  }
}

const validateForm = () => {
  if (!state.formData.name.trim()) {
    message.error('请输入任务名称')
    return false
  }
  if (!state.formData.project_id || !state.formData.project) {
    message.error('请选择所属项目')
    return false
  }
  if (!state.formData.owner_id || !state.formData.owner) {
    message.error('请选择负责人')
    return false
  }
  if (!state.formData.host.trim()) {
    message.error('请输入目标地址')
    return false
  }
  const validScenarios = state.formData.scenarios.filter(item => item.scenario_id)
  if (!validScenarios.length) {
    message.error('请至少选择一个场景')
    return false
  }
  if (new Set(validScenarios.map(item => item.scenario_id)).size !== validScenarios.length) {
    message.error('同一个任务中不能重复添加相同场景')
    return false
  }
  if (state.formData.execution_strategy === 'weighted') {
    const totalWeight = validScenarios.reduce((sum, item) => sum + Number(item.weight || 0), 0)
    if (totalWeight <= 0) {
      message.error('按权重分配时，场景权重总和必须大于 0')
      return false
    }
  }
  return true
}

const buildScenariosPayload = () =>
  state.formData.scenarios
    .filter(item => item.scenario_id)
    .map(({ scenario_id, order, weight, target_users }) => ({
      scenario_id,
      order,
      weight,
      target_users: target_users || undefined,
    }))

const handleModalOk = async () => {
  if (!validateForm()) {
    return
  }
  state.submitLoading = true
  try {
    const payload = {
      name: state.formData.name.trim(),
      description: state.formData.description || undefined,
      owner: state.formData.owner,
      owner_id: state.formData.owner_id!,
      project_id: state.formData.project_id!,
      project: state.formData.project,
      host: state.formData.host.trim(),
      users: state.formData.users,
      spawn_rate: state.formData.spawn_rate,
      duration: state.formData.duration,
      execution_strategy: state.formData.execution_strategy,
      scenarios: buildScenariosPayload(),
    }

    if (state.isEditing && state.currentEditId) {
      await TaskApi.updateTask({
        id: state.currentEditId,
        ...payload,
        status: state.formData.status,
      })
      message.success('任务已更新')
    } else {
      const response = await TaskApi.createTask(payload)
      if (state.formData.status !== 'pending') {
        await TaskApi.updateTask({
          id: response.data.id,
          status: state.formData.status,
        })
      }
      message.success('任务已创建')
    }

    state.modalVisible = false
    await fetchTaskList()
  } catch (error) {
    console.error('保存任务失败:', error)
    message.error('保存任务失败，请稍后重试')
  } finally {
    state.submitLoading = false
  }
}

const handleModalCancel = () => {
  state.modalVisible = false
}

const previewTask = async (taskId: number) => {
  state.previewVisible = true
  state.previewLoading = true
  try {
    const response = await TaskApi.getTaskInfo({ id: taskId })
    state.previewData = normalizeTask(response.data)
  } catch (error) {
    console.error('获取任务详情失败:', error)
    message.error('任务详情加载失败，请稍后重试')
    state.previewVisible = false
  } finally {
    state.previewLoading = false
  }
}

const updateTaskStatus = async (taskId: number, status: string) => {
  try {
    if (status === 'running') {
      await TaskApi.runTask({ task_id: taskId })
      message.success('任务已开始执行')
    } else if (status === 'canceled') {
      await TaskApi.stopTask({ task_id: taskId })
      message.success('任务已发送停止指令')
    } else {
      await TaskApi.updateTask({ id: taskId, status })
      message.success(`任务状态已更新为 ${statusMap[status]?.text || status}`)
    }
    await fetchTaskList()
  } catch (error) {
    console.error('更新任务状态失败:', error)
    message.error('更新任务状态失败，请稍后重试')
  }
}

const viewMonitor = (taskId: number) => {
  router.push(`/monitor/${taskId}`)
}

const deleteTask = async (taskId: number) => {
  const task = state.tasks.find(item => item.id === taskId)
  if (!task) {
    return
  }
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除任务 "${task.name}" 吗？此操作不可恢复。`,
    okType: 'danger',
    async onOk() {
      await TaskApi.deleteTask({ id: taskId })
      message.success(`任务 "${task.name}" 已删除`)
      await fetchTaskList()
    },
  })
}

onMounted(async () => {
  const queryName = route.query.name as string | undefined
  const queryStatus = route.query.status as string | undefined
  const queryProjectId = Number(route.query.project_id)
  const queryScenarioId = Number(route.query.scenario_id)
  const queryPage = Number(route.query.page || 1)

  if (queryName) {
    state.searchFilters.name = queryName
  }
  if (queryStatus) {
    state.searchFilters.status = queryStatus
  }
  if (Number.isFinite(queryProjectId) && queryProjectId > 0) {
    state.searchFilters.project_id = queryProjectId
  }
  if (Number.isFinite(queryScenarioId) && queryScenarioId > 0) {
    state.searchFilters.scenario_id = queryScenarioId
  }
  if (Number.isFinite(queryPage) && queryPage > 0) {
    state.currentPage = queryPage
  }

  await fetchProjectOptions()
  await fetchOwnerOptions()
  await fetchScenarioFilterOptions()
  await fetchTaskList()
})
</script>

<style scoped>
.app-container {
  padding: 10px;
  min-height: calc(100vh - 64px);
  box-sizing: border-box;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.page-title-section {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: rgba(0, 0, 0, 0.85);
}

.page-subtitle {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
  margin: 8px 0 0 0;
}

.filter-card {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.scenario-board {
  padding: 18px;
  border: 1px solid #e8eef8;
  border-radius: 16px;
  background:
    radial-gradient(circle at top right, rgba(228, 239, 255, 0.85), transparent 34%),
    linear-gradient(180deg, #ffffff 0%, #f9fbff 100%);
}

.scenario-board-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.scenario-board-title {
  font-size: 16px;
  font-weight: 700;
  color: #183153;
}

.scenario-board-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #6a7b92;
  line-height: 1.6;
}

.scenario-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.scenario-summary-item {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(247, 250, 255, 0.95);
  border: 1px solid rgba(22, 119, 255, 0.08);
}

.scenario-summary-label {
  display: block;
  font-size: 12px;
  color: #73839a;
}

.scenario-summary-value {
  display: block;
  margin-top: 6px;
  font-size: 15px;
  font-weight: 700;
  color: #183153;
}

.config-tips {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(240, 247, 255, 0.9);
  font-size: 12px;
  line-height: 1.7;
  color: #52637a;
}

.scenario-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scenario-row {
  padding: 16px;
  border: 1px solid #edf2fa;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  box-shadow: 0 8px 20px rgba(30, 64, 175, 0.04);
}

.scenario-row-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.scenario-row-title {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.scenario-card-title {
  font-size: 14px;
  font-weight: 700;
  color: #183153;
}

.scenario-card-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #6a7b92;
}

.scenario-row-actions {
  display: flex;
  gap: 8px;
}

.sequence-chip,
.order-chip {
  min-width: 72px;
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.sequence-chip {
  background: #eef4ff;
  color: #1677ff;
}

.order-chip {
  width: 100%;
  background: #f6ffed;
  color: #389e0d;
}

.scenario-inline-item {
  margin-bottom: 0;
}

.subtle-text {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.preview-loading {
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-scenario-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-scenario-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.empty-icon {
  font-size: 48px;
  color: rgba(0, 0, 0, 0.25);
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 8px;
}

.empty-state p {
  color: rgba(0, 0, 0, 0.45);
  max-width: 400px;
  margin: 0 auto 16px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .scenario-board-head,
  .scenario-row-head {
    flex-direction: column;
  }

  .scenario-summary {
    grid-template-columns: 1fr;
  }
}
</style>
