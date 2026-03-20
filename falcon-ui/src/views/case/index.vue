<template>
  <div class="app-container">
    <div class="page-header">
      <div class="page-title-section">
        <h1 class="page-title">用例管理</h1>
        <p class="page-subtitle">维护压测基础用例，统一关联项目、请求配置与断言逻辑。</p>
      </div>

      <Space>
        <Button @click="showImportModal">
          <template #icon><ImportOutlined /></template>
          导入用例
        </Button>
        <Button type="primary" @click="showAddModal">
          <template #icon><PlusOutlined /></template>
          新增用例
        </Button>
      </Space>
    </div>

    <ACard title="用例筛选" class="filter-card">
      <template #extra><FilterOutlined /></template>

      <Row :gutter="16">
        <Col :span="6">
          <Input
            v-model:value="state.searchFilters.name"
            placeholder="输入用例名称"
            allow-clear
            @pressEnter="applyFilters"
          />
        </Col>
        <Col :span="6">
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
        <Col :span="6">
          <Select
            v-model:value="state.searchFilters.type"
            placeholder="用例类型"
            allow-clear
            style="width: 100%"
          >
            <Select.Option value="">全部类型</Select.Option>
            <Select.Option value="http">HTTP/HTTPS</Select.Option>
            <Select.Option value="websocket">WebSocket</Select.Option>
            <Select.Option value="grpc">gRPC</Select.Option>
            <Select.Option value="custom">自定义脚本</Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
            v-model:value="state.searchFilters.status"
            placeholder="用例状态"
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
            查询用例
          </Button>
        </Col>
      </Row>
    </ACard>

    <ACard v-if="state.selectedCaseIds.length > 0" class="batch-actions-card">
      <div class="batch-content">
        <Checkbox v-model:checked="state.isAllSelected" @change="toggleSelectAll">
          全选当前页
        </Checkbox>

        <div class="batch-buttons">
          <Button @click="batchUpdateStatus('active')">
            <template #icon><CheckCircleOutlined /></template>
            批量启用
          </Button>
          <Button @click="batchUpdateStatus('inactive')">
            <template #icon><StopOutlined /></template>
            批量停用
          </Button>
          <Button @click="batchExportCases">
            <template #icon><DownloadOutlined /></template>
            批量导出
          </Button>
          <Button danger @click="batchDeleteCases">
            <template #icon><DeleteOutlined /></template>
            批量删除
          </Button>
        </div>

        <div class="selected-count">
          已选择 <span>{{ state.selectedCaseIds.length }}</span> 个用例
        </div>
      </div>
    </ACard>

    <ACard>
      <Table
        :columns="columns"
        :data-source="state.testcases"
        :pagination="false"
        :loading="state.listLoading"
        :row-selection="rowSelection"
        row-key="id"
        :scroll="{ x: 1300 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <Tag :color="typeMap[record.type]?.color || 'default'">
              {{ typeMap[record.type]?.text || record.type }}
            </Tag>
          </template>

          <template v-if="column.key === 'method'">
            <Tag :color="methodMap[record.method || '']?.color || 'default'">
              {{ record.method || '-' }}
            </Tag>
          </template>

          <template v-if="column.key === 'url'">
            <Tooltip :title="record.url || record.description || '-'" placement="topLeft">
              <span class="ellipsis-text">
                {{ truncateText(record.url || record.description || '-', 52) }}
              </span>
            </Tooltip>
          </template>

          <template v-if="column.key === 'status'">
            <Tag :color="statusMap[record.status]?.color || 'default'">
              {{ statusMap[record.status]?.text || record.status }}
            </Tag>
          </template>

          <template v-if="column.key === 'created_at'">
            {{ formatDateTime(record.created_at) }}
          </template>

          <template v-if="column.key === 'actions'">
            <Space size="small">
              <Tooltip title="预览">
                <Button type="link" size="small" @click="previewCase(record.id)">
                  <EyeOutlined />
                </Button>
              </Tooltip>
              <Tooltip title="编辑">
                <Button type="link" size="small" @click="showEditModal(record.id)">
                  <EditOutlined />
                </Button>
              </Tooltip>
              <Tooltip title="复制">
                <Button type="link" size="small" @click="copyCase(record.id)">
                  <CopyOutlined />
                </Button>
              </Tooltip>
              <Tooltip title="删除">
                <Button type="link" size="small" danger @click="deleteCase(record.id)">
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
            <h3>暂无用例数据</h3>
            <p>当前没有找到符合条件的用例，可以先新建一个用例开始联调。</p>
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
      width="860px"
      :mask-closable="false"
      :confirm-loading="state.submitLoading"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    >
      <Tabs v-model:activeKey="state.activeTab">
        <Tabs.TabPane key="basic" tab="基础信息">
          <Form layout="vertical">
            <Form.Item label="用例名称" required>
              <Input
                v-model:value="state.formData.name"
                placeholder="例如：用户登录接口"
              />
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
                <Form.Item label="用例状态">
                  <Select v-model:value="state.formData.status">
                    <Select.Option value="draft">草稿</Select.Option>
                    <Select.Option value="active">启用中</Select.Option>
                    <Select.Option value="inactive">已停用</Select.Option>
                    <Select.Option value="archived">已归档</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row :gutter="16">
              <Col :span="12">
                <Form.Item label="用例类型">
                  <Select v-model:value="state.formData.type" @change="handleTypeChange">
                    <Select.Option value="http">HTTP/HTTPS</Select.Option>
                    <Select.Option value="websocket">WebSocket</Select.Option>
                    <Select.Option value="grpc">gRPC</Select.Option>
                    <Select.Option value="custom">自定义脚本</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col :span="12">
                <Form.Item label="请求方法">
                  <Select
                    v-model:value="state.formData.method"
                    :disabled="state.formData.type === 'custom'"
                  >
                    <Select.Option value="GET">GET</Select.Option>
                    <Select.Option value="POST">POST</Select.Option>
                    <Select.Option value="PUT">PUT</Select.Option>
                    <Select.Option value="DELETE">DELETE</Select.Option>
                    <Select.Option value="PATCH">PATCH</Select.Option>
                    <Select.Option value="HEAD">HEAD</Select.Option>
                    <Select.Option value="OPTIONS">OPTIONS</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="用例描述">
              <Input.TextArea
                v-model:value="state.formData.description"
                placeholder="描述此用例的测试目的、业务场景和注意事项"
                :rows="3"
              />
            </Form.Item>
          </Form>
        </Tabs.TabPane>

        <Tabs.TabPane key="request" tab="请求配置">
          <Form layout="vertical">
            <Form.Item label="请求URL" :required="state.formData.type !== 'custom'">
              <Input
                v-model:value="state.formData.url"
                :disabled="state.formData.type === 'custom'"
                placeholder="例如：https://api.example.com/v1/login"
              />
            </Form.Item>

            <Form.Item label="请求体 (Body)">
              <Input.TextArea
                v-model:value="state.formData.body"
                :rows="6"
                class="code-textarea"
                placeholder='例如：{"username":"demo","password":"123456"}'
              />
            </Form.Item>
          </Form>
        </Tabs.TabPane>

        <Tabs.TabPane key="headers" tab="请求头">
          <Table
            :columns="headerColumns"
            :data-source="state.formData.headers"
            :pagination="false"
            size="small"
            row-key="row_key"
          >
            <template #bodyCell="{ column, index }">
              <template v-if="column.key === 'name'">
                <Input
                  v-model:value="state.formData.headers[index].name"
                  placeholder="Header名称"
                  size="small"
                />
              </template>
              <template v-if="column.key === 'value'">
                <Input
                  v-model:value="state.formData.headers[index].value"
                  placeholder="Header值"
                  size="small"
                />
              </template>
              <template v-if="column.key === 'action'">
                <Button type="link" danger size="small" @click="removeHeader(index)">
                  <DeleteOutlined />
                </Button>
              </template>
            </template>
          </Table>

          <Button type="dashed" @click="addHeader" class="header-add-button">
            <PlusOutlined />
            添加请求头
          </Button>
        </Tabs.TabPane>

        <Tabs.TabPane key="advanced" tab="高级设置">
          <Form layout="vertical">
            <Form.Item label="断言脚本">
              <Input.TextArea
                v-model:value="state.formData.assertion"
                :rows="6"
                class="code-textarea"
                placeholder="// 在这里编写断言逻辑"
              />
            </Form.Item>

            <Row :gutter="16">
              <Col :span="12">
                <Form.Item label="期望状态码">
                  <Input
                    v-model:value="state.formData.expected_status"
                    placeholder="例如：200"
                  />
                </Form.Item>
              </Col>
              <Col :span="12">
                <Form.Item label="期望响应时间 (ms)">
                  <Input
                    v-model:value="state.formData.expected_response_time"
                    type="number"
                    placeholder="例如：1000"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="前置脚本">
              <Input.TextArea
                v-model:value="state.formData.pre_request_script"
                :rows="5"
                class="code-textarea"
                placeholder="// 请求发送前执行的脚本"
              />
            </Form.Item>

            <Form.Item label="后置脚本">
              <Input.TextArea
                v-model:value="state.formData.post_request_script"
                :rows="5"
                class="code-textarea"
                placeholder="// 请求结束后执行的脚本"
              />
            </Form.Item>
          </Form>
        </Tabs.TabPane>
      </Tabs>
    </Modal>

    <Modal
      v-model:open="state.importModalVisible"
      title="导入用例"
      width="1080px"
      :mask-closable="false"
      :confirm-loading="state.importSubmitLoading"
      @cancel="handleImportModalCancel"
    >
      <div class="import-layout">
        <ACard title="导入配置" size="small" class="import-config-card">
          <Form layout="vertical">
            <Row :gutter="16">
              <Col :span="12">
                <Form.Item label="所属项目" required>
                  <Select
                    v-model:value="state.importForm.project_id"
                    placeholder="请选择要导入到的项目"
                    show-search
                    option-filter-prop="label"
                  >
                    <Select.Option
                      v-for="project in state.projectOptions"
                      :key="project.id"
                      :value="project.id"
                      :label="project.name"
                    >
                      {{ project.name }}
                    </Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col :span="12">
                <Form.Item label="导入来源" required>
                  <Select v-model:value="state.importForm.source_type">
                    <Select.Option value="openapi_url">OpenAPI URL</Select.Option>
                    <Select.Option value="openapi_json">OpenAPI JSON 内容</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              v-if="state.importForm.source_type === 'openapi_url'"
              label="文档地址"
              required
            >
              <Input
                v-model:value="state.importForm.source_url"
                placeholder="例如：https://api.example.com/openapi.json"
              />
            </Form.Item>

            <Form.Item v-else label="文档内容" required>
              <Input.TextArea
                v-model:value="state.importForm.document_content"
                :rows="8"
                class="code-textarea"
                placeholder="请粘贴 OpenAPI / Swagger JSON 内容"
              />
              <div class="import-json-actions">
                <input
                  ref="importFileInputRef"
                  type="file"
                  accept=".json,application/json"
                  class="import-file-input"
                  @change="handleImportFileChange"
                />
                <Button @click="triggerImportFileSelect">
                  <template #icon><UploadOutlined /></template>
                  从文件读取 JSON
                </Button>
              </div>
            </Form.Item>

            <Row :gutter="16">
              <Col :span="12">
                <Form.Item label="冲突处理">
                  <Select v-model:value="state.importForm.conflict_policy">
                    <Select.Option value="skip">跳过已存在用例</Select.Option>
                    <Select.Option value="overwrite">覆盖已存在用例</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col :span="12">
                <Form.Item label="默认状态">
                  <Select v-model:value="state.importForm.default_status">
                    <Select.Option value="draft">草稿</Select.Option>
                    <Select.Option value="active">启用中</Select.Option>
                    <Select.Option value="inactive">已停用</Select.Option>
                    <Select.Option value="archived">已归档</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Form>
        </ACard>

        <ACard title="导入预览" size="small" class="import-preview-card">
          <template #extra>
            <Space size="middle">
              <span v-if="state.importPreviewMeta" class="import-summary">
                共 {{ state.importPreviewMeta.total_count }} 个接口，
                重复 {{ state.importPreviewMeta.duplicate_count }} 个
              </span>
              <Button :loading="state.importPreviewLoading" @click="previewImportCases">
                <template #icon><CloudDownloadOutlined /></template>
                解析预览
              </Button>
            </Space>
          </template>

          <div v-if="state.importPreviewMeta" class="import-preview-meta">
            <Tag color="blue">项目：{{ state.importPreviewMeta.project_name }}</Tag>
            <Tag color="processing">可导入：{{ state.importPreviewMeta.importable_count }}</Tag>
            <Tag color="warning">重复：{{ state.importPreviewMeta.duplicate_count }}</Tag>
          </div>

          <Table
            :columns="importColumns"
            :data-source="state.importPreviewItems"
            :pagination="false"
            :loading="state.importPreviewLoading"
            :row-selection="importRowSelection"
            :scroll="{ x: 940, y: 360 }"
            row-key="import_key"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'method'">
                <Tag :color="methodMap[record.method || '']?.color || 'default'">
                  {{ record.method }}
                </Tag>
              </template>

              <template v-if="column.key === 'url'">
                <Tooltip :title="record.url" placement="topLeft">
                  <span class="ellipsis-text">{{ truncateText(record.url, 56) }}</span>
                </Tooltip>
              </template>

              <template v-if="column.key === 'tags'">
                <Space size="small" wrap>
                  <Tag v-for="tag in record.tags" :key="tag">{{ tag }}</Tag>
                  <span v-if="record.tags.length === 0">-</span>
                </Space>
              </template>

              <template v-if="column.key === 'exists'">
                <Tag :color="record.exists ? 'warning' : 'success'">
                  {{ record.exists ? '已存在' : '新用例' }}
                </Tag>
                <div v-if="record.duplicate_case_name" class="import-duplicate-text">
                  {{ record.duplicate_case_name }}
                </div>
              </template>
            </template>

            <template #emptyText>
              <div class="empty-state compact-empty">
                <div class="empty-icon">
                  <CloudDownloadOutlined />
                </div>
                <h3>还没有导入预览结果</h3>
                <p>先选择项目和文档来源，然后点击“解析预览”。</p>
              </div>
            </template>
          </Table>
        </ACard>
      </div>

      <template #footer>
        <Space>
          <Button @click="handleImportModalCancel">取消</Button>
          <Button :loading="state.importPreviewLoading" @click="previewImportCases">
            重新预览
          </Button>
          <Button
            type="primary"
            :loading="state.importSubmitLoading"
            @click="commitImportCases"
          >
            导入选中用例
          </Button>
        </Space>
      </template>
    </Modal>

    <Modal
      v-model:open="state.previewVisible"
      title="用例详情预览"
      width="860px"
      :footer="null"
    >
      <div v-if="state.previewLoading" class="preview-loading">
        <a-spin tip="正在加载用例详情..." />
      </div>

      <Tabs v-else v-model:activeKey="state.previewTab">
        <Tabs.TabPane key="info" tab="基本信息">
          <Descriptions :column="2" bordered>
            <DescriptionsItem label="用例ID">{{ state.previewData?.id || '-' }}</DescriptionsItem>
            <DescriptionsItem label="用例名称">{{ state.previewData?.name || '-' }}</DescriptionsItem>
            <DescriptionsItem label="所属项目">{{ state.previewData?.project || '-' }}</DescriptionsItem>
            <DescriptionsItem label="用例类型">
              <Tag :color="typeMap[state.previewData?.type || '']?.color || 'default'">
                {{ typeMap[state.previewData?.type || '']?.text || state.previewData?.type || '-' }}
              </Tag>
            </DescriptionsItem>
            <DescriptionsItem label="请求方法">
              <Tag :color="methodMap[state.previewData?.method || '']?.color || 'default'">
                {{ state.previewData?.method || '-' }}
              </Tag>
            </DescriptionsItem>
            <DescriptionsItem label="用例状态">
              <Tag :color="statusMap[state.previewData?.status || '']?.color || 'default'">
                {{ statusMap[state.previewData?.status || '']?.text || state.previewData?.status || '-' }}
              </Tag>
            </DescriptionsItem>
            <DescriptionsItem label="创建时间">{{ formatDateTime(state.previewData?.created_at) }}</DescriptionsItem>
            <DescriptionsItem label="最后更新">{{ formatDateTime(state.previewData?.updated_at) }}</DescriptionsItem>
            <DescriptionsItem label="用例描述" :span="2">
              {{ state.previewData?.description || '-' }}
            </DescriptionsItem>
          </Descriptions>
        </Tabs.TabPane>

        <Tabs.TabPane key="request" tab="请求详情">
          <div class="preview-section">
            <div class="preview-section-title">请求URL</div>
            <pre class="preview-code">{{ state.previewData?.url || '自定义脚本' }}</pre>
          </div>

          <div class="preview-section">
            <div class="preview-section-title">请求头</div>
            <pre class="preview-code">{{ formatHeaders(state.previewData?.headers || []) }}</pre>
          </div>

          <div class="preview-section">
            <div class="preview-section-title">请求体</div>
            <pre class="preview-code">{{ state.previewData?.body || '无' }}</pre>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane key="script" tab="脚本代码">
          <div class="preview-section">
            <div class="preview-section-title">断言脚本</div>
            <pre class="preview-code">{{ state.previewData?.assertion || '无' }}</pre>
          </div>

          <div class="preview-section">
            <div class="preview-section-title">前置脚本</div>
            <pre class="preview-code">{{ state.previewData?.pre_request_script || '无' }}</pre>
          </div>

          <div class="preview-section">
            <div class="preview-section-title">后置脚本</div>
            <pre class="preview-code">{{ state.previewData?.post_request_script || '无' }}</pre>
          </div>
        </Tabs.TabPane>
      </Tabs>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
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
  Checkbox,
  Pagination,
  Space,
  Divider,
  Descriptions,
  DescriptionsItem,
  Tooltip,
  Tabs,
  message,
} from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  RedoOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  ApiOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  StopOutlined,
  DownloadOutlined,
  ImportOutlined,
  UploadOutlined,
  CloudDownloadOutlined,
} from '@ant-design/icons-vue'
import { CaseApi } from '@/api/case'
import { ProjectApi } from '@/api/project'
import { formatDateTime } from '@/utils/tools'
import type {
  CaseHeaderItem,
  CaseImportItem,
  CaseImportPreviewData,
  CaseImportSourceType,
  CaseInfo,
} from '@/types/case'
import type { ProjectInfo } from '@/types/project'

