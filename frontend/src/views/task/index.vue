<template>
  <div class="task-management-container">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <div class="page-title-section">
        <h1 class="page-title">任务管理</h1>
        <p class="page-subtitle">压测任务创建、启停控制、状态查看、日志溯源，承接场景配置执行压测</p>
      </div>

      <Space>
        <!-- 视图切换 -->
        <Button.Group>
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

        <!-- 新增任务按钮 -->
        <Button type="primary" @click="showAddModal">
          <template #icon><PlusOutlined /></template>
          新增任务
        </Button>
      </Space>
    </div>

    <!-- 统计卡片 -->
    <Row :gutter="16" class="stats-row" v-show="false">
      <Col :span="6">
        <ACard>
          <Statistic
              title="任务总数"
              :value="statistics.total"
              :value-style="{ color: '#1890ff', fontSize: '24px' }"
          >
            <template #prefix><ScheduleOutlined /></template>
            <template #suffix>
              <span style="font-size: 12px; color: #666">今日 +5</span>
            </template>
          </Statistic>
        </ACard>
      </Col>
      <Col :span="6">
        <ACard>
          <Statistic
              title="运行中"
              :value="statistics.running"
              :value-style="{ color: '#52c41a', fontSize: '24px' }"
          >
            <template #prefix><PlayCircleOutlined /></template>
            <template #suffix>
              <span style="font-size: 12px; color: #666">实时监控</span>
            </template>
          </Statistic>
        </ACard>
      </Col>
      <Col :span="6">
        <ACard>
          <Statistic
              title="成功率"
              :value="statistics.successRate"
              :value-style="{ color: '#13c2c2', fontSize: '24px' }"
              suffix="%"
          >
            <template #prefix><CheckCircleOutlined /></template>
            <template #suffix>
              <span style="font-size: 12px; color: #666">整体指标</span>
            </template>
          </Statistic>
        </ACard>
      </Col>
      <Col :span="6">
        <ACard>
          <Statistic
              title="总耗时"
              :value="statistics.totalDuration"
              :value-style="{ color: '#faad14', fontSize: '24px' }"
              suffix="小时"
          >
            <template #prefix><ClockCircleOutlined /></template>
            <template #suffix>
              <span style="font-size: 12px; color: #666">累计压测</span>
            </template>
          </Statistic>
        </ACard>
      </Col>
    </Row>

    <!-- 筛选区域 -->
    <ACard title="任务筛选" class="filter-card">
      <template #extra><FilterOutlined /></template>

      <Row :gutter="16">
        <Col :span="6">
          <Input
              v-model:value="state.searchFilters.name"
              placeholder="输入任务名称关键字"
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
            <Select.Option value="running">运行中</Select.Option>
            <Select.Option value="completed">已完成</Select.Option>
            <Select.Option value="stopped">已停止</Select.Option>
            <Select.Option value="failed">失败</Select.Option>
            <Select.Option value="scheduled">已计划</Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.project"
              placeholder="所属项目"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部项目</Select.Option>
            <Select.Option v-for="project in projectOptions" :key="project.value" :value="project.value">
              {{ project.label }}
            </Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.scenario"
              placeholder="所属场景"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部场景</Select.Option>
            <Select.Option v-for="scenario in scenarioOptions" :key="scenario.value" :value="scenario.value">
              {{ scenario.label }}
            </Select.Option>
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
            查询任务
          </Button>
        </Col>
      </Row>
    </ACard>

    <!-- 任务展示区域 -->
    <div v-if="state.viewMode === 'card'">
      <!-- 卡片视图 -->
      <Row :gutter="[16, 16]" v-if="paginatedTasks.length > 0">
        <Col :span="8" v-for="task in paginatedTasks" :key="task.id">
          <ACard class="task-card" hoverable>
            <template #title>
              <div class="task-card-header">
                <h3 class="task-name">{{ task.name }}</h3>
                <div class="task-id">{{ task.id }}</div>
              </div>
            </template>

            <template #extra>
              <Tag :color="statusMap[task.status].color">
                {{ statusMap[task.status].text }}
              </Tag>
            </template>

            <div class="task-description">执行场景: {{ task.scenario }}</div>

            <div class="task-tags">
              <Tag color="blue" size="small">{{ task.project }}</Tag>
              <Tag color="cyan" size="small">用户数: {{ task.params.users }}</Tag>
              <Tag color="orange" size="small">时长: {{ task.params.duration || '无限' }}分钟</Tag>
            </div>

            <div class="task-meta">
              <div class="meta-item">
                <span class="meta-label">负责人</span>
                <div class="meta-value">
                  <Avatar size="small" style="backgroundColor: #1890ff">
                    {{ task.owner.charAt(0) }}
                  </Avatar>
                  {{ task.owner }}
                </div>
              </div>

              <div class="meta-item">
                <span class="meta-label">创建时间</span>
                <div class="meta-value">{{ task.createdAt }}</div>
              </div>

              <div class="meta-item">
                <span class="meta-label">开始时间</span>
                <div class="meta-value">{{ task.startedAt || '—' }}</div>
              </div>

              <div class="meta-item">
                <span class="meta-label">结束时间</span>
                <div class="meta-value">{{ task.endedAt || '—' }}</div>
              </div>
            </div>

            <div class="task-performance">
              <div class="performance-item">
                <div class="performance-value" style="color: #52c41a;">
                  {{ task.params.users }}
                </div>
                <div class="performance-label">虚拟用户</div>
              </div>
              <div class="performance-item">
                <div class="performance-value">{{ task.params.spawnRate }}个/秒</div>
                <div class="performance-label">生成速率</div>
              </div>
              <div class="performance-item">
                <div class="performance-value" style="color: #1890ff;">
                  {{ task.params.duration || '∞' }}
                </div>
                <div class="performance-label">压测时长</div>
              </div>
            </div>

            <template #actions>
              <Tooltip v-if="task.status === 'running'" title="停止">
                <Button type="link" danger @click="stopTask(task.id)">
                  <template #icon><StopOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip v-if="task.status !== 'running'" title="执行">
                <Button type="link" @click="startTask(task.id)">
                  <template #icon><PlayCircleOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="监控">
                <Button type="link" @click="viewMonitor(task.id)">
                  <template #icon><LineChartOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="日志">
                <Button type="link" @click="viewLogs(task.id)">
                  <template #icon><FileTextOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="编辑">
                <Button type="link" @click="showEditModal(task.id)">
                  <template #icon><EditOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="删除">
                <Button type="link" danger @click="deleteTask(task.id)">
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Tooltip>
            </template>
          </ACard>
        </Col>
      </Row>

      <!-- 卡片视图空状态 -->
      <div v-if="paginatedTasks.length === 0" class="empty-state">
        <div class="empty-icon">
          <ScheduleOutlined />
        </div>
        <h3>暂无任务数据</h3>
        <p>当前没有找到符合筛选条件的任务，请尝试调整筛选条件或创建新的压测任务。</p>
        <Button type="primary" @click="showAddModal">
          <template #icon><PlusOutlined /></template>
          新增任务
        </Button>
      </div>
    </div>

    <!-- 表格视图 -->
    <div v-else>
      <ACard>
        <Table
            :columns="columns"
            :data-source="paginatedTasks"
            :pagination="false"
            row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <!-- 状态标签 -->
            <template v-if="column.key === 'status'">
              <Tag :color="statusMap[record.status].color">
                {{ statusMap[record.status].text }}
              </Tag>
            </template>

            <!-- 负责人 -->
            <template v-if="column.key === 'owner'">
              <Space>
                <Avatar size="small" style="backgroundColor: #1890ff">
                  {{ record.owner.charAt(0) }}
                </Avatar>
                <span>{{ record.owner }}</span>
              </Space>
            </template>

            <!-- 操作按钮 -->
            <template v-if="column.key === 'actions'">
              <Space size="small">
                <Tooltip v-if="record.status === 'running'" title="停止">
                  <Button size="small" type="link" danger @click="stopTask(record.id)">
                    <StopOutlined />
                  </Button>
                </Tooltip>
                <Tooltip v-if="record.status !== 'running'" title="执行">
                  <Button size="small" type="link" @click="startTask(record.id)">
                    <PlayCircleOutlined />
                  </Button>
                </Tooltip>
                <Tooltip title="监控">
                  <Button size="small" type="link" @click="viewMonitor(record.id)">
                    <LineChartOutlined />
                  </Button>
                </Tooltip>
                <Tooltip title="日志">
                  <Button size="small" type="link" @click="viewLogs(record.id)">
                    <FileTextOutlined />
                  </Button>
                </Tooltip>
                <Tooltip title="编辑">
                  <Button size="small" type="link" @click="showEditModal(record.id)">
                    <EditOutlined />
                  </Button>
                </Tooltip>
                <Tooltip title="删除">
                  <Button size="small" type="link" danger @click="deleteTask(record.id)">
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
              <p>当前没有找到符合筛选条件的任务，请尝试调整筛选条件或创建新的压测任务。</p>
              <Button type="primary" @click="showAddModal">
                <template #icon><PlusOutlined /></template>
                新增任务
              </Button>
            </div>
          </template>
        </Table>
      </ACard>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="state.filteredTasks.length > 0">
      <Pagination
          v-model:current="state.currentPage"
          v-model:pageSize="state.pageSize"
          :total="state.filteredTasks.length"
          show-quick-jumper
          show-size-changer
          :show-total="(total: number) => `共 ${total} 条`"
      />
    </div>

    <!-- 新增/编辑任务模态框 -->
    <Modal
        v-model:visible="state.modalVisible"
        :title="state.modalTitle"
        width="600px"
        @ok="handleModalOk"
        @cancel="state.modalVisible = false"
    >
      <Form layout="vertical">
        <Form.Item label="任务名称" required>
          <Input
              v-model:value="state.formData.name"
              placeholder="例如：双十一大促压测"
          />
        </Form.Item>

        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="所属项目" required>
              <Select v-model:value="state.formData.project">
                <Select.Option v-for="project in projectOptions" :key="project.value" :value="project.value">
                  {{ project.label }}
                </Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="所属场景" required>
              <Select v-model:value="state.formData.scenario">
                <Select.Option v-for="scenario in scenarioOptions" :key="scenario.value" :value="scenario.value">
                  {{ scenario.label }}
                </Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="负责人">
              <Select v-model:value="state.formData.owner">
                <Select.Option value="张三">张三</Select.Option>
                <Select.Option value="李四">李四</Select.Option>
                <Select.Option value="王五">王五</Select.Option>
                <Select.Option value="赵六">赵六</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="任务状态">
              <Select v-model:value="state.formData.status">
                <Select.Option value="scheduled">已计划</Select.Option>
                <Select.Option value="running">运行中</Select.Option>
                <Select.Option value="stopped">已停止</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Divider>压测参数</Divider>

        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="虚拟用户数" required>
              <InputNumber
                  v-model:value="state.formData.users"
                  :min="1"
                  :max="10000"
                  placeholder="例如：100"
                  style="width: 100%"
              />
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="生成速率 (个/秒)" required>
              <InputNumber
                  v-model:value="state.formData.spawnRate"
                  :min="1"
                  :max="1000"
                  placeholder="例如：10"
                  style="width: 100%"
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="压测时长 (分钟)">
          <InputNumber
              v-model:value="state.formData.duration"
              :min="1"
              :max="1440"
              placeholder="留空表示无限时长"
              style="width: 100%"
          />
          <div class="form-help">1-1440分钟，留空表示无限时长</div>
        </Form.Item>

        <Divider>高级设置</Divider>

        <Form.Item label="任务描述">
          <Input.TextArea
              v-model:value="state.formData.description"
              placeholder="描述任务的压测目标、注意事项..."
              :rows="3"
          />
        </Form.Item>

        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="性能目标 - TPS">
              <InputNumber
                  v-model:value="state.formData.targetTps"
                  :min="1"
                  placeholder="例如：1000"
                  style="width: 100%"
              />
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="性能目标 - 响应时间(ms)">
              <InputNumber
                  v-model:value="state.formData.targetRt"
                  :min="1"
                  placeholder="例如：200"
                  style="width: 100%"
              />
            </Form.Item>
          </Col>
        </Row>
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
  InputNumber,
  Select,
  Table,
  Tag,
  Avatar,
  Statistic,
  Modal,
  Form,
  Pagination,
  Space,
  Divider,
  Tooltip
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
  ScheduleOutlined,
  PlayCircleOutlined,
  StopOutlined,
  LineChartOutlined,
  FileTextOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons-vue'
