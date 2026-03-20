<template>
  <div class="app-container">
    <div class="page-header">
      <div class="page-title-section">
        <h1 class="page-title">场景管理</h1>
        <p class="page-subtitle">维护项目场景和用例编排关系，为任务执行提供稳定的场景模板。</p>
      </div>

      <Button type="primary" @click="showAddModal">
        <template #icon><PlusOutlined /></template>
        新增场景
      </Button>
    </div>

    <ACard title="场景筛选" class="filter-card">
      <template #extra><FilterOutlined /></template>

      <Row :gutter="16">
        <Col :span="8">
          <Input
            v-model:value="state.searchFilters.name"
            placeholder="输入场景名称"
            allow-clear
            @pressEnter="applyFilters"
          />
        </Col>
        <Col :span="8">
          <Select
            v-model:value="state.searchFilters.project_id"
            placeholder="所属项目"
            allow-clear
            style="width: 100%"
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
        <Col :span="8">
          <Select
            v-model:value="state.searchFilters.status"
            placeholder="场景状态"
            allow-clear
            style="width: 100%"
          >
            <Select.Option value="">全部状态</Select.Option>
            <Select.Option value="draft">草稿</Select.Option>
            <Select.Option value="active">启用中</Select.Option>
            <Select.Option value="inactive">已停用</Select.Option>
            <Select.Option value="archived">已归档</Select.Option>
          </Select>
        </Col>
      </Row>

      <Divider />

      <Row justify="space-between">
        <Col>
          <Button @click="resetFilters">
            <template #icon><RedoOutlined /></template>
            重置筛选条件
          </Button>
        </Col>
        <Col>
          <Button type="primary" @click="applyFilters">
            <template #icon><SearchOutlined /></template>
            查询场景
          </Button>
        </Col>
      </Row>
    </ACard>

    <ACard>
      <Table
        :columns="columns"
        :data-source="state.scenarios"
        :pagination="false"
        :loading="state.listLoading"
        row-key="id"
        :scroll="{ x: 1200 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="statusMap[record.status]?.color || 'default'">
              {{ statusMap[record.status]?.text || record.status }}
            </Tag>
          </template>

          <template v-if="column.key === 'cases'">
            <div>
              <div>{{ record.total_testcases || record.cases.length || 0 }} 个用例</div>
              <div class="subtle-text">
                {{ getCaseSummary(record.cases) }}
              </div>
            </div>
          </template>

          <template v-if="column.key === 'created_at'">
            {{ formatDateTime(record.created_at) }}
          </template>

          <template v-if="column.key === 'last_run'">
            {{ formatDateTime(record.last_run) }}
          </template>

          <template v-if="column.key === 'actions'">
            <Space size="small">
              <Tooltip title="预览">
                <Button type="link" size="small" @click="previewScenario(record.id)">
                  <EyeOutlined />
                </Button>
              </Tooltip>
              <Tooltip title="编辑">
                <Button type="link" size="small" @click="showEditModal(record.id)">
                  <EditOutlined />
                </Button>
              </Tooltip>
              <Tooltip title="复制">
                <Button type="link" size="small" @click="copyScenario(record.id)">
                  <CopyOutlined />
                </Button>
              </Tooltip>
              <Tooltip title="删除">
                <Button type="link" size="small" danger @click="deleteScenario(record.id)">
                  <DeleteOutlined />
                </Button>
              </Tooltip>
            </Space>
          </template>
        </template>

        <template #emptyText>
          <div class="empty-state">
            <div class="empty-icon">
              <ApiOutlined />
            </div>
            <h3>暂无场景数据</h3>
            <p>当前没有找到符合条件的场景，可以先从已有项目下创建一个场景。</p>
          </div>
        </template>
      </Table>
    </ACard>

    <div class="pagination-container" v-if="paginationTotal > 0">
      <Pagination
        v-model:current="state.currentPage"
        v-model:pageSize="state.pageSize"
        :total="paginationTotal"
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
      width="860px"
      :confirm-loading="state.submitLoading"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    >
      <Form layout="vertical">
        <Form.Item label="场景名称" required>
          <Input v-model:value="state.formData.name" placeholder="例如：首页访问场景" />
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
            <Form.Item label="场景状态">
              <Select v-model:value="state.formData.status">
                <Select.Option value="draft">草稿</Select.Option>
                <Select.Option value="active">启用中</Select.Option>
                <Select.Option value="inactive">已停用</Select.Option>
                <Select.Option value="archived">已归档</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="场景描述">
          <Input.TextArea
            v-model:value="state.formData.description"
            placeholder="描述此场景的用途、测试目标和注意事项"
            :rows="4"
          />
        </Form.Item>

        <Form.Item label="测试用例配置" required>
          <div class="config-header">
            <span>测试用例列表</span>
            <Button type="dashed" size="small" @click="addCaseRow" :disabled="!state.formData.project_id">
              <template #icon><PlusOutlined /></template>
              添加用例
            </Button>
          </div>

          <div class="config-tips">
            <span>先选择所属项目，再从该项目下加载并选择用例。</span>
            <span :class="['weight-total', getWeightTotal() === 100 ? 'is-valid' : 'is-invalid']">
              当前权重总和 {{ getWeightTotal() }}%
            </span>
          </div>

          <div
            v-for="(caseBind, index) in state.formData.cases"
            :key="caseBind.row_key"
            class="case-row"
          >
            <Row :gutter="8" align="middle">
              <Col :span="2">
                <div class="sequence-chip">#{{ index + 1 }}</div>
              </Col>
              <Col :span="11">
                <Select
                  v-model:value="caseBind.case_id"
                  :disabled="!state.formData.project_id"
                  placeholder="请选择测试用例"
                  style="width: 100%"
                >
                  <Select.Option
                    v-for="testcase in getAvailableCaseOptions(caseBind.case_id)"
                    :key="testcase.id"
                    :value="testcase.id"
                  >
                    {{ testcase.name }}
                  </Select.Option>
                </Select>
              </Col>
              <Col :span="6">
                <InputNumber
                  v-model:value="caseBind.weight"
                  :min="1"
                  :max="100"
                  :disabled="!caseBind.case_id"
                  placeholder="权重"
                  style="width: 100%"
                />
              </Col>
              <Col :span="5">
                <Space>
                  <Button size="small" :disabled="index === 0" @click="moveCaseRow(index, 'up')">
                    <template #icon><ArrowUpOutlined /></template>
                  </Button>
                  <Button
                    size="small"
                    :disabled="index === state.formData.cases.length - 1"
                    @click="moveCaseRow(index, 'down')"
                  >
                    <template #icon><ArrowDownOutlined /></template>
                  </Button>
                  <Button
                    danger
                    size="small"
                    :disabled="state.formData.cases.length <= 1"
                    @click="removeCaseRow(index)"
                  >
                    <template #icon><DeleteOutlined /></template>
                  </Button>
                </Space>
              </Col>
            </Row>
          </div>
        </Form.Item>
      </Form>
    </Modal>

    <Modal
      v-model:open="state.previewVisible"
      title="场景详情预览"
      width="760px"
      :footer="null"
    >
      <div v-if="state.previewLoading" class="preview-loading">
        <a-spin tip="正在加载场景详情..." />
      </div>

      <Descriptions v-else-if="state.previewData" :column="2" bordered>
        <DescriptionsItem label="场景ID">{{ state.previewData.id }}</DescriptionsItem>
        <DescriptionsItem label="场景名称">{{ state.previewData.name }}</DescriptionsItem>
        <DescriptionsItem label="所属项目">{{ state.previewData.project }}</DescriptionsItem>
        <DescriptionsItem label="场景状态">
          <Tag :color="statusMap[state.previewData.status]?.color || 'default'">
            {{ statusMap[state.previewData.status]?.text || state.previewData.status }}
          </Tag>
        </DescriptionsItem>
        <DescriptionsItem label="创建时间">{{ formatDateTime(state.previewData.created_at) }}</DescriptionsItem>
        <DescriptionsItem label="最后运行">{{ formatDateTime(state.previewData.last_run) }}</DescriptionsItem>
        <DescriptionsItem label="场景描述" :span="2">
          {{ state.previewData.description || '-' }}
        </DescriptionsItem>
        <DescriptionsItem label="关联用例" :span="2">
          <div class="preview-case-list">
            <div
              v-for="caseBind in state.previewData.cases"
              :key="`${caseBind.case_id}-${caseBind.order}`"
              class="preview-case-item"
            >
              <span>{{ getCaseName(caseBind.case_id, caseBind.name) }}</span>
              <span class="subtle-text">顺序 {{ caseBind.order }} / 权重 {{ caseBind.weight }}</span>
            </div>
          </div>
        </DescriptionsItem>
      </Descriptions>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import {
  Card as ACard,
  Row,
  Col,
  Button,
  Input,
  Select,
  Table,
  Tag,
  Modal,
  Form,
  InputNumber,
  Pagination,
  Space,
  Divider,
  Descriptions,
  DescriptionsItem,
  Tooltip,
  message,
} from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  RedoOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
  FilterOutlined,
  CopyOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons-vue'