type CaseFormState = {
  name: string
  project_id: number | undefined
  project: string
  type: string
  status: string
  description: string
  method: string
  url: string
  headers: Array<CaseHeaderItem & { row_key: string }>
  body: string
  assertion: string
  expected_status: string
  expected_response_time: number | null
  pre_request_script: string
  post_request_script: string
}

type CaseImportFormState = {
  project_id: number | undefined
  source_type: CaseImportSourceType
  source_url: string
  document_content: string
  conflict_policy: 'skip' | 'overwrite'
  default_status: string
}

type ImportPreviewItem = CaseImportItem & {
  import_key: string
}

const createDefaultHeaders = () => [
  { row_key: crypto.randomUUID(), name: 'User-Agent', value: 'Falcon/1.0' },
  { row_key: crypto.randomUUID(), name: 'Content-Type', value: 'application/json' },
]

const createDefaultFormData = (): CaseFormState => ({
  name: '',
  project_id: undefined,
  project: '',
  type: 'http',
  status: 'draft',
  description: '',
  method: 'POST',
  url: '',
  headers: createDefaultHeaders(),
  body: '',
  assertion: '',
  expected_status: '',
  expected_response_time: null,
  pre_request_script: '',
  post_request_script: '',
})

const createDefaultImportFormData = (): CaseImportFormState => ({
  project_id: undefined,
  source_type: 'openapi_url',
  source_url: '',
  document_content: '',
  conflict_policy: 'skip',
  default_status: 'draft',
})

