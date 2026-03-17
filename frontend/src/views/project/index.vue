<script setup lang="ts">
import { reactive, computed, onMounted, h } from 'vue'
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
  Tooltip
} from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  RedoOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  UserAddOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  ProjectOutlined,
  FilterOutlined
} from '@ant-design/icons-vue'
import { ProjectApi } from "@/api/project.ts";
import { QueryProjectList } from "@/types/project";
import type {ProjectInfo, ProjectMemberInfo} from "../../types/project";
import { useUserStore } from '@/store/modules/user'
import { UserApi } from '@/api/user'
import type { UserOption } from '@/types/user'

const userStore = useUserStore()

const normalizeStatus = (status: string | null | undefined): string | null => {
  if (!status) {
    return null
  }
  return status.toUpperCase()
}

const normalizePriority = (priority: string | null | undefined): string | null => {
  if (!priority) {
    return null
  }
  return priority.toLowerCase()
}

const parseProjectTags = (tags: ProjectInfo["tags"]): string[] => {
  if (Array.isArray(tags)) {
    return tags
  }

  if (typeof tags === 'string' && tags.trim()) {
    try {
      const parsed = JSON.parse(tags)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return tags.split(',').map(tag => tag.trim()).filter(Boolean)
    }
  }

  return []
}

const normalizeProject = (project: ProjectInfo): ProjectInfo => ({
  ...project,
  status: normalizeStatus(project.status),
  priority: normalizePriority(project.priority),
  tags: parseProjectTags(project.tags),
  members: project.members || [],
})

// 响应式数据
const state = reactive({
  // 项目数据
  projects: [] as ProjectInfo[],
  filteredProjects: [] as ProjectInfo[],
  ownerOptions: [] as UserOption[],
  projectMembers: [] as ProjectMemberInfo[],
  memberDraft: {
    member_id: undefined as number | undefined,
    member_role: 'VIEWER',
  },

  // 分页相关
  currentPage: 1,
  pageSize: 8,
  total: 0,

  // 视图模式
  viewMode: 'table', // 'card' 或 'table'

  // 模态框相关
  modalVisible: false,
  detailVisible: false,
  detailLoading: false,
  modalTitle: '创建新项目',
  isEditing: false,
  currentEditId: null as number | null,
  detailProject: null as ProjectInfo | null,

  // 表单数据
  formData: {
    name: '',
    status: 'ACTIVE',
    owner_id: userStore.userId || 0,
    owner_name: userStore.name || '',
    priority: 'medium',
    description: '',
    tags: [] as string[],
  },

  // 筛选条件
  searchFilters: {
    name: '',
    status: '',
    tags: [],
    owner_id: undefined as number | undefined,
    owner_name: '',
    priority: '',
  }
})


const paginatedProjects = computed(() => {
  const start = (state.currentPage - 1) * state.pageSize
  const end = start + state.pageSize
  return state.filteredProjects.slice(start, end)
})