import router from "@/router";

// 模拟数据
const mockTasks = [
  {
    id: "TASK-20240120-001",
    name: "Baidu首页压测",
    project: "搜索引擎",
    scenario: "首页访问场景",
    owner: "张三",
    status: "completed",
    params: {
      users: 100,
      spawnRate: 10,
      duration: 30
    },
    description: "搜索引擎首页的高并发访问测试",
    stats: {
      successRate: 99.8,
      avgResponseTime: 45,
      totalRequests: 15000
    },
    targets: {
      tps: 500,
      responseTime: 100
    },
    createdAt: "2024-01-20 10:30:00",
    startedAt: "2024-01-20 10:30:00",
    endedAt: "2024-01-20 11:00:00",
    updatedAt: "2024-01-20 11:05:00"
  },
  {
    id: "TASK-20240120-002",
    name: "双十一大促压测",
    project: "电商平台",
    scenario: "下单流程场景",
    owner: "李四",
    status: "running",
    params: {
      users: 500,
      spawnRate: 50,
      duration: 60
    },
    description: "双十一活动期间的订单处理能力测试",
    stats: {
      successRate: 98.5,
      avgResponseTime: 156,
      totalRequests: 45000
    },
    targets: {
      tps: 1000,
      responseTime: 200
    },
    createdAt: "2024-01-20 14:00:00",
    startedAt: "2024-01-20 14:00:00",
    endedAt: null,
    updatedAt: "2024-01-20 14:30:00"
  },
  {
    id: "TASK-20240120-003",
    name: "用户登录性能测试",
    project: "用户中心",
    scenario: "登录注册场景",
    owner: "王五",
    status: "stopped",
    params: {
      users: 200,
      spawnRate: 20,
      duration: null
    },
    description: "用户登录接口的性能和稳定性测试",
    stats: {
      successRate: 99.2,
      avgResponseTime: 124,
      totalRequests: 12000
    },
    targets: {
      tps: 2000,
      responseTime: 100
    },
    createdAt: "2024-01-19 09:15:00",
    startedAt: "2024-01-19 09:15:00",
    endedAt: "2024-01-19 09:45:00",
    updatedAt: "2024-01-19 09:50:00"
  },
  {
    id: "TASK-20240119-001",
    name: "API网关极限测试",
    project: "API网关",
    scenario: "高并发场景",
    owner: "赵六",
    status: "failed",
    params: {
      users: 1000,
      spawnRate: 100,
      duration: 45
    },
    description: "API网关的极限并发处理能力测试",
    stats: {
      successRate: 85.5,
      avgResponseTime: 320,
      totalRequests: 18000
    },
    targets: {
      tps: 5000,
      responseTime: 50
    },
    createdAt: "2024-01-19 16:30:00",
    startedAt: "2024-01-19 16:30:00",
    endedAt: "2024-01-19 17:15:00",
    updatedAt: "2024-01-19 17:20:00"
  },
  {
    id: "TASK-20240118-001",
    name: "商品搜索性能测试",
    project: "电商平台",
    scenario: "搜索性能场景",
    owner: "张三",
    status: "completed",
    params: {
      users: 300,
      spawnRate: 30,
      duration: 20
    },
    description: "商品搜索接口的性能优化验证",
    stats: {
      successRate: 99.5,
      avgResponseTime: 95,
      totalRequests: 18000
    },
    targets: {
      tps: 1500,
      responseTime: 150
    },
    createdAt: "2024-01-18 13:20:00",
    startedAt: "2024-01-18 13:20:00",
    endedAt: "2024-01-18 13:40:00",
    updatedAt: "2024-01-18 13:45:00"
  },
  {
    id: "TASK-20240118-002",
    name: "支付接口压测",
    project: "支付系统",
    scenario: "支付压测场景",
    owner: "李四",
    status: "completed",
    params: {
      users: 150,
      spawnRate: 15,
      duration: 40
    },
    description: "支付核心流程的稳定性和安全性测试",
    stats: {
      successRate: 97.9,
      avgResponseTime: 210,
      totalRequests: 9000
    },
    targets: {
      tps: 800,
      responseTime: 300
    },
    createdAt: "2024-01-18 11:10:00",
    startedAt: "2024-01-18 11:10:00",
    endedAt: "2024-01-18 11:50:00",
    updatedAt: "2024-01-18 11:55:00"
  },
  {
    id: "TASK-20240117-001",
    name: "推荐系统负载测试",
    project: "推荐引擎",
    scenario: "推荐算法场景",
    owner: "王五",
    status: "running",
    params: {
      users: 400,
      spawnRate: 40,
      duration: null
    },
    description: "推荐算法的实时计算能力测试",
    stats: {
      successRate: 99.3,
      avgResponseTime: 132,
      totalRequests: 32000
    },
    targets: {
      tps: 3000,
      responseTime: 120
    },
    createdAt: "2024-01-17 15:45:00",
    startedAt: "2024-01-17 15:45:00",
    endedAt: null,
    updatedAt: "2024-01-17 16:15:00"
  },
  {
    id: "TASK-20240117-002",
    name: "图片上传性能测试",
    project: "内容管理",
    scenario: "文件上传场景",
    owner: "赵六",
    status: "stopped",
    params: {
      users: 80,
      spawnRate: 8,
      duration: 25
    },
    description: "大文件上传的带宽和稳定性测试",
    stats: {
      successRate: 98.8,
      avgResponseTime: 180,
      totalRequests: 2000
    },
    targets: {
      tps: 500,
      responseTime: 250
    },
    createdAt: "2024-01-17 10:30:00",
    startedAt: "2024-01-17 10:30:00",
    endedAt: "2024-01-17 10:55:00",
    updatedAt: "2024-01-17 11:00:00"
  }
]