const normalizeHeaders = (headers: CaseInfo['headers']): Array<CaseHeaderItem & { row_key: string }> => {
  if (!Array.isArray(headers)) {
    return []
  }

  return headers.map(item => ({
    row_key: crypto.randomUUID(),
    name: item.name || '',
    value: item.value || '',
  }))
}

const normalizeCase = (testcase: CaseInfo): CaseInfo => ({
  ...testcase,
  status: testcase.status?.toLowerCase() || 'draft',
  headers: Array.isArray(testcase.headers) ? testcase.headers : [],
})

const state = reactive({
  testcases: [] as CaseInfo[],
  projectOptions: [] as ProjectInfo[],
  currentPage: 1,
  pageSize: 8,
  total: 0,
  listLoading: false,
  submitLoading: false,
  searchFilters: {
    name: '',
    project_id: undefined as number | undefined,
    type: '',
    status: '',
  },
  selectedCaseIds: [] as number[],
  isAllSelected: false,
  modalVisible: false,
  modalTitle: '创建新用例',
  isEditing: false,
  currentEditId: null as number | null,
  activeTab: 'basic',
  previewVisible: false,
  previewLoading: false,
  previewTab: 'info',
  previewData: null as CaseInfo | null,
  formData: createDefaultFormData(),
  importModalVisible: false,
  importPreviewLoading: false,
  importSubmitLoading: false,
  importPreviewItems: [] as ImportPreviewItem[],
  importPreviewMeta: null as CaseImportPreviewData | null,
  selectedImportKeys: [] as string[],
  importForm: createDefaultImportFormData(),
})