import { ScenarioApi } from '@/api/scenario'
import { ProjectApi } from '@/api/project'
import { CaseApi } from '@/api/case'
import { formatDateTime } from '@/utils/tools'
import type { ProjectInfo } from '@/types/project'
import type { CaseInfo } from '@/types/case'
import type { ScenarioCaseBind, ScenarioCaseSummary, ScenarioInfo, ScenarioListItem } from '@/types/scenario'

type FormCaseBind = ScenarioCaseBind & { row_key: string }

const createDefaultCaseRow = (): FormCaseBind => ({
  row_key: crypto.randomUUID(),
  case_id: undefined as unknown as number,
  order: 1,
  weight: 100,
})

const createDefaultFormData = () => ({
  name: '',
  project_id: undefined as number | undefined,
  project: '',
  status: 'draft',
  description: '',
  cases: [createDefaultCaseRow()],
})

const state = reactive({
  scenarios: [] as ScenarioListItem[],
  projectOptions: [] as ProjectInfo[],
  caseOptions: [] as CaseInfo[],
  currentPage: 1,
  pageSize: 8,
  total: 0,
  listLoading: false,
  submitLoading: false,
  modalVisible: false,
  modalTitle: '创建新场景',
  isEditing: false,
  currentEditId: null as number | null,
  previewVisible: false,
  previewLoading: false,
  previewData: null as ScenarioInfo | null,
  searchFilters: {
    name: '',
    project_id: undefined as number | undefined,
    status: '',
  },
  formData: createDefaultFormData(),
})