// 响应式数据
const state = reactive({
  tasks: [...mockTasks],
  filteredTasks: [...mockTasks],
  currentPage: 1,
  pageSize: 8,
  viewMode: 'card', // 'card' 或 'table'
  searchFilters: {
    name: '',
    status: '',
    project: '',
    scenario: ''
  },
  modalVisible: false,
  modalTitle: '创建新任务',
  isEditing: false,
  currentEditId: null as string | null,
  formData: {
    name: '',
    project: '',
    scenario: '',
    owner: '张三',
    status: 'scheduled',
    users: null as number | null,
    spawnRate: null as number | null,
    duration: null as number | null,
    description: '',
    targetTps: null as number | null,
    targetRt: null as number | null
  }
})

// 选项数据
const projectOptions = [
  { value: '电商平台', label: '电商平台' },
  { value: 'API网关', label: 'API网关' },
  { value: '用户中心', label: '用户中心' },
  { value: '支付系统', label: '支付系统' },
  { value: '搜索引擎', label: '搜索引擎' },
  { value: '推荐引擎', label: '推荐引擎' },
  { value: '内容管理', label: '内容管理' }
]

const scenarioOptions = [
  { value: '首页访问场景', label: '首页访问场景' },
  { value: '下单流程场景', label: '下单流程场景' },
  { value: '登录注册场景', label: '登录注册场景' },
  { value: '高并发场景', label: '高并发场景' },
  { value: '搜索性能场景', label: '搜索性能场景' },
  { value: '支付压测场景', label: '支付压测场景' },
  { value: '推荐算法场景', label: '推荐算法场景' },
  { value: '文件上传场景', label: '文件上传场景' }
]