const importFileInputRef = ref<HTMLInputElement | null>(null)

const rowSelection = computed(() => ({
  selectedRowKeys: state.selectedCaseIds,
  onChange: (selectedRowKeys: number[]) => {
    state.selectedCaseIds = selectedRowKeys
    state.isAllSelected = selectedRowKeys.length > 0 && selectedRowKeys.length === state.testcases.length
  },
}))

const importRowSelection = computed(() => ({
  selectedRowKeys: state.selectedImportKeys,
  onChange: (selectedRowKeys: string[]) => {
    state.selectedImportKeys = selectedRowKeys
  },
}))

const statusMap: Record<string, { text: string; color: string }> = {
  draft: { text: '草稿', color: 'default' },
  active: { text: '启用中', color: 'green' },
  inactive: { text: '已停用', color: 'orange' },
  archived: { text: '已归档', color: 'purple' },
}

const typeMap: Record<string, { text: string; color: string }> = {
  http: { text: 'HTTP', color: 'blue' },
  websocket: { text: 'WebSocket', color: 'purple' },
  grpc: { text: 'gRPC', color: 'orange' },
  custom: { text: '自定义', color: 'cyan' },
}

const methodMap: Record<string, { color: string }> = {
  GET: { color: 'green' },
  POST: { color: 'blue' },
  PUT: { color: 'orange' },
  DELETE: { color: 'red' },
  PATCH: { color: 'purple' },
  HEAD: { color: 'cyan' },
  OPTIONS: { color: 'geekblue' },
}

