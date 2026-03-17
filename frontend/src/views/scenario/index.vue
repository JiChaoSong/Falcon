<template>
  <div class="app-container">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <div class="page-title-section">
        <h1 class="page-title">场景管理</h1>
        <p class="page-subtitle">压测场景配置、用例编排、权重分配，为任务执行提供场景模板</p>
      </div>

      <Space>
        <!-- 视图切换 -->
        <Button.Group v-show="false">
          <Button
              :type="state.viewMode === 'card' ? 'primary' : 'default'"
              @click="switchView('card')"
          >
            <template #icon><AppstoreOutlined /></template>
            卡片视图
          </Button>
          <Button
              :type="state.viewMode === 'table' ? 'primary' : 'default'"
              @click="switchView('table')"
          >
            <template #icon><UnorderedListOutlined /></template>
            表格视图
          </Button>
        </Button.Group>

        <!-- 新增场景按钮 -->
        <Button type="primary" @click="showAddModal">
          <template #icon><PlusOutlined /></template>
          新增场景
        </Button>
      </Space>
    </div>

<!--    &lt;!&ndash; 统计卡片 &ndash;&gt;-->
<!--    <Row :gutter="16" class="stats-row">-->
<!--      <Col :span="6">-->
<!--        <ACard>-->
<!--          <Statistic-->
<!--              title="场景总数"-->
<!--              :value="statistics.total"-->
<!--              :value-style="{ color: '#1890ff', fontSize: '24px' }"-->
<!--          >-->
<!--            <template #prefix><ApiOutlined /></template>-->
<!--            <template #suffix>-->
<!--              <span style="font-size: 12px; color: #666">较上月 +8</span>-->
<!--            </template>-->
<!--          </Statistic>-->
<!--        </ACard>-->
<!--      </Col>-->
<!--      <Col :span="6">-->
<!--        <ACard>-->
<!--          <Statistic-->
<!--              title="活跃场景"-->
<!--              :value="statistics.active"-->
<!--              :value-style="{ color: '#52c41a', fontSize: '24px' }"-->
<!--          >-->
<!--            <template #prefix><PlayCircleOutlined /></template>-->
<!--            <template #suffix>-->
<!--              <span style="font-size: 12px; color: #666">较上月 +3</span>-->
<!--            </template>-->
<!--          </Statistic>-->
<!--        </ACard>-->
<!--      </Col>-->
<!--      <Col :span="6">-->
<!--        <ACard>-->
<!--          <Statistic-->
<!--              title="用例总数"-->
<!--              :value="statistics.totalTestcases"-->
<!--              :value-style="{ color: '#faad14', fontSize: '24px' }"-->
<!--          >-->
<!--            <template #prefix><UnorderedListOutlined /></template>-->
<!--            <template #suffix>-->
<!--              <span style="font-size: 12px; color: #666">较上月 +15</span>-->
<!--            </template>-->
<!--          </Statistic>-->
<!--        </ACard>-->
<!--      </Col>-->
<!--      <Col :span="6">-->
<!--        <ACard>-->
<!--          <Statistic-->
<!--              title="执行次数"-->
<!--              :value="statistics.totalRuns"-->
<!--              :value-style="{ color: '#13c2c2', fontSize: '24px' }"-->
<!--          >-->
<!--            <template #prefix><ScheduleOutlined /></template>-->
<!--            <template #suffix>-->
<!--              <span style="font-size: 12px; color: #666">较上月 +24</span>-->
<!--            </template>-->
<!--          </Statistic>-->
<!--        </ACard>-->
<!--      </Col>-->
<!--    </Row>-->

    <!-- 筛选区域 -->
    <ACard title="场景筛选" class="filter-card">
      <template #extra><FilterOutlined /></template>

      <Row :gutter="16">
        <Col :span="6">
          <Input
              v-model:value="state.searchFilters.name"
              placeholder="输入场景名称关键字"
              allow-clear
              @pressEnter="applyFilters"
          />
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.project"
              placeholder="所属项目"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部项目</Select.Option>
            <Select.Option v-for="project in projectOptions" :key="project" :value="project">
              {{ project }}
            </Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.status"
              placeholder="场景状态"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部状态</Select.Option>
            <Select.Option value="active">启用中</Select.Option>
            <Select.Option value="draft">草稿</Select.Option>
            <Select.Option value="inactive">已停用</Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.time"
              placeholder="创建时间"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部时间</Select.Option>
            <Select.Option value="today">今天</Select.Option>
            <Select.Option value="week">本周</Select.Option>
            <Select.Option value="month">本月</Select.Option>
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

    <!-- 场景展示区域 -->
    <div v-if="state.viewMode === 'card'">
      <!-- 卡片视图 -->
      <Row :gutter="[16, 16]" v-if="paginatedScenarios.length > 0">
        <Col :span="8" v-for="scenario in paginatedScenarios" :key="scenario.id">
          <ACard class="scenario-card" hoverable>
            <template #title>
              <div class="scenario-card-header">
                <h3 class="scenario-name">{{ scenario.name }}</h3>
                <div class="scenario-id">{{ scenario.id }}</div>
              </div>
            </template>

            <template #extra>
              <Tag :color="statusMap[scenario.status].color">
                {{ statusMap[scenario.status].text }}
              </Tag>
            </template>

            <div class="scenario-description">{{ scenario.description }}</div>

            <div class="scenario-meta">
              <div class="meta-item">
                <span class="meta-label">所属项目</span>
                <div class="meta-value">
                  <ProjectOutlined style="margin-right: 4px" />
                  {{ scenario.project }}
                </div>
              </div>

              <div class="meta-item">
                <span class="meta-label">用例数量</span>
                <div class="meta-value">{{ scenario.totalTestcases }}</div>
              </div>

              <div class="meta-item">
                <span class="meta-label">创建时间</span>
                <div class="meta-value">{{ scenario.createdAt.split(' ')[0] }}</div>
              </div>

              <div class="meta-item">
                <span class="meta-label">最后修改</span>
                <div class="meta-value">{{ scenario.updatedAt.split(' ')[0] }}</div>
              </div>
            </div>

            <!-- 测试用例预览 -->
            <ACard size="small" class="testcases-preview">
              <template #title>
                <div class="testcases-title">
                  <span>测试用例配置 {{ scenario.testcases.length > 3 ? `等 ${scenario.testcases.length} 个用例` : '' }}</span>
                  <Tag color="blue" class="testcases-count">{{ scenario.testcases.length }}</Tag>
                </div>
              </template>

              <div class="testcases-list">
                <div
                    v-for="(tc, index) in scenario.testcases.slice(0, 3)"
                    :key="tc.id"
                    class="testcase-item"
                >
                  <span class="testcase-name">{{ tc.name }}</span>
                  <Tag color="orange" class="testcase-weight">{{ tc.weight }}%</Tag>
                </div>
              </div>
            </ACard>

            <template #actions>
              <Tooltip title="编辑">
                <Button type="link" @click="showEditModal(scenario.id)">
                  <template #icon><EditOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="运行">
                <Button type="link" @click="runScenario(scenario.id)">
                  <template #icon><PlayCircleOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="复制">
                <Button type="link" @click="copyScenario(scenario.id)">
                  <template #icon><CopyOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="删除">
                <Button type="link" danger @click="deleteScenario(scenario.id)">
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Tooltip>
            </template>
          </ACard>
        </Col>
      </Row>

      <!-- 卡片视图空状态 -->
      <div v-if="paginatedScenarios.length === 0" class="empty-state">
        <div class="empty-icon">
          <ApiOutlined />
        </div>
        <h3>暂无场景数据</h3>
        <p>当前没有找到符合筛选条件的场景，请尝试调整筛选条件或创建新的压测场景。</p>
        <Button type="primary" @click="showAddModal">
          <template #icon><PlusOutlined /></template>
          新增场景
        </Button>
      </div>
    </div>

    <!-- 表格视图 -->
    <div v-else>
      <ACard>
        <Table
            :columns="columns"
            :data-source="paginatedScenarios"
            :pagination="false"
            row-key="id"
            :scroll="{x: 1300}"
        >
          <template #emptyText>
            <div class="empty-state">
              <div class="empty-icon">
                <ApiOutlined />
              </div>
              <h3>暂无场景数据</h3>
              <p>当前没有找到符合筛选条件的场景，请尝试调整筛选条件或创建新的压测场景。</p>
              <Button type="primary" @click="showAddModal">
                <template #icon><PlusOutlined /></template>
                新增场景
              </Button>
            </div>
          </template>

          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <Tag :color="statusMap[record.status].color">
                {{ statusMap[record.status].text }}
              </Tag>
            </template>

            <template v-if="column.key === 'testcases'">
              <div>
                <div style="margin-bottom: 4px">{{ record.totalTestcases }} 个用例</div>
                <div style="font-size: 12px; color: #666">
                  {{ record.testcases.slice(0, 2).map(tc => `${tc.name}(${tc.weight}%)`).join(', ') }}
                  {{ record.testcases.length > 2 ? '...' : '' }}
                </div>
              </div>
            </template>

            <template v-if="column.key === 'actions'">
              <Space size="small">
                <Tooltip title="编辑">
                  <Button type="link" size="small" @click="showEditModal(record.id)">
                    <template #icon><EditOutlined /></template>
                  </Button>
                </Tooltip>
                <Tooltip title="运行">
                  <Button type="link" size="small" @click="runScenario(record.id)">
                    <template #icon><PlayCircleOutlined /></template>
                  </Button>
                </Tooltip>
                <Tooltip title="复制">
                  <Button type="link" size="small" @click="copyScenario(record.id)">
                    <template #icon><CopyOutlined /></template>
                  </Button>
                </Tooltip>
                <Tooltip title="删除">
                  <Button type="link" size="small" danger @click="deleteScenario(record.id)">
                    <template #icon><DeleteOutlined /></template>
                  </Button>
                </Tooltip>
              </Space>
            </template>
          </template>
        </Table>
      </ACard>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="state.filteredScenarios.length > 0">
      <Pagination
          v-model:current="state.currentPage"
          v-model:pageSize="state.pageSize"
          :total="state.filteredScenarios.length"
          show-quick-jumper
          show-size-changer
          :show-total="(total: number) => `共 ${total} 条`"
      />
    </div>

    <!-- 新增/编辑场景模态框 -->
    <Modal
        v-model:visible="state.modalVisible"
        :title="state.modalTitle"
        width="800px"
        @ok="handleModalOk"
        @cancel="state.modalVisible = false"
        :confirm-loading="state.modalLoading"
    >
      <Form layout="vertical">
        <Form.Item label="场景名称" required>
          <Input
              v-model:value="state.formData.name"
              placeholder="例如：首页访问场景"
          />
        </Form.Item>

        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="所属项目" required>
              <Select v-model:value="state.formData.project">
                <Select.Option value="">请选择项目</Select.Option>
                <Select.Option value="电商平台">电商平台</Select.Option>
                <Select.Option value="API网关">API网关</Select.Option>
                <Select.Option value="用户中心">用户中心</Select.Option>
                <Select.Option value="支付系统">支付系统</Select.Option>
                <Select.Option value="搜索引擎">搜索引擎</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="场景状态">
              <Select v-model:value="state.formData.status">
                <Select.Option value="active">启用中</Select.Option>
                <Select.Option value="draft">草稿</Select.Option>
                <Select.Option value="inactive">已停用</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="场景描述">
          <Input.TextArea
              v-model:value="state.formData.description"
              placeholder="描述此场景的用途、测试目标和注意事项..."
              :rows="4"
          />
        </Form.Item>

        <Form.Item label="测试用例配置" required>
          <div class="testcase-config-header">
            <span>测试用例列表</span>
            <Button type="dashed" @click="addTestCaseRow" size="small">
              <template #icon><PlusOutlined /></template>
              添加用例
            </Button>
          </div>

          <div v-for="(testcase, index) in state.formData.testcases" :key="index" class="testcase-config-row">
            <Row :gutter="8" align="middle">
              <Col :span="12">
                <Select
                    v-model:value="testcase.id"
                    placeholder="请选择测试用例"
                    style="width: 100%"
                    @change="updateWeightTotal"
                >
                  <Select.Option value="">请选择测试用例</Select.Option>
                  <Select.Option v-for="tc in testCaseOptions" :key="tc.id" :value="tc.id">
                    {{ tc.name }}
                  </Select.Option>
                </Select>
              </Col>
              <Col :span="8">
                <InputNumber
                    v-model:value="testcase.weight"
                    placeholder="权重%"
                    :min="1"
                    :max="100"
                    style="width: 100%"
                    @change="updateWeightTotal"
                />
              </Col>
              <Col :span="4">
                <Button
                    danger
                    @click="removeTestCaseRow(index)"
                    size="small"
                    :disabled="state.formData.testcases.length <= 1"
                >
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Col>
            </Row>
          </div>

          <div class="weight-total">
            提示：所有用例权重总和应为100%，当前总和:
            <span :style="{ color: state.weightTotal === 100 ? '#52c41a' : '#ff4d4f' }">
              {{ state.weightTotal }}
            </span>%
          </div>
        </Form.Item>
      </Form>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import {
  Card as ACard,
  Row,
  Col,
  Button,
  Input,
  Select,
  Table,
  Tag,
  Avatar,
  Statistic,
  Modal,
  Form,
  InputNumber,
  Pagination,
  Space,
  Divider,
  Descriptions,
  DescriptionsItem,
  Tooltip,
  message
} from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  RedoOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  ProjectOutlined,
  PlayCircleOutlined,
  ApiOutlined,
  ScheduleOutlined,
  FilterOutlined,
  CopyOutlined
} from '@ant-design/icons-vue'