// 状态映射
const statusMap: Record<string, { text: string, color: string }> = {
  running: { text: '运行中', color: 'green' },
  completed: { text: '已完成', color: 'blue' },
  stopped: { text: '已停止', color: 'orange' },
  failed: { text: '失败', color: 'red' },
  scheduled: { text: '已计划', color: 'purple' }
}

// 计算属性
const statistics = computed(() => {
  const total = state.tasks.length
  const running = state.tasks.filter(t => t.status === 'running').length
  let successRate = 0
  let totalDuration = 0

  state.tasks.forEach(t => {
    if (t.stats?.successRate) {
      successRate += t.stats.successRate
    }
    if (t.params?.duration) {
      totalDuration += t.params.duration
    }
  })

  return {
    total,
    running,
    successRate: total > 0 ? (successRate / total).toFixed(1) : '0.0',
    totalDuration: (totalDuration / 60).toFixed(1) // 转换为小时
  }
})

const paginatedTasks = computed(() => {
  const start = (state.currentPage - 1) * state.pageSize
  const end = start + state.pageSize
  return state.filteredTasks.slice(start, end)
})

// 表格列定义
const columns = [
  {
    title: '任务ID',
    dataIndex: 'id',
    key: 'id',
    width: 120
  },
  {
    title: '任务名称',
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
    title: '所属场景',
    dataIndex: 'scenario',
    key: 'scenario',
    width: 140
  },
  {
    title: '负责人',
    dataIndex: 'owner',
    key: 'owner',
    width: 100
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
    width: 140
  },
  {
    title: '操作',
    key: 'actions',
    width: 180
  }
]