const columns = [
  {
    title: '用例ID',
    dataIndex: 'id',
    key: 'id',
    width: 130,
  },
  {
    title: '用例名称',
    dataIndex: 'name',
    key: 'name',
    width: 180,
  },
  {
    title: '所属项目',
    dataIndex: 'project',
    key: 'project',
    width: 140,
  },
  {
    title: '类型',
    key: 'type',
    width: 100,
  },
  {
    title: '方法',
    key: 'method',
    width: 100,
  },
  {
    title: '请求URL/描述',
    key: 'url',
    width: 240,
  },
  {
    title: '状态',
    key: 'status',
    width: 110,
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    fixed: 'right',
  },
]

const headerColumns = [
  {
    title: 'Header 名称',
    key: 'name',
    width: '40%',
  },
  {
    title: 'Header 值',
    key: 'value',
    width: '50%',
  },
  {
    title: '操作',
    key: 'action',
    width: '10%',
  },
]

const importColumns = [
  {
    title: '接口名称',
    dataIndex: 'name',
    key: 'name',
    width: 220,
  },
  {
    title: '方法',
    key: 'method',
    width: 100,
  },
  {
    title: '请求路径',
    key: 'url',
    width: 280,
  },
  {
    title: '标签',
    key: 'tags',
    width: 180,
  },
  {
    title: '导入状态',
    key: 'exists',
    width: 140,
  },
]

const truncateText = (text: string, maxLength: number) => {
  if (!text) {
    return ''
  }
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text
}

const formatHeaders = (headers: CaseInfo['headers']) => {
  if (!headers || headers.length === 0) {
    return '无'
  }
  return headers.map(item => `${item.name}: ${item.value}`).join('\n')
}

const getImportItemKey = (item: Pick<CaseImportItem, 'method' | 'url' | 'name'>) => {
  return `${item.method}::${item.url}::${item.name}`
}

