<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import dayjs from 'dayjs'
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
  Drawer,
  Form,
  Checkbox,
  Pagination,
  Space,
  Divider,
  Descriptions,
  DescriptionsItem,
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
  ProjectOutlined,
  FilterOutlined
} from '@ant-design/icons-vue'
import { ProjectApi } from "@/api/project.ts";
import {ProjectInfoList, QueryProjectList} from "@/types/project";
import type {ProjectInfo} from "../../types/project";

// 响应式数据
const state = reactive({
  // 项目数据
  projects: [] as ProjectInfoList[],
  filteredProjects: [] as ProjectInfoList[],

  // 分页相关
  currentPage: 1,
  pageSize: 8,
  total: 0,

  // 视图模式
  viewMode: 'table', // 'card' 或 'table'

  // 模态框相关
  modalVisible: false,
  modalTitle: '创建新项目',
  isEditing: false,
  currentEditId: null as string | null,

  // 表单数据
  formData: {
    name: '',
    key: '',
    status: 'active',
    owner: '张三',
    priority: 'medium',
    description: '',
    tags: [] as string[],
    targetTps: null as number | null,
    targetRt: null as number | null
  },

  // 筛选条件
  searchFilters: {
    name: '',
    status: '',
    tags: [],
    owner: {
      id: 0,
      name: ''
    },
    priority: '',
  }
})


const paginatedProjects = computed(() => {
  const start = (state.currentPage - 1) * state.pageSize
  const end = start + state.pageSize
  return state.filteredProjects.slice(start, end)
})

// 标签颜色映射
const tagColors: Record<string, string> = {
  ecommerce: 'blue',
  api: 'green',
  user: 'orange',
  payment: 'purple',
  // search: 'pink'
  search: 'yellow'
}

const tagNames: Record<string, string> = {
  ecommerce: '电商',
  api: 'API接口',
  user: '用户系统',
  payment: '支付系统',
  search: '搜索引擎'
}

const tagsOptions = ['ecommerce', 'api', 'user', 'payment', 'search' ]

// 状态映射
const statusMap: Record<string, { text: string, color: string }> = {
  ACTIVE: { text: '启用中', color: 'green' },
  INACTIVE: { text: '已停用', color: 'gray' },
  ARCHIVED: { text: '已归档', color: 'orange' }
}

// 优先级映射
const priorityMap: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低'
}

// 方法
const applyFilters = () => {
  const { name, status, tag, owner } = state.searchFilters

  state.filteredProjects = state.projects.filter(project => {
    // 名称筛选
    if (name && !project.name.toLowerCase().includes(name.toLowerCase())) {
      return false
    }

    // 状态筛选
    if (status && project.status !== status) {
      return false
    }

    // 标签筛选 - 假设接口返回的是字符串数组
    if (tag && !project.tags?.includes(tag)) {
      return false
    }

    // 负责人筛选
    if (owner && project.owner_name !== owner) {
      return false
    }

    return true
  })

  state.currentPage = 1
  state.totalProjects = state.filteredProjects.length
}

const resetFilters = () => {
  state.searchFilters = {
    name: '',
    status: '',
    tag: '',
    owner: '',
    priority: ''
  }
  state.filteredProjects = [...state.projects]
  state.currentPage = 1
  state.totalProjects = state.projects.length
}

const switchView = (mode: string) => {
  state.viewMode = mode
}

const showAddModal = () => {
  state.modalTitle = '创建新项目'
  state.isEditing = false
  state.currentEditId = null
  state.formData = {
    name: '',
    status: 'active',
    owner: {
      id: 0,
      name: ''
    },
    priority: 'medium',
    description: '',
    tags: [],
  }
  state.modalVisible = true
}

const showEditModal = (projectId: string) => {
  const project = state.projects.find(p => p.id === projectId)
  if (!project) return

  state.modalTitle = '编辑项目'
  state.isEditing = true
  state.currentEditId = projectId
  state.formData = {
    name: project.name,
    key: project.key || '',
    status: project.status || 'active',
    owner: project.owner_name || '张三',
    priority: project.priority || 'medium',
    description: project.description || '',
    tags: Array.isArray(project.tags) ? [...project.tags] : [],
    targetTps: project.target_tps || null,
    targetRt: project.target_rt || null
  }
  state.modalVisible = true
}