// 方法
const applyFilters = () => {
  const { name, status, project, scenario } = state.searchFilters

  state.filteredTasks = state.tasks.filter(task => {
    // 名称筛选
    if (name && !task.name.toLowerCase().includes(name.toLowerCase()) &&
        !(task.description && task.description.toLowerCase().includes(name.toLowerCase()))) {
      return false
    }

    // 状态筛选
    if (status && task.status !== status) {
      return false
    }

    // 项目筛选
    if (project && task.project !== project) {
      return false
    }

    // 场景筛选
    if (scenario && task.scenario !== scenario) {
      return false
    }

    return true
  })

  state.currentPage = 1
}

const resetFilters = () => {
  state.searchFilters = {
    name: '',
    status: '',
    project: '',
    scenario: ''
  }
  state.filteredTasks = [...state.tasks]
  state.currentPage = 1
}

const switchView = (mode: string) => {
  state.viewMode = mode
}

const showAddModal = () => {
  state.modalTitle = '创建新任务'
  state.isEditing = false
  state.currentEditId = null
  state.formData = {
    name: '',
    project: '',
    scenario: '',
    owner: '张三',
    status: 'scheduled',
    users: null,
    spawnRate: null,
    duration: null,
    description: '',
    targetTps: null,
    targetRt: null
  }
  state.modalVisible = true
}