const normalizeImportPreviewData = (data: CaseImportPreviewData) => ({
  ...data,
  results: data.results.map(item => ({
    ...item,
    tags: Array.isArray(item.tags) ? item.tags : [],
    headers: Array.isArray(item.headers) ? item.headers : [],
    import_key: getImportItemKey(item),
  })),
})

const syncSelectState = () => {
  state.isAllSelected = state.testcases.length > 0 && state.selectedCaseIds.length === state.testcases.length
}

const fetchProjectOptions = async () => {
  try {
    const response = await ProjectApi.getProjectList({
      page: 1,
      page_size: 200,
    })
    state.projectOptions = response.data.results
  } catch (error) {
    console.error('获取项目列表失败:', error)
    message.error('项目选项加载失败，请稍后重试')
  }
}

const fetchCaseList = async () => {
  state.listLoading = true
  try {
    const response = await CaseApi.getCaseList({
      page: state.currentPage,
      page_size: state.pageSize,
      name: state.searchFilters.name || undefined,
      project_id: state.searchFilters.project_id,
      type: state.searchFilters.type || undefined,
      status: state.searchFilters.status || undefined,
    })

    state.testcases = response.data.results.map(normalizeCase)
    state.total = response.data.total
    state.selectedCaseIds = state.selectedCaseIds.filter(id =>
      state.testcases.some(item => item.id === id)
    )
    syncSelectState()
  } catch (error) {
    console.error('获取用例列表失败:', error)
    message.error('用例列表加载失败，请稍后重试')
  } finally {
    state.listLoading = false
  }
}

const getSelectedProject = (projectId?: number) => {
  return state.projectOptions.find(item => item.id === projectId)
}

const loadCaseDetail = async (caseId: number) => {
  const response = await CaseApi.getCaseInfo({ id: caseId })
  return normalizeCase(response.data)
}

const applyFilters = async () => {
  state.currentPage = 1
  await fetchCaseList()
}

const resetFilters = async () => {
  state.searchFilters = {
    name: '',
    project_id: undefined,
    type: '',
    status: '',
  }
  state.currentPage = 1
  state.selectedCaseIds = []
  state.isAllSelected = false
  await fetchCaseList()
}

const handlePageChange = async (page: number, pageSize: number) => {
  state.currentPage = page
  state.pageSize = pageSize
  await fetchCaseList()
}

const handleProjectChange = (projectId: number) => {
  const project = getSelectedProject(projectId)
  state.formData.project_id = project?.id
  state.formData.project = project?.name || ''
}

const handleTypeChange = (value: string) => {
  if (value === 'custom') {
    state.formData.method = 'POST'
    state.formData.url = ''
  } else if (!state.formData.method) {
    state.formData.method = 'POST'
  }
}

const addHeader = () => {
  state.formData.headers.push({
    row_key: crypto.randomUUID(),
    name: '',
    value: '',
  })
}

const removeHeader = (index: number) => {
  state.formData.headers.splice(index, 1)
}

const showAddModal = () => {
  state.modalTitle = '创建新用例'
  state.isEditing = false
  state.currentEditId = null
  state.activeTab = 'basic'
  state.formData = createDefaultFormData()
  state.modalVisible = true
}

const resetImportState = () => {
  state.importForm = createDefaultImportFormData()
  state.importPreviewItems = []
  state.importPreviewMeta = null
  state.selectedImportKeys = []
  state.importPreviewLoading = false
  state.importSubmitLoading = false
  if (importFileInputRef.value) {
    importFileInputRef.value.value = ''
  }
}

const showImportModal = () => {
  resetImportState()
  state.importModalVisible = true
}

const handleImportModalCancel = () => {
  state.importModalVisible = false
}

const triggerImportFileSelect = () => {
  importFileInputRef.value?.click()
}

const handleImportFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) {
    return
  }

  try {
    state.importForm.document_content = await file.text()
    message.success(`已加载文件：${file.name}`)
  } catch (error) {
    console.error('读取导入文件失败:', error)
    message.error('读取文件失败，请重试')
  } finally {
    target.value = ''
  }
}

const validateImportForm = () => {
  if (!state.importForm.project_id) {
    message.error('请选择要导入到的项目')
    return false
  }

  if (state.importForm.source_type === 'openapi_url' && !state.importForm.source_url.trim()) {
    message.error('请输入 OpenAPI 文档地址')
    return false
  }

  if (
    state.importForm.source_type === 'openapi_json'
    && !state.importForm.document_content.trim()
  ) {
    message.error('请输入或加载 OpenAPI JSON 内容')
    return false
  }

  return true
}

const previewImportCases = async () => {
  if (!validateImportForm()) {
    return
  }

  state.importPreviewLoading = true
  try {
    const response = await CaseApi.previewImport({
      project_id: state.importForm.project_id!,
      source_type: state.importForm.source_type,
      source_url: state.importForm.source_type === 'openapi_url'
        ? state.importForm.source_url.trim()
        : undefined,
      document_content: state.importForm.source_type === 'openapi_json'
        ? state.importForm.document_content
        : undefined,
    })

    const previewData = normalizeImportPreviewData(response.data)
    state.importPreviewMeta = {
      ...previewData,
      results: previewData.results.map(({ import_key, ...item }) => item),
    }
    state.importPreviewItems = previewData.results
    state.selectedImportKeys = previewData.results.map(item => item.import_key)
    message.success(`已解析 ${previewData.total_count} 个接口`)
  } catch (error) {
    console.error('预览导入用例失败:', error)
    message.error('导入预览失败，请检查文档内容后重试')
  } finally {
    state.importPreviewLoading = false
  }
}