const statusMap: Record<string, { text: string; color: string }> = {
  draft: { text: '草稿', color: 'default' },
  active: { text: '启用中', color: 'green' },
  inactive: { text: '已停用', color: 'orange' },
  archived: { text: '已归档', color: 'purple' },
}

const columns = [
  { title: '场景ID', dataIndex: 'id', key: 'id', width: 120 },
  { title: '场景名称', dataIndex: 'name', key: 'name', width: 180 },
  { title: '所属项目', dataIndex: 'project', key: 'project', width: 140 },
  { title: '测试用例', key: 'cases', width: 240 },
  { title: '描述', dataIndex: 'description', key: 'description', width: 220, ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 110 },
  { title: '创建时间', key: 'created_at', width: 180 },
  { title: '最后运行', key: 'last_run', width: 180 },
  { title: '操作', key: 'actions', width: 180, fixed: 'right' },
]

const getCaseName = (caseId: number, fallbackName?: string) => {
  return fallbackName || state.caseOptions.find(item => item.id === caseId)?.name || `用例 ${caseId}`
}

const syncCaseMeta = () => {
  state.formData.cases = state.formData.cases.map((item, index) => {
    return {
      ...item,
      order: index + 1,
    }
  })
}

const rebalanceCaseWeights = () => {
  const total = state.formData.cases.length || 1
  const baseWeight = Math.floor(100 / total)
  let remainder = 100 - baseWeight * total

  state.formData.cases = state.formData.cases.map(item => {
    const extra = remainder > 0 ? 1 : 0
    remainder -= extra
    return {
      ...item,
      weight: baseWeight + extra,
    }
  })
}

const getWeightTotal = () => {
  return state.formData.cases.reduce((sum, item) => sum + (Number(item.weight) || 0), 0)
}

const getAvailableCaseOptions = (currentCaseId?: number) => {
  const selectedIds = state.formData.cases
    .map(item => item.case_id)
    .filter((id): id is number => Boolean(id) && id !== currentCaseId)

  return state.caseOptions.filter(item => !selectedIds.includes(item.id) || item.id === currentCaseId)
}