const showEditModal = (taskId: string) => {
  const task = state.tasks.find(t => t.id === taskId)
  if (!task) return

  state.modalTitle = '编辑任务'
  state.isEditing = true
  state.currentEditId = taskId
  state.formData = {
    name: task.name,
    project: task.project,
    scenario: task.scenario,
    owner: task.owner,
    status: task.status,
    users: task.params.users,
    spawnRate: task.params.spawnRate,
    duration: task.params.duration,
    description: task.description || '',
    targetTps: task.targets?.tps || null,
    targetRt: task.targets?.responseTime || null
  }
  state.modalVisible = true
}

const handleModalOk = () => {
  const { name, project, scenario, owner, status, users, spawnRate, duration, description, targetTps, targetRt } = state.formData

  // 验证
  if (!name.trim()) {
    Modal.error({ title: '错误', content: '请输入任务名称' })
    return
  }

  if (!project) {
    Modal.error({ title: '错误', content: '请选择所属项目' })
    return
  }

  if (!scenario) {
    Modal.error({ title: '错误', content: '请选择所属场景' })
    return
  }

  if (!users || users <= 0) {
    Modal.error({ title: '错误', content: '请输入有效的虚拟用户数' })
    return
  }

  if (!spawnRate || spawnRate <= 0) {
    Modal.error({ title: '错误', content: '请输入有效的生成速率' })
    return
  }

  if (state.isEditing && state.currentEditId) {
    // 编辑任务
    const index = state.tasks.findIndex(t => t.id === state.currentEditId)
    if (index !== -1) {
      state.tasks[index] = {
        ...state.tasks[index],
        name,
        project,
        scenario,
        owner,
        status,
        params: {
          ...state.tasks[index].params,
          users: users || 0,
          spawnRate: spawnRate || 0,
          duration: duration || null
        },
        description,
        targets: {
          tps: targetTps || 0,
          responseTime: targetRt || 0
        },
        updatedAt: new Date().toLocaleString('zh-CN')
      }
      Modal.success({ title: '成功', content: `任务 ${name} 已更新` })
    }
  } else {
    // 新增任务
    const newId = `TASK-${new Date().toISOString().slice(0,10).replace(/-/g, '')}-${String(state.tasks.length + 1).padStart(3, '0')}`
    const now = new Date().toLocaleString('zh-CN')

    // 生成模拟统计数据
    const successRate = 95 + Math.random() * 4
    const avgResponseTime = 50 + Math.random() * 200
    const totalRequests = (users || 0) * 60 * (duration || 1)

    const newTask = {
      id: newId,
      name,
      project,
      scenario,
      owner,
      status,
      params: {
        users: users || 0,
        spawnRate: spawnRate || 0,
        duration: duration || null
      },
      description,
      stats: {
        successRate: parseFloat(successRate.toFixed(1)),
        avgResponseTime: Math.round(avgResponseTime),
        totalRequests: Math.round(totalRequests)
      },
      targets: {
        tps: targetTps || 0,
        responseTime: targetRt || 0
      },
      createdAt: now,
      startedAt: status === 'running' ? now : null,
      endedAt: null,
      updatedAt: now
    }

    state.tasks.unshift(newTask)
    Modal.success({ title: '成功', content: `任务 ${name} 已创建` })
  }

  state.modalVisible = false
  resetFilters() // 重置筛选以显示新数据
}