const commitImportCases = async () => {
  if (!validateImportForm()) {
    return
  }

  const selectedItems = state.importPreviewItems
    .filter(item => state.selectedImportKeys.includes(item.import_key))
    .map(({ import_key, ...item }) => item)

  if (selectedItems.length === 0) {
    message.error('请至少选择一个要导入的接口')
    return
  }

  state.importSubmitLoading = true
  try {
    const response = await CaseApi.commitImport({
      project_id: state.importForm.project_id!,
      source_type: state.importForm.source_type,
      source_url: state.importForm.source_type === 'openapi_url'
        ? state.importForm.source_url.trim()
        : undefined,
      document_content: state.importForm.source_type === 'openapi_json'
        ? state.importForm.document_content
        : undefined,
      items: selectedItems,
      conflict_policy: state.importForm.conflict_policy,
      default_status: state.importForm.default_status,
    })

    const result = response.data
    message.success(
      `导入完成：新增 ${result.created_count}，覆盖 ${result.updated_count}，跳过 ${result.skipped_count}`
    )
    state.importModalVisible = false
    await fetchCaseList()
  } catch (error) {
    console.error('提交导入失败:', error)
    message.error('导入用例失败，请稍后重试')
  } finally {
    state.importSubmitLoading = false
  }
}

const fillFormData = (testcase: CaseInfo) => {
  state.formData = {
    name: testcase.name,
    project_id: testcase.project_id,
    project: testcase.project,
    type: testcase.type,
    status: testcase.status,
    description: testcase.description || '',
    method: testcase.method || 'POST',
    url: testcase.url || '',
    headers: normalizeHeaders(testcase.headers),
    body: testcase.body || '',
    assertion: testcase.assertion || '',
    expected_status: testcase.expected_status || '',
    expected_response_time: testcase.expected_response_time || null,
    pre_request_script: testcase.pre_request_script || '',
    post_request_script: testcase.post_request_script || '',
  }
}

const showEditModal = async (caseId: number) => {
  try {
    const testcase = await loadCaseDetail(caseId)
    state.modalTitle = '编辑用例'
    state.isEditing = true
    state.currentEditId = caseId
    state.activeTab = 'basic'
    fillFormData(testcase)
    state.modalVisible = true
  } catch (error) {
    console.error('获取用例详情失败:', error)
    message.error('用例详情加载失败，请稍后重试')
  }
}

const buildConfigPayload = (caseId: number) => ({
  id: caseId,
  headers: state.formData.headers
    .map(({ name, value }) => ({ name: name.trim(), value: value.trim() }))
    .filter(item => item.name || item.value),
  body: state.formData.body || undefined,
  expected_status: state.formData.expected_status || undefined,
  expected_response_time: state.formData.expected_response_time,
  assertion: state.formData.assertion || undefined,
  pre_request_script: state.formData.pre_request_script || undefined,
  post_request_script: state.formData.post_request_script || undefined,
})

const validateForm = () => {
  if (!state.formData.name.trim()) {
    message.error('请输入用例名称')
    return false
  }

  if (!state.formData.project_id || !state.formData.project) {
    message.error('请选择所属项目')
    return false
  }

  if (state.formData.type !== 'custom' && !state.formData.url.trim()) {
    message.error('请输入请求URL')
    return false
  }

  return true
}

const handleModalOk = async () => {
  if (!validateForm()) {
    return
  }

  state.submitLoading = true
  try {
    let caseId = state.currentEditId

    if (state.isEditing && state.currentEditId) {
      await CaseApi.updateCase({
        id: state.currentEditId,
        name: state.formData.name.trim(),
        type: state.formData.type,
        project_id: state.formData.project_id,
        project: state.formData.project,
        method: state.formData.method,
        url: state.formData.type === 'custom' ? '' : state.formData.url.trim(),
        description: state.formData.description || undefined,
        status: state.formData.status,
      })
    } else {
      const response = await CaseApi.createCase({
        name: state.formData.name.trim(),
        type: state.formData.type,
        project_id: state.formData.project_id!,
        project: state.formData.project,
        method: state.formData.method,
        url: state.formData.type === 'custom' ? '' : state.formData.url.trim(),
        description: state.formData.description || undefined,
      })
      caseId = response.data.id

      if (state.formData.status !== 'draft') {
        await CaseApi.updateCase({
          id: caseId,
          status: state.formData.status,
        })
      }
    }

    if (caseId) {
      await CaseApi.configCase(buildConfigPayload(caseId))
    }

    message.success(state.isEditing ? '用例已更新' : '用例已创建')
    state.modalVisible = false
    await fetchCaseList()
  } catch (error) {
    console.error('保存用例失败:', error)
    message.error('保存用例失败，请稍后重试')
  } finally {
    state.submitLoading = false
  }
}