const handleModalOk = async () => {
  const { name, key, status, owner, priority, description, tags, targetTps, targetRt } = state.formData

  // 验证
  if (!name.trim()) {
    Modal.error({ title: '错误', content: '请输入项目名称' })
    return
  }

  if (!key.trim()) {
    Modal.error({ title: '错误', content: '请输入项目标识' })
    return
  }

  if (key.length < 3) {
    Modal.error({ title: '错误', content: '项目标识至少需要3个字符' })
    return
  }

  try {
    if (state.isEditing && state.currentEditId) {
      // 编辑项目 - 调用更新接口
      const updateData = {
        id: state.currentEditId,
        name,
        key,
        status,
        owner_name: owner,
        priority,
        description,
        tags: tags.join(','),
        target_tps: targetTps,
        target_rt: targetRt
      }

      // 调用更新接口
      await ProjectApi.updateProject(updateData)
      Modal.success({ title: '成功', content: `项目 ${name} 已更新` })
    } else {
      // 新增项目 - 调用创建接口
      const createData = {
        name,
        key,
        status,
        owner_name: owner,
        priority,
        description,
        tags: tags.join(','),
        target_tps: targetTps,
        target_rt: targetRt
      }

      await ProjectApi.createProject(createData)
      Modal.success({ title: '成功', content: `项目 ${name} 已创建` })
    }

    // 重新获取项目列表
    await handleGetProjectList({
      page: state.currentPage,
      page_size: state.pageSize,
      name: state.searchFilters.name,
      priority: state.searchFilters.priority,
      status: state.searchFilters.status,
      owner_name: state.searchFilters.owner,
    })

    state.modalVisible = false
  } catch (error) {
    console.error('保存项目失败:', error)
    Modal.error({ title: '错误', content: '保存项目失败，请稍后重试' })
  }
}