// 模拟测试用例数据
const mockTestCases = [
  { id: "TC-001", name: "首页加载", description: "模拟用户访问首页" },
  { id: "TC-002", name: "商品分类浏览", description: "浏览商品分类列表" },
  { id: "TC-003", name: "轮播图切换", description: "切换首页轮播图" },
  { id: "TC-004", name: "公告信息获取", description: "获取首页公告信息" },
  { id: "TC-005", name: "商品详情页", description: "查看商品详细信息" },
  { id: "TC-006", name: "加入购物车", description: "将商品加入购物车" },
  { id: "TC-007", name: "购物车结算", description: "购物车页面结算操作" },
  { id: "TC-008", name: "提交订单", description: "提交订单到系统" },
  { id: "TC-009", name: "支付流程", description: "完成支付操作" },
  { id: "TC-010", name: "用户登录", description: "用户登录系统" }
]

// 完整模拟场景数据
const mockScenarios = [
  {
    id: "SCENARIO-001",
    name: "首页访问场景",
    project: "电商平台",
    description: "模拟用户访问电商首页的完整流程，包括页面加载、资源请求和用户交互",
    status: "active",
    testcases: [
      { id: "TC-001", name: "首页加载", weight: 60 },
      { id: "TC-002", name: "商品分类浏览", weight: 20 },
      { id: "TC-003", name: "轮播图切换", weight: 10 },
      { id: "TC-004", name: "公告信息获取", weight: 10 }
    ],
    createdAt: "2024-01-20 10:30:00",
    updatedAt: "2024-01-20 14:15:00",
    totalTestcases: 4,
    lastRun: "2024-01-20 11:00:00"
  },
  {
    id: "SCENARIO-002",
    name: "下单流程场景",
    project: "电商平台",
    description: "完整的购物下单流程，从商品选择到支付完成",
    status: "active",
    testcases: [
      { id: "TC-005", name: "商品详情页", weight: 20 },
      { id: "TC-006", name: "加入购物车", weight: 20 },
      { id: "TC-007", name: "购物车结算", weight: 20 },
      { id: "TC-008", name: "提交订单", weight: 20 },
      { id: "TC-009", name: "支付流程", weight: 20 }
    ],
    createdAt: "2024-01-19 09:15:00",
    updatedAt: "2024-01-19 16:45:00",
    totalTestcases: 5,
    lastRun: "2024-01-19 14:00:00"
  },
  {
    id: "SCENARIO-003",
    name: "用户登录注册场景",
    project: "用户中心",
    description: "用户登录、注册、找回密码等核心功能测试",
    status: "active",
    testcases: [
      { id: "TC-010", name: "用户登录", weight: 50 },
      { id: "TC-011", name: "用户注册", weight: 30 },
      { id: "TC-012", name: "密码重置", weight: 20 }
    ],
    createdAt: "2024-01-18 14:20:00",
    updatedAt: "2024-01-19 10:30:00",
    totalTestcases: 3,
    lastRun: "2024-01-18 15:45:00"
  },
  {
    id: "SCENARIO-004",
    name: "API网关压力测试",
    project: "API网关",
    description: "API网关的高并发场景测试，验证网关的吞吐量和响应时间",
    status: "draft",
    testcases: [
      { id: "TC-013", name: "健康检查接口", weight: 10 },
      { id: "TC-014", name: "用户信息查询", weight: 30 },
      { id: "TC-015", name: "订单状态查询", weight: 30 },
      { id: "TC-016", name: "商品库存查询", weight: 30 }
    ],
    createdAt: "2024-01-17 11:10:00",
    updatedAt: "2024-01-17 16:20:00",
    totalTestcases: 4,
    lastRun: null
  },
  {
    id: "SCENARIO-005",
    name: "支付系统压测场景",
    project: "支付系统",
    description: "支付系统的全链路压测，包括支付、退款、查询等核心功能",
    status: "active",
    testcases: [
      { id: "TC-017", name: "发起支付", weight: 40 },
      { id: "TC-018", name: "支付回调", weight: 30 },
      { id: "TC-019", name: "退款申请", weight: 20 },
      { id: "TC-020", name: "交易查询", weight: 10 }
    ],
    createdAt: "2024-01-16 09:00:00",
    updatedAt: "2024-01-16 15:30:00",
    totalTestcases: 4,
    lastRun: "2024-01-16 11:10:00"
  },
  {
    id: "SCENARIO-006",
    name: "搜索性能场景",
    project: "搜索引擎",
    description: "商品搜索、筛选、排序等功能的性能测试",
    status: "inactive",
    testcases: [
      { id: "TC-021", name: "关键词搜索", weight: 50 },
      { id: "TC-022", name: "高级筛选", weight: 30 },
      { id: "TC-023", name: "搜索结果排序", weight: 20 }
    ],
    createdAt: "2024-01-15 13:20:00",
    updatedAt: "2024-01-16 10:15:00",
    totalTestcases: 3,
    lastRun: "2024-01-15 14:30:00"
  },
  {
    id: "SCENARIO-007",
    name: "图片上传处理场景",
    project: "内容管理",
    description: "图片上传、压缩、裁剪、水印等处理流程测试",
    status: "active",
    testcases: [
      { id: "TC-024", name: "图片上传", weight: 40 },
      { id: "TC-025", name: "图片压缩", weight: 30 },
      { id: "TC-026", name: "添加水印", weight: 20 },
      { id: "TC-027", name: "生成缩略图", weight: 10 }
    ],
    createdAt: "2024-01-14 10:30:00",
    updatedAt: "2024-01-15 11:45:00",
    totalTestcases: 4,
    lastRun: "2024-01-14 14:00:00"
  },
  {
    id: "SCENARIO-008",
    name: "消息队列消费场景",
    project: "消息中间件",
    description: "消息的生产、消费、重试、死信队列等场景测试",
    status: "draft",
    testcases: [
      { id: "TC-028", name: "消息生产", weight: 40 },
      { id: "TC-029", name: "消息消费", weight: 40 },
      { id: "TC-030", name: "消息重试", weight: 20 }
    ],
    createdAt: "2024-01-13 16:00:00",
    updatedAt: "2024-01-14 09:30:00",
    totalTestcases: 3,
    lastRun: null
  }
]