const ownerFilterOptions = computed(() => {
  const ownerMap = new Map<number, string>()

  state.projects.forEach(project => {
    if (project.owner_id && project.owner_name) {
      ownerMap.set(project.owner_id, project.owner_name)
    }
  })

  state.ownerOptions.forEach(user => {
    if (user.id && user.name) {
      ownerMap.set(user.id, user.name)
    }
  })

  return Array.from(ownerMap.entries())
    .map(([id, name]) => ({ id, name }))
    .sort((a, b) => a.name.localeCompare(b.name))
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

const memberRoleMap: Record<string, { text: string; color: string }> = {
  OWNER: { text: '负责人', color: 'gold' },
  ADMIN: { text: '管理员', color: 'blue' },
  DEVELOPER: { text: '开发', color: 'green' },
  TEACHER: { text: '测试', color: 'purple' },
  VIEWER: { text: '只读', color: 'default' },
}

const memberRoleOptions = [
  { label: '管理员', value: 'ADMIN' },
  { label: '开发', value: 'DEVELOPER' },
  { label: '测试', value: 'TEACHER' },
  { label: '只读', value: 'VIEWER' },
]

// 方法
const applyFilters = () => {
  const { name, status, tags, owner_name, priority } = state.searchFilters

  state.filteredProjects = state.projects.filter(project => {
    if (name && !project.name.toLowerCase().includes(name.toLowerCase())) {
      return false
    }

    if (status && project.status !== status) {
      return false
    }

    const projectTags = parseProjectTags(project.tags)
    if (tags.length > 0 && !tags.every(tag => projectTags.includes(tag))) {
      return false
    }

    if (owner_name && project.owner_name !== owner_name) {
      return false
    }

    if (priority && project.priority !== priority) {
      return false
    }

    return true
  })

  state.currentPage = 1
  state.total = state.filteredProjects.length
}

const resetFilters = () => {
  state.searchFilters = {
    name: '',
    status: '',
    tags: [],
    owner_id: undefined,
    owner_name: '',
    priority: ''
  }
  state.filteredProjects = [...state.projects]
  state.currentPage = 1
  state.total = state.projects.length
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
    status: 'ACTIVE',
    owner_id: userStore.userId || 0,
    owner_name: userStore.name || '',
    priority: 'medium',
    description: '',
    tags: [],
  }
  state.projectMembers = []
  state.modalVisible = true
}

const showEditModal = async (projectId: number) => {
  const project = state.projects.find(p => p.id === projectId)
  if (!project) return

  state.modalTitle = '编辑项目'
  state.isEditing = true
  state.currentEditId = projectId
  state.formData = {
    name: project.name,
    status: project.status || 'ACTIVE',
    owner_id: project.owner_id,
    owner_name: project.owner_name || '',
    priority: project.priority || 'medium',
    description: project.description || '',
    tags: parseProjectTags(project.tags),
  }
  state.projectMembers = []
  await fetchProjectMembers(projectId)
  state.modalVisible = true
}

const handleModalOk = async () => {
  const { name, status, owner_id, owner_name, priority, description, tags } = state.formData

  if (!name.trim()) {
    Modal.error({ title: '错误', content: '请输入项目名称' })
    return
  }

  if (!owner_id || !owner_name.trim()) {
    Modal.error({ title: '错误', content: '请选择或填写项目负责人' })
    return
  }

  try {
    if (state.isEditing && state.currentEditId) {
      const updateData = {
        id: state.currentEditId,
        name,
        status,
        priority,
        description,
        tags,
        owner_id,
        owner_name,
      }

      await ProjectApi.updateProject(updateData)
      Modal.success({ title: '成功', content: `项目 ${name} 已更新` })
    } else {
      const createData = {
        name,
        priority,
        description,
        tags,
        owner_id,
        owner_name,
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
      owner_name: state.searchFilters.owner_name,
      owner_id: state.searchFilters.owner_id,
      tags: state.searchFilters.tags,
    })

    state.modalVisible = false
  } catch (error) {
    console.error('保存项目失败:', error)
    Modal.error({ title: '错误', content: '保存项目失败，请稍后重试' })
  }
}

const handleOwnerChange = (ownerId: number) => {
  const owner = state.ownerOptions.find(item => item.id === ownerId)
  if (!owner) {
    return
  }
  state.formData.owner_id = owner.id
  state.formData.owner_name = owner.name
}

const fetchProjectMembers = async (projectId: number) => {
  try {
    const response = await ProjectApi.getProjectMembers({ id: projectId })
    state.projectMembers = response.data
  } catch (error) {
    console.error('获取项目成员失败:', error)
    state.projectMembers = []
  }
}

const addProjectMember = async () => {
  if (!state.currentEditId) {
    return
  }
  if (!state.memberDraft.member_id) {
    Modal.error({ title: '错误', content: '请选择成员' })
    return
  }
  await ProjectApi.addProjectMember({
    project_id: state.currentEditId,
    member_id: state.memberDraft.member_id,
    member_role: state.memberDraft.member_role,
  })
  state.memberDraft.member_id = undefined
  state.memberDraft.member_role = 'VIEWER'
  await fetchProjectMembers(state.currentEditId)
  message.success('项目成员已添加')
}

const updateProjectMemberRole = async (member: ProjectMemberInfo, role: string) => {
  if (!state.currentEditId || member.member_role === 'OWNER') {
    return
  }
  await ProjectApi.updateProjectMemberRole({
    project_id: state.currentEditId,
    member_id: member.member_id,
    member_role: role,
  })
  await fetchProjectMembers(state.currentEditId)
  message.success('成员角色已更新')
}

const removeProjectMember = async (member: ProjectMemberInfo) => {
  if (!state.currentEditId || member.member_role === 'OWNER') {
    return
  }
  await ProjectApi.removeProjectMember(state.currentEditId, member.member_id)
  await fetchProjectMembers(state.currentEditId)
  message.success('成员已移除')
}

const deleteProject = async (projectId: number) => {
  const project = state.projects.find(p => p.id === projectId)
  if (!project) return

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除项目 "${project.name}" 吗？此操作不可恢复，且会同时删除项目下的所有场景和任务。`,
    async onOk() {
      try {
        await ProjectApi.deleteProject({ id: projectId })

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

const viewProject = async (projectId: number) => {
  state.detailVisible = true
  state.detailLoading = true
  try {
    const [projectResponse, membersResponse] = await Promise.all([
      ProjectApi.getProjectInfo({ id: projectId }),
      ProjectApi.getProjectMembers({ id: projectId }),
    ])
    state.detailProject = normalizeProject({
      ...projectResponse.data,
      members: membersResponse.data,
    } as ProjectInfo)
  } catch (error) {
    console.error('获取项目详情失败:', error)
    Modal.error({
      title: '获取详情失败',
      content: '项目详情暂时无法加载，请稍后重试',
    })
    state.detailVisible = false
  } finally {
    state.detailLoading = false
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
      owner_name: data?.owner_name || state.searchFilters.owner_name,
      owner_id: data?.owner_id || state.searchFilters.owner_id,
    }

    const response = await ProjectApi.getProjectList(params);

    state.projects = response.data.results.map(normalizeProject) as ProjectInfo[]
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

const fetchOwnerOptions = async () => {
  try {
    const response = await UserApi.userOptions()
    state.ownerOptions = response.data
    if (!state.formData.owner_id && response.data.length > 0) {
      handleOwnerChange(response.data[0].id)
    }
  } catch (error) {
    console.error('获取用户选项失败:', error)
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
      const tagsArray = parseProjectTags(text as ProjectInfo["tags"])

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
  state.projectMembers = []
}

const handleCloseDetailDrawer = () => {
  state.detailVisible = false
  state.detailProject = null
  state.detailLoading = false
}

const openDetailEdit = async () => {
  const detailProjectId = state.detailProject?.id
  if (!detailProjectId) {
    return
  }
  handleCloseDetailDrawer()
  await showEditModal(detailProjectId)
}
// 新增项目-提交
onMounted(() => {
  fetchOwnerOptions()
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
    owner_name: state.searchFilters.owner_name,
    owner_id: state.searchFilters.owner_id
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
            <Select.Option value="ACTIVE">启用中</Select.Option>
            <Select.Option value="INACTIVE">已停用</Select.Option>
            <Select.Option value="ARCHIVED">已归档</Select.Option>
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
              v-model:value="state.searchFilters.owner_name"
              placeholder="负责人"
              allow-clear
              style="width: 100%"
          >
            <Select.Option value="">全部负责人</Select.Option>
            <Select.Option
              v-for="owner in ownerFilterOptions"
              :key="owner.id"
              :value="owner.name"
            >
              {{ owner.name }}
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
                <div class="project-id">ID: {{ project.id }}</div>
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
                <div class="meta-value">{{ project.scenario_count || 0 }}</div>
              </div>

              <div class="meta-item">
                <span class="meta-label">任务数</span>
                <div class="meta-value">{{ project.task_count || 0 }}</div>
              </div>
            </div>

            <template #actions>
              <Tooltip title="查看">
                <Button type="link" @click="viewProject(project.id)">
                  <template #icon><EyeOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="编辑">
                <Button type="link" @click="showEditModal(project.id)">
                  <template #icon><EditOutlined /></template>
                </Button>
              </Tooltip>
              <Tooltip title="删除">
                <Button type="link" danger @click="deleteProject(project.id)">
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
        <Button type="primary" @click="showAddModal">
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
              <Select v-model:value="state.formData.status">
                <Select.Option value="ACTIVE">启用中</Select.Option>
                <Select.Option value="INACTIVE">已停用</Select.Option>
                <Select.Option value="ARCHIVED">已归档</Select.Option>
              </Select>
            </a-form-item>
          </Col>
          <Col :span="12">
            <a-form-item label="项目优先级" required>
              <Select v-model:value="state.formData.priority">
                <Select.Option value="high">高</Select.Option>
                <Select.Option value="medium">中</Select.Option>
                <Select.Option value="low">低</Select.Option>
              </Select>
            </a-form-item>
          </Col>
        </Row>
        <a-form-item label="项目负责人" required>
          <Select v-model:value="state.formData.owner_id" @change="handleOwnerChange">
            <Select.Option v-for="user in state.ownerOptions" :key="user.id" :value="user.id">
              {{ user.name }} ({{ user.username }})
            </Select.Option>
          </Select>
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

      <div v-if="state.isEditing" class="member-section">
        <Divider orientation="left">项目成员</Divider>
        <div class="member-toolbar">
          <Select
            v-model:value="state.memberDraft.member_id"
            placeholder="选择用户"
            style="min-width: 240px"
            allow-clear
          >
            <Select.Option
              v-for="user in state.ownerOptions.filter(item => item.id !== state.formData.owner_id)"
              :key="user.id"
              :value="user.id"
            >
              {{ user.name }} ({{ user.username }})
            </Select.Option>
          </Select>
          <Select v-model:value="state.memberDraft.member_role" style="width: 160px">
            <Select.Option v-for="role in memberRoleOptions" :key="role.value" :value="role.value">
              {{ role.label }}
            </Select.Option>
          </Select>
          <Button type="dashed" @click="addProjectMember">
            <template #icon><UserAddOutlined /></template>
            添加成员
          </Button>
        </div>

        <Table
          :data-source="state.projectMembers"
          :pagination="false"
          row-key="id"
          size="small"
          class="member-table"
        >
          <a-table-column title="成员" data-index="member_name" key="member_name" />
          <a-table-column title="角色" key="member_role">
            <template #default="{ record }">
              <Tag :color="memberRoleMap[record.member_role]?.color || 'default'">
                {{ memberRoleMap[record.member_role]?.text || record.member_role }}
              </Tag>
            </template>
          </a-table-column>
          <a-table-column title="加入时间" data-index="join_time" key="join_time">
            <template #default="{ record }">
              {{ record.join_time ? dayjs(record.join_time).format('YYYY-MM-DD HH:mm:ss') : '-' }}
            </template>
          </a-table-column>
          <a-table-column title="操作" key="actions">
            <template #default="{ record }">
              <Space>
                <Select
                  v-if="record.member_role !== 'OWNER'"
                  :value="record.member_role"
                  style="width: 140px"
                  @change="(value: string) => updateProjectMemberRole(record, value)"
                >
                  <Select.Option v-for="role in memberRoleOptions" :key="role.value" :value="role.value">
                    {{ role.label }}
                  </Select.Option>
                </Select>
                <Button v-else type="link" disabled>负责人</Button>
                <Button
                  type="link"
                  danger
                  :disabled="record.member_role === 'OWNER'"
                  @click="removeProjectMember(record)"
                >
                  移除
                </Button>
              </Space>
            </template>
          </a-table-column>
        </Table>
      </div>

      <template #extra>
        <a-space>
          <a-button @click="handleOnCloseDrawer">取消</a-button>
          <a-button type="primary" @click="handleModalOk">保存</a-button>
        </a-space>
      </template>
    </a-drawer>

    <a-drawer
      title="项目详情"
      width="760px"
      :open="state.detailVisible"
      :close="handleCloseDetailDrawer"
    >
      <div v-if="state.detailLoading" class="detail-loading">
        <a-spin tip="项目详情加载中..." />
      </div>

      <div v-else-if="state.detailProject" class="project-detail">
        <div class="project-detail-hero">
          <div class="project-detail-title-wrap">
            <div class="project-detail-id">项目 ID: {{ state.detailProject.id }}</div>
            <h2 class="project-detail-title">{{ state.detailProject.name }}</h2>
            <div class="project-detail-tags">
              <Tag :color="statusMap[state.detailProject.status || '']?.color || 'default'">
                {{ statusMap[state.detailProject.status || '']?.text || state.detailProject.status || '未知状态' }}
              </Tag>
              <Tag color="processing">
                优先级：{{ priorityMap[state.detailProject.priority || ''] || '-' }}
              </Tag>
              <Tag v-if="state.detailProject.owner_name" color="blue">
                负责人：{{ state.detailProject.owner_name }}
              </Tag>
            </div>
          </div>
          <Button type="primary" @click="openDetailEdit">
            <template #icon><EditOutlined /></template>
            编辑项目
          </Button>
        </div>

        <Row :gutter="[16, 16]" class="detail-metrics">
          <Col :span="12">
            <div class="detail-metric-card">
              <div class="detail-metric-value">{{ state.detailProject.scenario_count || 0 }}</div>
              <div class="detail-metric-label">关联场景</div>
            </div>
          </Col>
          <Col :span="12">
            <div class="detail-metric-card">
              <div class="detail-metric-value">{{ state.detailProject.task_count || 0 }}</div>
              <div class="detail-metric-label">关联任务</div>
            </div>
          </Col>
        </Row>

        <ACard title="基础信息" class="detail-card">
          <div class="detail-grid">
            <div class="detail-field">
              <span class="detail-field-label">创建时间</span>
              <span class="detail-field-value">
                {{ state.detailProject.created_at ? dayjs(state.detailProject.created_at).format('YYYY-MM-DD HH:mm:ss') : '-' }}
              </span>
            </div>
            <div class="detail-field">
              <span class="detail-field-label">更新时间</span>
              <span class="detail-field-value">
                {{ state.detailProject.updated_at ? dayjs(state.detailProject.updated_at).format('YYYY-MM-DD HH:mm:ss') : '-' }}
              </span>
            </div>
            <div class="detail-field detail-field-full">
              <span class="detail-field-label">项目描述</span>
              <p class="detail-description">
                {{ state.detailProject.description || '这个项目还没有填写描述。' }}
              </p>
            </div>
            <div class="detail-field detail-field-full">
              <span class="detail-field-label">项目标签</span>
              <div class="detail-tag-list">
                <Tag
                  v-for="tag in parseProjectTags(state.detailProject.tags)"
                  :key="tag"
                  :color="tagColors[tag] || 'default'"
                >
                  {{ tagNames[tag] || tag }}
                </Tag>
                <span v-if="parseProjectTags(state.detailProject.tags).length === 0" class="detail-empty-text">
                  暂无标签
                </span>
              </div>
            </div>
          </div>
        </ACard>

        <ACard title="项目成员" class="detail-card">
          <div v-if="state.detailProject.members?.length" class="detail-member-list">
            <div
              v-for="member in state.detailProject.members"
              :key="member.id"
              class="detail-member-item"
            >
              <div class="detail-member-main">
                <Avatar size="large" style="background-color: #1677ff">
                  {{ (member.member_name || '?').charAt(0) }}
                </Avatar>
                <div class="detail-member-info">
                  <div class="detail-member-name">{{ member.member_name || `用户 ${member.member_id}` }}</div>
                  <div class="detail-member-meta">
                    <Tag :color="memberRoleMap[member.member_role]?.color || 'default'">
                      {{ memberRoleMap[member.member_role]?.text || member.member_role }}
                    </Tag>
                    <span>
                      加入时间：{{ member.join_time ? dayjs(member.join_time).format('YYYY-MM-DD HH:mm:ss') : '-' }}
                    </span>
                  </div>
                </div>
              </div>
              <Tag :color="member.is_active ? 'success' : 'default'">
                {{ member.is_active ? '启用' : '停用' }}
              </Tag>
            </div>
          </div>
          <div v-else class="detail-empty-text">当前项目还没有额外成员。</div>
        </ACard>
      </div>

      <template #extra>
        <a-space>
          <a-button @click="handleCloseDetailDrawer">关闭</a-button>
          <a-button
            v-if="state.detailProject"
            type="primary"
            @click="openDetailEdit"
          >
            编辑项目
          </a-button>
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

.member-section {
  margin-top: 24px;
}

.member-toolbar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.member-table {
  margin-top: 8px;
}

.detail-loading {
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.project-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.project-detail-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f5f9ff 0%, #eef6ff 100%);
  border: 1px solid #d9e9ff;
}

.project-detail-title-wrap {
  flex: 1;
}

.project-detail-id {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-bottom: 8px;
}

.project-detail-title {
  margin: 0;
  font-size: 26px;
  line-height: 1.2;
  color: rgba(0, 0, 0, 0.88);
}

.project-detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.detail-metrics {
  margin: 0;
}

.detail-metric-card {
  padding: 20px;
  border-radius: 14px;
  background: #fafcff;
  border: 1px solid #edf2fa;
}

.detail-metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #1677ff;
  line-height: 1;
}

.detail-metric-label {
  margin-top: 8px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);
}

.detail-card {
  border-radius: 14px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.detail-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-field-full {
  grid-column: 1 / -1;
}

.detail-field-label {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.detail-field-value {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.88);
}

.detail-description {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: rgba(0, 0, 0, 0.75);
  white-space: pre-wrap;
}

.detail-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 32px;
  align-items: center;
}

.detail-member-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid #edf2fa;
  border-radius: 12px;
  background: #fcfdff;
}

.detail-member-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.detail-member-info {
  min-width: 0;
}

.detail-member-name {
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}

.detail-member-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.detail-empty-text {
  font-size: 13px;
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

  .project-detail-hero {
    flex-direction: column;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-member-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