const deleteProject = async (projectId: string) => {
  const project = state.projects.find(p => p.id === projectId)
  if (!project) return

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除项目 "${project.name}" 吗？此操作不可恢复，且会同时删除项目下的所有场景和任务。`,
    async onOk() {
      try {
        await ProjectApi.deleteProject(projectId)

        // 从本地列表中移除
        const index = state.projects.findIndex(p => p.id === projectId)
        if (index !== -1) {
          state.projects.splice(index, 1)
          resetFilters()
          Modal.success({ title: '成功', content: `项目 "${project.name}" 已删除` })
        }
      } catch (error) {
        console.error('删除项目失败:', error)
        Modal.error({ title: '错误', content: '删除项目失败，请稍后重试' })
      }
    }
  })
}

const viewProject = (projectId: string) => {
  const project = state.projects.find(p => p.id === projectId)
  if (project) {
    Modal.info({
      title: `项目详情: ${project.name}`,
      width: 600,
      content: h('div', {}, [
        h(Descriptions, { column: 2, bordered: true }, {
          default: () => [
            h(DescriptionsItem, { label: '项目ID' }, () => project.id),
            h(DescriptionsItem, { label: '项目标识' }, () => project.key || '-'),
            h(DescriptionsItem, { label: '负责人' }, () => project.owner_name || '-'),
            h(DescriptionsItem, { label: '状态' }, () =>
                h(Tag, { color: statusMap[project.status]?.color || 'default' },
                    statusMap[project.status]?.text || project.status)
            ),
            h(DescriptionsItem, { label: '优先级' }, () => priorityMap[project.priority] || '-'),
            h(DescriptionsItem, { label: '标签' }, () =>
                (Array.isArray(project.tags) ? project.tags : []).map(tag =>
                    h(Tag, { color: tagColors[tag] || 'default', key: tag }, tagNames[tag] || tag)
                )
            ),
            h(DescriptionsItem, { label: '场景数' }, () => project.scenarios_count || 0),
            h(DescriptionsItem, { label: '任务数' }, () => project.tasks_count || 0),
            h(DescriptionsItem, { label: '成功率' }, () => `${project.success_rate || 0}%`),
            h(DescriptionsItem, { label: '平均响应时间' }, () => `${project.avg_response_time || 0}ms`),
            h(DescriptionsItem, { label: '创建时间' }, () => project.created_at || '-'),
            h(DescriptionsItem, { label: '最后更新' }, () => project.updated_at || '-'),
            h(DescriptionsItem, { label: '项目描述', span: 2 }, () => project.description || '-')
          ]
        })
      ])
    })
  }
}

// 获取项目列表
const handleGetProjectList = async (data?: QueryProjectList) => {
  try {
    const params = {
      page: data?.page || state.currentPage,
      page_size: data?.page_size || state.pageSize,
      name: data?.name || state.searchFilters.name,
      status: data?.status || state.searchFilters.status,
      tags: data?.tags || state.searchFilters.tags,
      priority: data?.priority || state.searchFilters.priority,
      owner_name: data?.name || state.searchFilters.owner.name,
      owner_id: data?.owner_id || state.searchFilters.owner.id,
    }

    const response = await ProjectApi.getProjectList(params);

    // 假设接口返回结构为 { data: { results: ProjectInfoList[], total: number } }
    state.projects = response.data.results as ProjectInfo[]
    state.filteredProjects = [...state.projects]
    state.total = response.data.total

  } catch(error) {
    console.error('获取项目列表失败:', error)
    Modal.error({
      title: '获取数据失败',
      content: '无法加载项目列表，请检查网络连接或稍后重试'
    })
  }
}

// 表格列定义
const columns = [
  {
    title: '项目ID',
    dataIndex: 'id',
    key: 'id',
    width: 100
  },
  {
    title: '项目名称',
    dataIndex: 'name',
    key: 'name',
    width: 180,
    customRender: ({ text, record }: { text: string, record: any }) => {
      return h('div', {}, [
        h('div', { style: { fontWeight: 'bold' } }, text),
      ])
    }
  },
  {
    title: '负责人',
    dataIndex: 'owner_name',
    key: 'owner_name',
    width: 150,
    customRender: ({ text }: { text: string }) => {
      return h(Space, {}, [
        h(Avatar, { size: 'small', style: { backgroundColor: '#1890ff' } }, text ? text.charAt(0) : '?'),
        h('span', {}, text || '-')
      ])
    }
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 120,
    customRender: ({ text }: { text: string }) => {
      const statusInfo = statusMap[text] || { text: text, color: 'default' }
      return h(Tag, { color: statusInfo.color }, statusInfo.text)
    }
  },
  {
    title: '标签',
    dataIndex: 'tags',
    key: 'tags',
    width: 150,
    customRender: ({ text }: { text: string | string[] }) => {
      // 处理字符串：解析JSON为数组
      let tagsArray: string[] = [];
      if (typeof text === 'string') {
        // 解析JSON字符串格式的数组
        tagsArray = JSON.parse(text);
      } else if (Array.isArray(text)) {
        // 兼容原生数组格式
        tagsArray = text;
      }

      return h('div', {}, tagsArray.map(tag =>
          h(Tag, {
            color: tagColors[tag],
            key: tag,
            style: { margin: '2px' }
          }, tagNames[tag] || tag)
      ))
    }
  },
  {
    title: '场景数',
    dataIndex: 'scenario_count',
    key: 'scenario_count',
    width: 120
  },
  {
    title: '任务数',
    dataIndex: 'task_count',
    key: 'task_count',
    width: 120
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 140,
    customRender: ({ text }: { text?: string | null }) => {
      if (!text || !dayjs(text).isValid()) {
        return '-'
      }
      // 核心格式化：传入格式模板即可
      // YYYY-MM-DD = 仅日期
      return dayjs(text).format('YYYY-MM-DD HH:mm:ss')
    }
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    customRender: ({ record }: { record: any }) => {
      return h(Space, { size: 'small' }, [
        h(Tooltip, { title: '查看' }, {
          default: () => h(Button, {
            type: 'link',
            icon: h(EyeOutlined),
            onClick: () => viewProject(record.id)
          })
        }),
        h(Tooltip, { title: '编辑' }, {
          default: () => h(Button, {
            type: 'link',
            icon: h(EditOutlined),
            onClick: () => showEditModal(record.id)
          })
        }),
        h(Tooltip, { title: '删除' }, {
          default: () => h(Button, {
            type: 'link',
            danger: true,
            icon: h(DeleteOutlined),
            onClick: () => deleteProject(record.id)
          })
        })
      ])
    }
  }
]

const handleOnCloseDrawer = () => {
  state.modalVisible = false
}
// 新增项目-提交
const handleSubmitOk = () => {
  console.log(state.formData)
}

onMounted(() => {
  handleGetProjectList()
})

// 监听页码变化
const handlePageChange = (page: number, pageSize: number) => {
  state.currentPage = page
  state.pageSize = pageSize
  handleGetProjectList({
    page,
    page_size: pageSize,
    name: state.searchFilters.name,
    status: state.searchFilters.status,
    priority: state.searchFilters.priority,
    tags: state.searchFilters.tags,
    owner_name: state.searchFilters.owner.name,
    owner_id: state.searchFilters.owner.id
  })
}

</script>

<template>
  <div class="app-container">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <div class="page-title-section">
        <h1 class="page-title">项目管理</h1>
        <p class="page-subtitle">压测项目创建、团队协作、资源配置，为压测工作提供组织管理</p>
      </div>

      <Space>
        <!-- 视图切换 -->
        <Button.Group>
          <Button
              :type="state.viewMode === 'card' ? 'primary' : 'default'"
          >
            <template #icon><AppstoreOutlined /></template>
            卡片视图
          </Button>
          <Button
              :type="state.viewMode === 'table' ? 'primary' : 'default'"
          >
            <template #icon><UnorderedListOutlined /></template>
            表格视图
          </Button>
        </Button.Group>

        <!-- 新增项目按钮 -->
        <Button type="primary" @click="showAddModal">
          <template #icon><PlusOutlined /></template>
          新增项目
        </Button>
      </Space>
    </div>


    <!-- 筛选区域 -->
    <ACard title="项目筛选" class="filter-card">
      <template #extra><FilterOutlined /></template>

      <Row :gutter="16">
        <Col :span="6">
          <Input
              v-model:value="state.searchFilters.name"
              placeholder="输入项目名称关键字"
              allow-clear
              @pressEnter="applyFilters"
          />
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.status"
              placeholder="项目状态"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部状态</Select.Option>
            <Select.Option value="active">启用中</Select.Option>
            <Select.Option value="inactive">已停用</Select.Option>
            <Select.Option value="archived">已归档</Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.tags"
              placeholder="项目标签"
              allow-clear
              style="width: 100%"
              multiple
          >
            <Select.Option value="">全部标签</Select.Option>
            <Select.Option value="ecommerce">电商</Select.Option>
            <Select.Option value="api">API接口</Select.Option>
            <Select.Option value="user">用户系统</Select.Option>
            <Select.Option value="payment">支付系统</Select.Option>
            <Select.Option value="search">搜索引擎</Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Select
              v-model:value="state.searchFilters.owner_id"
              placeholder="负责人"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部负责人</Select.Option>
            <Select.Option value="张三">张三</Select.Option>
            <Select.Option value="李四">李四</Select.Option>
            <Select.Option value="王五">王五</Select.Option>
            <Select.Option value="赵六">赵六</Select.Option>
          </Select>
        </Col>
      </Row>

      <Divider />

      <Row justify="space-between">
        <Col>
          <Button >
            <template #icon><RedoOutlined /></template>
            重置筛选条件
          </Button>
        </Col>
        <Col>
          <Button type="primary" >
            <template #icon><SearchOutlined /></template>
            查询项目
          </Button>
        </Col>
      </Row>
    </ACard>

    <!-- 项目展示区域 -->
    <div v-if="state.viewMode === 'card'">
      <!-- 卡片视图 -->
      <Row :gutter="[16, 16]" v-if="paginatedProjects.length > 0">
        <Col :span="8" v-for="project in paginatedProjects" :key="project.id">
          <ACard class="project-card" hoverable>
            <template #title>
              <div class="project-card-header">
                <h3 class="project-name">{{ project.name }}</h3>
                <div class="project-id">{{ project.id }} ({{ project.key || '-' }})</div>
              </div>
            </template>

            <template #extra>
              <Tag :color="statusMap[project.status]?.color || 'default'">
                {{ statusMap[project.status]?.text || project.status }}
              </Tag>
            </template>

            <div class="project-description">{{ project.description || '暂无描述' }}</div>

            <div class="project-tags">
              <Tag
                  v-for="tag in (Array.isArray(project.tags) ? project.tags : [])"
                  :key="tag"
                  :color="tagColors[tag] || 'default'"
                  size="small"
              >
                {{ tagNames[tag] || tag }}
              </Tag>
            </div>

            <div class="project-meta">
              <div class="meta-item">
                <span class="meta-label">负责人</span>
                <div class="meta-value">
                  <Avatar size="small" style="backgroundColor: #1890ff">
                    {{ (project.owner_name || '?').charAt(0) }}
                  </Avatar>
                  {{ project.owner_name || '未分配' }}
                </div>
              </div>

              <div class="meta-item">
                <span class="meta-label">优先级</span>
                <div class="meta-value">{{ priorityMap[project.priority] || '-' }}</div>
              </div>

              <div class="meta-item">
                <span class="meta-label">场景数</span>
                <div class="meta-value">{{ project.scenarios_count || 0 }}</div>
              </div>

              <div class="meta-item">
                <span class="meta-label">任务数</span>
                <div class="meta-value">{{ project.tasks_count || 0 }}</div>
              </div>
            </div>

            <div class="project-performance">
              <div class="performance-item">
                <div class="performance-value" style="color: #52c41a;">
                  {{ project.success_rate || 0 }}%
                </div>
                <div class="performance-label">成功率</div>
              </div>
              <div class="performance-item">
                <div class="performance-value">{{ project.avg_response_time || 0 }}ms</div>
                <div class="performance-label">平均响应</div>
              </div>
              <div class="performance-item">
                <div class="performance-value" style="color: #1890ff;">
                  {{ project.last_task_date ? project.last_task_date.split(' ')[0] : '-' }}
                </div>
                <div class="performance-label">最后执行</div>
              </div>
            </div>

            <template #actions>
              <Tooltip title="查看">
                <Button type="link" >
                  <template #icon><EyeOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="编辑">
                <Button type="link" >
                  <template #icon><EditOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="删除">
                <Button type="link" danger >
                  <template #icon><DeleteOutlined /></template>
                </Button>
              </Tooltip>
            </template>
          </ACard>
        </Col>
      </Row>

      <!-- 卡片视图空状态 -->
      <div v-if="paginatedProjects.length === 0" class="empty-state">
        <div class="empty-icon">
          <ProjectOutlined />
        </div>
        <h3>暂无项目数据</h3>
        <p>当前没有找到符合筛选条件的项目，请尝试调整筛选条件或创建新的项目。</p>
        <Button type="primary" >
          <template #icon><PlusOutlined /></template>
          新增项目
        </Button>
      </div>
    </div>

    <!-- 表格视图 -->
    <div v-else>
      <ACard>
        <Table
            :columns="columns"
            :data-source="paginatedProjects"
            :pagination="false"
            row-key="id"
        >
          <template #emptyText>
            <div class="empty-state">
              <div class="empty-icon">
                <ProjectOutlined />
              </div>
              <h3>暂无项目数据</h3>
              <p>当前没有找到符合筛选条件的项目，请尝试调整筛选条件或创建新的项目。</p>
            </div>
          </template>
        </Table>
      </ACard>
    </div>

    <!-- 分页 -->
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

    <!-- 新增/编辑项目抽屉   -->
    <a-drawer
      :title="state.modalTitle"
      width="720px"
      :open="state.modalVisible"
      :close="handleOnCloseDrawer"
    >
      <a-form layout="vertical">
        <a-form-item label="项目名称" required>
          <Input v-model:value="state.formData.name"></Input>
        </a-form-item>
        <Row :gutter="16">
          <Col :span="12">
            <a-form-item label="项目状态" required>
              <Select v-model:value="state.formData.status"></Select>
            </a-form-item>
          </Col>
          <Col :span="12">
            <a-form-item label="项目优先级" required>
              <Select v-model:value="state.formData.priority"></Select>
            </a-form-item>
          </Col>
        </Row>
        <a-form-item label="项目负责人" required>
          <Input v-model:value="state.formData.owner"></Input>
        </a-form-item>
        <a-form-item >
          <a-checkbox-group v-model:value="state.formData.tags" :options="tagsOptions">
            <template #label = "{label}">
              <a-tag :color="tagColors[label]">{{tagNames[label]}}</a-tag>
            </template>
          </a-checkbox-group>
          <template #label>
            <a-space>
              <span>项目标签</span>
              <a-button type="link" :icon="h(PlusOutlined)">添加标签</a-button>
            </a-space>
          </template>
        </a-form-item>
        <a-form-item label="项目描述">
          <a-textarea v-model:value="state.formData.description"></a-textarea>
        </a-form-item>
      </a-form>

      <template #extra>
        <a-space>
          <a-button @click="handleOnCloseDrawer">取消</a-button>
          <a-button type="primary" @click="handleSubmitOk">保存</a-button>
        </a-space>
      </template>
    </a-drawer>
  </div>
</template>

<style scoped>
.app-container {
  padding: 10px;
  min-height: 100vh;
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

.project-card {
  padding: 20px 0;
  margin-bottom: 20px;
  height: 100%;
}

.project-card-header {
  margin-bottom: 12px;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: rgba(0, 0, 0, 0.85);
}

.project-id {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-bottom: 8px;
}

.project-description {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
  line-height: 1.5;
  margin-bottom: 12px;
}

.project-tags {
  margin-bottom: 16px;
}

.project-meta {
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

.project-performance {
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

  .project-card {
    margin-bottom: 16px;
  }
}
</style>