// 响应式数据
const state = reactive({
  scenarios: [...mockScenarios],
  filteredScenarios: [...mockScenarios],
  currentPage: 1,
  pageSize: 8,
  viewMode: 'table', // 'card' 或 'table'
  searchFilters: {
    name: '',
    project: '',
    status: '',
    time: ''
  },
  modalVisible: false,
  modalTitle: '创建新场景',
  modalLoading: false,
  isEditing: false,
  currentEditId: null,
  weightTotal: 0,
  formData: {
    name: '',
    project: '',
    status: 'active',
    description: '',
    testcases: [{ id: '', weight: 20 }] as Array<{id: string, weight: number}>
  }
})

// 计算属性
const statistics = computed(() => {
  const total = state.scenarios.length
  const active = state.scenarios.filter(s => s.status === 'active').length

  let totalTestcases = 0
  let totalRuns = 0

  state.scenarios.forEach(s => {
    totalTestcases += s.totalTestcases
    if (s.lastRun) totalRuns++
  })

  return { total, active, totalTestcases, totalRuns }
})

const paginatedScenarios = computed(() => {
  const start = (state.currentPage - 1) * state.pageSize
  const end = start + state.pageSize
  return state.filteredScenarios.slice(start, end)
})

const projectOptions = computed(() => {
  const projects = Array.from(new Set(state.scenarios.map(s => s.project)))
  return projects.sort()
})