const getCaseSummary = (cases: ScenarioCaseSummary[]) => {
  if (!cases?.length) {
    return '暂无关联用例'
  }
  return cases
    .slice(0, 2)
    .map(item => `${getCaseName(item.case_id, item.name)}(${item.weight})`)
    .join('，') + (cases.length > 2 ? ' ...' : '')
}

const normalizeScenario = <T extends ScenarioInfo | ScenarioListItem>(scenario: T): T => ({
  ...scenario,
  status: scenario.status?.toLowerCase() || 'draft',
  cases: Array.isArray(scenario.cases) ? scenario.cases : [],
}) as T

const paginationTotal = computed(() => Number(state?.total || 0))

const fetchProjectOptions = async () => {
  const response = await ProjectApi.getProjectList({ page: 1, page_size: 200 })
  state.projectOptions = response.data.results
}

const fetchCaseOptions = async (projectId?: number) => {
  if (!projectId) {
    state.caseOptions = []
    return
  }
  const response = await CaseApi.getCaseList({
    page: 1,
    page_size: 200,
    project_id: projectId,
  })
  state.caseOptions = response.data.results
}

const fetchScenarioList = async () => {
  state.listLoading = true
  try {
    const response = await ScenarioApi.getScenarioList({
      page: state.currentPage,
      page_size: state.pageSize,
      name: state.searchFilters.name || undefined,
      project_id: state.searchFilters.project_id,
      status: state.searchFilters.status || undefined,
    })
    const payload = response?.data || { results: [], total: 0 }
    state.scenarios = Array.isArray(payload.results) ? payload.results.map(normalizeScenario) : []
    state.total = Number(payload.total || 0)
  } catch (error) {
    state.scenarios = []
    state.total = 0
    console.error('获取场景列表失败:', error)
    message.error('场景列表加载失败，请稍后重试')
  } finally {
    state.listLoading = false
  }
}

const applyFilters = async () => {
  state.currentPage = 1
  await fetchScenarioList()
}

const resetFilters = async () => {
  state.searchFilters = {
    name: '',
    project_id: undefined,
    status: '',
  }
  state.currentPage = 1
  await fetchScenarioList()
}

const handlePageChange = async (page: number, pageSize: number) => {
  state.currentPage = page
  state.pageSize = pageSize
  await fetchScenarioList()
}

const handleProjectChange = async (projectId: number) => {
  const project = state.projectOptions.find(item => item.id === projectId)
  state.formData.project_id = project?.id
  state.formData.project = project?.name || ''
  state.formData.cases = [createDefaultCaseRow()]
  syncCaseMeta()
  await fetchCaseOptions(projectId)
}

const addCaseRow = () => {
  state.formData.cases.push(createDefaultCaseRow())
  syncCaseMeta()
  rebalanceCaseWeights()
}

const removeCaseRow = (index: number) => {
  state.formData.cases.splice(index, 1)
  syncCaseMeta()
  rebalanceCaseWeights()
}

const moveCaseRow = (index: number, direction: 'up' | 'down') => {
  const targetIndex = direction === 'up' ? index - 1 : index + 1
  if (targetIndex < 0 || targetIndex >= state.formData.cases.length) {
    return
  }
  const [current] = state.formData.cases.splice(index, 1)
  state.formData.cases.splice(targetIndex, 0, current)
  syncCaseMeta()
}

const showAddModal = async () => {
  state.modalTitle = '创建新场景'
  state.isEditing = false
  state.currentEditId = null
  state.formData = createDefaultFormData()
  state.modalVisible = true
  syncCaseMeta()
  state.caseOptions = []
}

const showEditModal = async (scenarioId: number) => {
  try {
    const response = await ScenarioApi.getScenarioInfo({ id: scenarioId })
    const scenario = normalizeScenario(response.data)
    state.modalTitle = '编辑场景'
    state.isEditing = true
    state.currentEditId = scenarioId
    state.formData = {
      name: scenario.name,
      project_id: scenario.project_id,
      project: scenario.project,
      status: scenario.status,
      description: scenario.description || '',
      cases: scenario.cases.length
        ? scenario.cases.map(item => ({ ...item, row_key: crypto.randomUUID() }))
        : [createDefaultCaseRow()],
    }
    syncCaseMeta()
    state.modalVisible = true
    await fetchCaseOptions(scenario.project_id)
  } catch (error) {
    console.error('获取场景详情失败:', error)
    message.error('场景详情加载失败，请稍后重试')
  }
}