const startTask = (taskId: string) => {
  const task = state.tasks.find(t => t.id === taskId)
  if (!task) return

  Modal.confirm({
    title: '确认执行',
    content: `确定要开始执行任务 "${task.name}" 吗？`,
    onOk() {
      task.status = 'running'
      task.startedAt = new Date().toLocaleString('zh-CN')
      task.endedAt = null
      task.updatedAt = new Date().toLocaleString('zh-CN')
      Modal.success({ title: '成功', content: `任务 "${task.name}" 已开始执行` })
    }
  })
}

const stopTask = (taskId: string) => {
  const task = state.tasks.find(t => t.id === taskId)
  if (!task) return

  Modal.confirm({
    title: '确认停止',
    content: `确定要停止任务 "${task.name}" 吗？`,
    onOk() {
      task.status = 'stopped'
      task.endedAt = new Date().toLocaleString('zh-CN')
      task.updatedAt = new Date().toLocaleString('zh-CN')
      Modal.success({ title: '成功', content: `任务 "${task.name}" 已停止` })
    }
  })
}

const viewMonitor = (taskId: string) => {
  const task = state.tasks.find(t => t.id === taskId)
  if (task) {
    Modal.info({
      title: `任务监控: ${task.name}`,
      content: `任务 ${task.name} 的监控页面将在新窗口打开`,
      onOk() {
        // 在实际项目中这里会跳转到监控页面
        console.log(`打开任务 ${taskId} 的监控页面`)
        router.push(`/monitor/1`)
      }
    })
  }
}

const viewLogs = (taskId: string) => {
  const task = state.tasks.find(t => t.id === taskId)
  if (task) {
    Modal.info({
      title: `任务日志: ${task.name}`,
      content: `任务 ${task.name} 的日志页面将在新窗口打开`,
      onOk() {
        // 在实际项目中这里会跳转到日志页面
        console.log(`打开任务 ${taskId} 的日志页面`)
      }
    })
  }
}

const deleteTask = (taskId: string) => {
  const task = state.tasks.find(t => t.id === taskId)
  if (!task) return

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除任务 "${task.name}" 吗？此操作不可恢复。`,
    onOk() {
      const index = state.tasks.findIndex(t => t.id === taskId)
      if (index !== -1) {
        state.tasks.splice(index, 1)
        resetFilters()
        Modal.success({ title: '成功', content: `任务 "${task.name}" 已删除` })
      }
    }
  })
}

onMounted(() => {
  // 初始化数据
  resetFilters()
})
</script>

<style scoped>
.task-management-container {
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

.task-card {
  padding: 20px 0;
  margin-bottom: 20px;
  height: 100%;
}

.task-card-header {
  margin-bottom: 12px;
}

.task-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: rgba(0, 0, 0, 0.85);
}

.task-id {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-bottom: 8px;
}

.task-description {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
  line-height: 1.5;
  margin-bottom: 12px;
}

.task-tags {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.task-meta {
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
  gap: 8px;
}

.task-performance {
  display: flex;
  justify-content: space-between;
  background-color: #fafafa;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.performance-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.performance-value {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}

.performance-label {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
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

.form-help {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 4px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .stats-row .ant-col {
    margin-bottom: 16px;
  }

  .task-card {
    margin-bottom: 16px;
  }
}
</style>