const testCaseOptions = computed(() => {
  return mockTestCases
})

// 状态映射
const statusMap: Record<string, { text: string, color: string }> = {
  active: { text: '启用中', color: 'green' },
  draft: { text: '草稿', color: 'orange' },
  inactive: { text: '已停用', color: 'gray' }
}

// 表格列定义
const columns = [
  {
    title: '场景ID',
    dataIndex: 'id',
    key: 'id',
    width: 100
  },
  {
    title: '场景名称',
    dataIndex: 'name',
    key: 'name',
    width: 180
  },
  {
    title: '所属项目',
    dataIndex: 'project',
    key: 'project',
    width: 120
  },
  {
    title: '测试用例',
    key: 'testcases',
    width: 200
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    width: 200,
    ellipsis: true
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 140,
    customRender: ({ text }: { text: string }) => text.split(' ')[0]
  },
  {
    title: '最后修改',
    dataIndex: 'updatedAt',
    key: 'updatedAt',
    width: 140,
    customRender: ({ text }: { text: string }) => text.split(' ')[0]
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    fixed: 'right'
  }
]

// 方法
const applyFilters = () => {
  const { name, project, status, time } = state.searchFilters

  state.filteredScenarios = state.scenarios.filter(scenario => {
    // 名称筛选
    if (name &&
        !scenario.name.toLowerCase().includes(name.toLowerCase()) &&
        !scenario.description.toLowerCase().includes(name.toLowerCase())) {
      return false
    }

    // 项目筛选
    if (project && scenario.project !== project) {
      return false
    }

    // 状态筛选
    if (status && scenario.status !== status) {
      return false
    }

    // 时间筛选
    if (time) {
      const scenarioDate = new Date(scenario.createdAt.split(' ')[0])
      const now = new Date()

      if (time === 'today') {
        const today = now.toISOString().split('T')[0]
        const scenarioDateStr = scenarioDate.toISOString().split('T')[0]
        if (scenarioDateStr !== today) return false
      } else if (time === 'week') {
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        if (scenarioDate < weekAgo) return false
      } else if (time === 'month') {
        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        if (scenarioDate < monthAgo) return false
      }
    }

    return true
  })

  state.currentPage = 1
}