const validateForm = () => {
  if (!state.formData.name.trim()) {
    message.error('请输入场景名称')
    return false
  }
  if (!state.formData.project_id || !state.formData.project) {
    message.error('请选择所属项目')
    return false
  }

  const validCases = state.formData.cases.filter(item => item.case_id)
  if (!validCases.length) {
    message.error('请至少选择一个测试用例')
    return false
  }
  if (new Set(validCases.map(item => item.case_id)).size !== validCases.length) {
    message.error('同一个场景中不能重复添加相同用例')
    return false
  }
  if (getWeightTotal() !== 100) {
    message.error('用例权重总和必须为 100%')
    return false
  }
  return true
}

const buildCasesPayload = () =>
  state.formData.cases
    .filter(item => item.case_id)
    .map(({ case_id, order, weight }) => ({
      case_id,
      order,
      weight,
    }))

const handleModalOk = async () => {
  if (!validateForm()) {
    return
  }

  state.submitLoading = true
  try {
    const payload = {
      name: state.formData.name.trim(),
      project_id: state.formData.project_id!,
      project: state.formData.project,
      description: state.formData.description || undefined,
      cases: buildCasesPayload(),
    }

    if (state.isEditing && state.currentEditId) {
      await ScenarioApi.updateScenario({
        id: state.currentEditId,
        ...payload,
        status: state.formData.status,
      })
      message.success('场景已更新')
    } else {
      const response = await ScenarioApi.createScenario(payload)
      if (state.formData.status !== 'draft') {
        await ScenarioApi.updateScenario({
          id: response.data.id,
          status: state.formData.status,
        })
      }
      message.success('场景已创建')
    }

    state.modalVisible = false
    await fetchScenarioList()
  } catch (error) {
    console.error('保存场景失败:', error)
    message.error('保存场景失败，请稍后重试')
  } finally {
    state.submitLoading = false
  }
}

const handleModalCancel = () => {
  state.modalVisible = false
}

const previewScenario = async (scenarioId: number) => {
  state.previewVisible = true
  state.previewLoading = true
  try {
    const response = await ScenarioApi.getScenarioInfo({ id: scenarioId })
    state.previewData = normalizeScenario(response.data)
  } catch (error) {
    console.error('获取场景详情失败:', error)
    message.error('场景详情加载失败，请稍后重试')
    state.previewVisible = false
  } finally {
    state.previewLoading = false
  }
}

const copyScenario = async (scenarioId: number) => {
  try {
    const response = await ScenarioApi.getScenarioInfo({ id: scenarioId })
    const scenario = normalizeScenario(response.data)
    const createResponse = await ScenarioApi.createScenario({
      name: `${scenario.name} (副本)`,
      project_id: scenario.project_id,
      project: scenario.project,
      description: scenario.description || undefined,
      cases: scenario.cases,
    })
    if (scenario.status !== 'draft') {
      await ScenarioApi.updateScenario({ id: createResponse.data.id, status: scenario.status })
    }
    message.success(`场景 "${scenario.name}" 已复制`)
    await fetchScenarioList()
  } catch (error) {
    console.error('复制场景失败:', error)
    message.error('复制场景失败，请稍后重试')
  }
}

const deleteScenario = async (scenarioId: number) => {
  const scenario = state.scenarios.find(item => item.id === scenarioId)
  if (!scenario) {
    return
  }

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除场景 "${scenario.name}" 吗？此操作不可恢复。`,
    okType: 'danger',
    async onOk() {
      await ScenarioApi.deleteScenario({ id: scenarioId })
      message.success(`场景 "${scenario.name}" 已删除`)
      await fetchScenarioList()
    },
  })
}

onMounted(async () => {
  await fetchProjectOptions()
  await fetchScenarioList()
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

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.config-tips {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.case-row {
  margin-bottom: 12px;
  padding: 14px 16px;
  border: 1px solid #edf2fa;
  border-radius: 12px;
  background: #fcfdff;
}

.sequence-chip {
  height: 32px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.sequence-chip {
  background: #eef4ff;
  color: #1677ff;
}

.weight-total {
  font-weight: 600;
}

.weight-total.is-valid {
  color: #389e0d;
}

.weight-total.is-invalid {
  color: #cf1322;
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

.preview-case-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-case-item {
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
}
</style>