const handleModalCancel = () => {
  state.modalVisible = false
}

const previewCase = async (caseId: number) => {
  state.previewVisible = true
  state.previewLoading = true
  state.previewTab = 'info'
  try {
    state.previewData = await loadCaseDetail(caseId)
  } catch (error) {
    console.error('预览用例失败:', error)
    message.error('用例详情加载失败，请稍后重试')
    state.previewVisible = false
  } finally {
    state.previewLoading = false
  }
}

const copyCase = async (caseId: number) => {
  try {
    const testcase = await loadCaseDetail(caseId)
    const createResponse = await CaseApi.createCase({
      name: `${testcase.name} (副本)`,
      type: testcase.type,
      project_id: testcase.project_id,
      project: testcase.project,
      method: testcase.method || 'POST',
      url: testcase.url || '',
      description: testcase.description || undefined,
    })

    await CaseApi.configCase({
      id: createResponse.data.id,
      headers: Array.isArray(testcase.headers) ? testcase.headers : undefined,
      body: testcase.body || undefined,
      expected_status: testcase.expected_status || undefined,
      expected_response_time: testcase.expected_response_time,
      assertion: testcase.assertion || undefined,
      pre_request_script: testcase.pre_request_script || undefined,
      post_request_script: testcase.post_request_script || undefined,
      extract: testcase.extract || undefined,
    })

    if (testcase.status && testcase.status !== 'draft') {
      await CaseApi.updateCase({
        id: createResponse.data.id,
        status: testcase.status,
      })
    }

    message.success(`用例 "${testcase.name}" 已复制`)
    await fetchCaseList()
  } catch (error) {
    console.error('复制用例失败:', error)
    message.error('复制用例失败，请稍后重试')
  }
}

const deleteCase = async (caseId: number) => {
  const testcase = state.testcases.find(item => item.id === caseId)
  if (!testcase) {
    return
  }

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除用例 "${testcase.name}" 吗？此操作不可恢复。`,
    okType: 'danger',
    async onOk() {
      await CaseApi.deleteCase({ id: caseId })
      message.success(`用例 "${testcase.name}" 已删除`)
      await fetchCaseList()
    },
  })
}

const toggleSelectAll = (event: { target: { checked: boolean } }) => {
  if (event.target.checked) {
    state.selectedCaseIds = state.testcases.map(item => item.id)
  } else {
    state.selectedCaseIds = []
  }
  syncSelectState()
}

const batchUpdateStatus = async (status: string) => {
  if (state.selectedCaseIds.length === 0) {
    return
  }

  const statusText = statusMap[status]?.text || status
  Modal.confirm({
    title: `确认批量更新状态`,
    content: `确定要将选中的 ${state.selectedCaseIds.length} 个用例设置为“${statusText}”吗？`,
    async onOk() {
      await Promise.all(
        state.selectedCaseIds.map(id =>
          CaseApi.updateCase({
            id,
            status,
          })
        )
      )
      message.success(`已更新 ${state.selectedCaseIds.length} 个用例状态`)
      state.selectedCaseIds = []
      syncSelectState()
      await fetchCaseList()
    },
  })
}

const batchDeleteCases = async () => {
  if (state.selectedCaseIds.length === 0) {
    return
  }

  Modal.confirm({
    title: '确认批量删除',
    content: `确定要删除选中的 ${state.selectedCaseIds.length} 个用例吗？此操作不可恢复。`,
    okType: 'danger',
    async onOk() {
      await Promise.all(state.selectedCaseIds.map(id => CaseApi.deleteCase({ id })))
      message.success(`已删除 ${state.selectedCaseIds.length} 个用例`)
      state.selectedCaseIds = []
      syncSelectState()
      await fetchCaseList()
    },
  })
}

const batchExportCases = () => {
  if (state.selectedCaseIds.length === 0) {
    return
  }
  message.info(`已选中 ${state.selectedCaseIds.length} 个用例，导出功能将在下一轮接入文件下载。`)
}

onMounted(async () => {
  await fetchProjectOptions()
  await fetchCaseList()
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

.batch-actions-card {
  margin-bottom: 20px;
  background-color: #fafafa;
}

.batch-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.batch-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.selected-count {
  margin-left: auto;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.selected-count span {
  color: #1677ff;
  font-weight: 600;
}

.ellipsis-text {
  color: rgba(0, 0, 0, 0.75);
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.header-add-button {
  width: 100%;
  margin-top: 16px;
}

.import-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.import-config-card,
.import-preview-card {
  border-radius: 10px;
}

.import-json-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.import-file-input {
  display: none;
}

.import-preview-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.import-summary {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
}

.import-duplicate-text {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.code-textarea {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.preview-loading {
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-section {
  margin-bottom: 16px;
}

.preview-section-title {
  font-weight: 500;
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.85);
}

.preview-code {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  background-color: #fafafa;
  color: rgba(0, 0, 0, 0.85);
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0;
  border: 1px solid #f0f0f0;
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

.compact-empty {
  padding: 24px 0;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .batch-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .selected-count {
    margin-left: 0;
  }
}
</style>