const resetFilters = () => {
  state.searchFilters = {
    name: '',
    project: '',
    status: '',
    time: ''
  }
  state.filteredScenarios = [...state.scenarios]
  state.currentPage = 1
}

const switchView = (mode: string) => {
  state.viewMode = mode
}

const showAddModal = () => {
  state.modalTitle = '创建新场景'
  state.isEditing = false
  state.currentEditId = null
  state.formData = {
    name: '',
    project: '',
    status: 'active',
    description: '',
    testcases: [{ id: '', weight: 20 }]
  }
  state.modalVisible = true
  updateWeightTotal()
}

const showEditModal = (scenarioId: string) => {
  const scenario = state.scenarios.find(s => s.id === scenarioId)
  if (!scenario) return

  state.modalTitle = '编辑场景'
  state.isEditing = true
  state.currentEditId = scenarioId
  state.formData = {
    name: scenario.name,
    project: scenario.project,
    status: scenario.status,
    description: scenario.description,
    testcases: scenario.testcases.map(tc => ({
      id: tc.id,
      weight: tc.weight
    }))
  }
  state.modalVisible = true
  updateWeightTotal()
}

const handleModalOk = () => {
  const { name, project, status, description, testcases } = state.formData

  // 验证
  if (!name.trim()) {
    message.error('请输入场景名称')
    return
  }

  if (!project) {
    message.error('请选择所属项目')
    return
  }

  // 验证测试用例
  const validTestcases = testcases.filter(tc => tc.id && tc.weight)
  if (validTestcases.length === 0) {
    message.error('请至少配置一个测试用例')
    return
  }

  // 计算权重总和
  const totalWeight = validTestcases.reduce((sum, tc) => sum + tc.weight, 0)
  if (totalWeight !== 100) {
    message.error(`测试用例权重总和应为100%，当前为${totalWeight}%`)
    return
  }

  state.modalLoading = true

  setTimeout(() => {
    const now = new Date().toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })

    if (state.isEditing && state.currentEditId) {
      // 编辑场景
      const index = state.scenarios.findIndex(s => s.id === state.currentEditId)
      if (index !== -1) {
        const testcaseDetails = validTestcases.map(tc => {
          const testcase = mockTestCases.find(mtc => mtc.id === tc.id)
          return {
            id: tc.id,
            name: testcase ? testcase.name : '未知用例',
            weight: tc.weight
          }
        })

        state.scenarios[index] = {
          ...state.scenarios[index],
          name,
          project,
          status,
          description,
          testcases: testcaseDetails,
          totalTestcases: testcaseDetails.length,
          updatedAt: now
        }

        message.success(`场景 ${name} 已更新`)
      }
    } else {
      // 新增场景
      const newId = `SCENARIO-${String(state.scenarios.length + 1).padStart(3, '0')}`

      const testcaseDetails = validTestcases.map(tc => {
        const testcase = mockTestCases.find(mtc => mtc.id === tc.id)
        return {
          id: tc.id,
          name: testcase ? testcase.name : '未知用例',
          weight: tc.weight
        }
      })

      const newScenario = {
        id: newId,
        name,
        project,
        description,
        status,
        testcases: testcaseDetails,
        createdAt: now,
        updatedAt: now,
        totalTestcases: testcaseDetails.length,
        lastRun: null
      }

      state.scenarios.unshift(newScenario)
      message.success(`场景 ${name} 已创建`)
    }

    state.modalVisible = false
    state.modalLoading = false
    resetFilters() // 重置筛选以显示新数据
  }, 500)
}

const addTestCaseRow = () => {
  state.formData.testcases.push({ id: '', weight: 20 })
  updateWeightTotal()
}

const removeTestCaseRow = (index: number) => {
  if (state.formData.testcases.length > 1) {
    state.formData.testcases.splice(index, 1)
    updateWeightTotal()
  }
}

const updateWeightTotal = () => {
  state.weightTotal = state.formData.testcases.reduce((sum, tc) => sum + (tc.weight || 0), 0)
}

const runScenario = (scenarioId: string) => {
  const scenario = state.scenarios.find(s => s.id === scenarioId)
  if (scenario) {
    message.info(`运行场景: ${scenario.name} - 在实际系统中会跳转到任务创建页面`)
  }
}

const copyScenario = (scenarioId: string) => {
  const scenario = state.scenarios.find(s => s.id === scenarioId)
  if (scenario) {
    Modal.confirm({
      title: '确认复制',
      content: `确定要复制场景 "${scenario.name}" 吗？`,
      onOk() {
        const newId = `SCENARIO-${String(state.scenarios.length + 1).padStart(3, '0')}`
        const now = new Date().toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        })

        const copiedScenario = {
          ...scenario,
          id: newId,
          name: `${scenario.name} (副本)`,
          createdAt: now,
          updatedAt: now,
          lastRun: null
        }

        state.scenarios.unshift(copiedScenario)
        resetFilters()
        message.success(`场景 "${scenario.name}" 已复制为 "${copiedScenario.name}"`)
      }
    })
  }
}

const deleteScenario = (scenarioId: string) => {
  const scenario = state.scenarios.find(s => s.id === scenarioId)
  if (scenario) {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除场景 "${scenario.name}" 吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      onOk() {
        const index = state.scenarios.findIndex(s => s.id === scenarioId)
        if (index !== -1) {
          state.scenarios.splice(index, 1)
          resetFilters()
          message.success(`场景 "${scenario.name}" 已删除`)
        }
      }
    })
  }
}

onMounted(() => {
  // 初始化数据
  resetFilters()
  updateWeightTotal()
})
</script>

<style scoped>
.app-container {
  padding: 10px;
  //min-height: 100vh;
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

.stats-row {
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.scenario-card {
  padding: 20px 0;
  margin-bottom: 20px;
  height: 100%;
}

.scenario-card-header {
  margin-bottom: 12px;
}

.scenario-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: rgba(0, 0, 0, 0.85);
}

.scenario-id {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-bottom: 8px;
}

.scenario-description {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
  line-height: 1.5;
  margin-bottom: 12px;
}

.scenario-meta {
  background-color: #fafafa;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.meta-item:last-child {
  margin-bottom: 0;
}

.meta-label {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.meta-value {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.85);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.testcases-preview {
  margin-bottom: 16px;
}

.testcases-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.testcases-count {
  font-size: 12px;
}

.testcases-list {
  margin-top: 8px;
}

.testcase-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}

.testcase-item:last-child {
  border-bottom: none;
}

.testcase-name {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.85);
}

.testcase-weight {
  font-size: 12px;
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

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.testcase-config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.testcase-config-row {
  margin-bottom: 12px;
}

.weight-total {
  margin-top: 8px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.65);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .stats-row .ant-col {
    margin-bottom: 16px;
  }

  .scenario-card {
    margin-bottom: 16px;
  }
}
</style>