<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined, EditOutlined, DeleteOutlined, LockOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { UserApi } from '@/api/user'
import type { UserCreate, UserInfo, UserListQuery, UserUpdate } from '@/types/user'
import { useUserStore } from '@/store/modules/user'

const loading = ref(false)
const modalVisible = ref(false)
const passwordModalVisible = ref(false)
const isEditing = ref(false)
const currentUserId = ref<number | null>(null)
const userStore = useUserStore()

const state = reactive({
  users: [] as UserInfo[],
  total: 0,
  query: {
    page: 1,
    page_size: 10,
    username: '',
    name: '',
    email: '',
    is_active: undefined as boolean | undefined,
  } as UserListQuery,
  formData: {
    username: '',
    password: '',
    name: '',
    email: '',
    phone: '',
    is_active: true,
    is_admin: false,
  } as UserCreate,
  passwordData: {
    password: '',
    confirmPassword: '',
  },
})

const columns = [
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '手机号', dataIndex: 'phone', key: 'phone' },
  { title: '状态', dataIndex: 'is_active', key: 'is_active' },
  { title: '管理员', dataIndex: 'is_admin', key: 'is_admin' },
  { title: '最后登录', dataIndex: 'last_login_at', key: 'last_login_at' },
  { title: '操作', key: 'actions', width: 220 },
]

const modalTitle = computed(() => (isEditing.value ? '编辑用户' : '新增用户'))

const isCurrentAdminUser = (user: UserInfo) => {
  return Boolean(user.is_admin && userStore.userId && user.id === userStore.userId)
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await UserApi.userList(state.query)
    state.users = response.data.results
    state.total = response.data.total
  } finally {
    loading.value = false
  }
}

const resetFilters = async () => {
  state.query = {
    page: 1,
    page_size: 10,
    username: '',
    name: '',
    email: '',
    is_active: undefined,
  }
  await fetchUsers()
}

const openCreateModal = () => {
  isEditing.value = false
  currentUserId.value = null
  state.formData = {
    username: '',
    password: '',
    name: '',
    email: '',
    phone: '',
    is_active: true,
    is_admin: false,
  }
  modalVisible.value = true
}

const openEditModal = (user: UserInfo) => {
  isEditing.value = true
  currentUserId.value = user.id
  state.formData = {
    username: user.username,
    password: '',
    name: user.name,
    email: user.email || '',
    phone: user.phone || '',
    is_active: user.is_active,
    is_admin: user.is_admin,
  }
  modalVisible.value = true
}

const submitForm = async () => {
  if (!state.formData.username.trim()) {
    message.error('请输入用户名')
    return
  }
  if (!state.formData.name.trim()) {
    message.error('请输入姓名')
    return
  }
  if (!isEditing.value && !state.formData.password.trim()) {
    message.error('请输入密码')
    return
  }

  if (isEditing.value && currentUserId.value) {
    const payload: UserUpdate = {
      id: currentUserId.value,
      username: state.formData.username,
      name: state.formData.name,
      email: state.formData.email || undefined,
      phone: state.formData.phone || undefined,
      is_active: state.formData.is_active,
      is_admin: state.formData.is_admin,
    }
    await UserApi.updateUser(payload)
    message.success('用户已更新')
  } else {
    await UserApi.createUser({
      ...state.formData,
      email: state.formData.email || undefined,
      phone: state.formData.phone || undefined,
    })
    message.success('用户已创建')
  }

  modalVisible.value = false
  await fetchUsers()
}

const deleteUser = async (user: UserInfo) => {
  await UserApi.deleteUser(user.id)
  message.success(`用户 ${user.name} 已删除`)
  await fetchUsers()
}

const toggleUserStatus = async (user: UserInfo) => {
  await UserApi.updateUser({
    id: user.id,
    is_active: !user.is_active,
  })
  message.success(`用户已${user.is_active ? '停用' : '启用'}`)
  await fetchUsers()
}

const openResetPasswordModal = (user: UserInfo) => {
  currentUserId.value = user.id
  state.passwordData.password = ''
  state.passwordData.confirmPassword = ''
  passwordModalVisible.value = true
}

const submitResetPassword = async () => {
  if (!state.passwordData.password.trim()) {
    message.error('请输入新密码')
    return
  }
  if (!state.passwordData.confirmPassword.trim()) {
    message.error('请确认新密码')
    return
  }
  if (state.passwordData.password !== state.passwordData.confirmPassword) {
    message.error('两次输入的密码不一致')
    return
  }
  if (!currentUserId.value) {
    return
  }
  await UserApi.resetPassword({
    id: currentUserId.value,
    password: state.passwordData.password,
  })
  passwordModalVisible.value = false
  message.success('密码已重置')
}

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <div class="user-management">
    <a-card title="用户筛选" class="filter-card">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input
            v-model:value="state.query.username"
            placeholder="输入用户名"
            allow-clear
            @pressEnter="fetchUsers"
          />
        </a-col>
        <a-col :span="6">
          <a-input
            v-model:value="state.query.name"
            placeholder="输入姓名"
            allow-clear
            @pressEnter="fetchUsers"
          />
        </a-col>
        <a-col :span="6">
          <a-input
            v-model:value="state.query.email"
            placeholder="输入邮箱"
            allow-clear
            @pressEnter="fetchUsers"
          />
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="state.query.is_active"
            placeholder="用户状态"
            allow-clear
            style="width: 100%"
          >
            <a-select-option :value="true">启用</a-select-option>
            <a-select-option :value="false">停用</a-select-option>
          </a-select>
        </a-col>
      </a-row>

      <a-divider />

      <a-row justify="space-between" :gutter="12">
        <a-col>
          <a-space wrap>
            <a-button @click="resetFilters">
              <template #icon><ReloadOutlined /></template>
              重置筛选条件
            </a-button>
            <a-button type="primary" @click="fetchUsers">
              <template #icon><SearchOutlined /></template>
              查询用户
            </a-button>
          </a-space>
        </a-col>
        <a-col>
          <a-button type="primary" ghost @click="openCreateModal">
            <template #icon><PlusOutlined /></template>
            新增用户
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <a-table
      :columns="columns"
      :data-source="state.users"
      :loading="loading"
      :pagination="false"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'is_active'">
          <a-switch
            :checked="record.is_active"
            checked-children="启用"
            un-checked-children="停用"
            :disabled="isCurrentAdminUser(record)"
            @change="() => toggleUserStatus(record)"
          />
        </template>
        <template v-if="column.key === 'is_admin'">
          <a-tag :color="record.is_admin ? 'blue' : 'default'">
            {{ record.is_admin ? '管理员' : '普通用户' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'last_login_at'">
          {{ record.last_login_at || '-' }}
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button type="link" @click="openEditModal(record)">
              <template #icon><EditOutlined /></template>
              编辑
            </a-button>
            <a-button type="link" @click="openResetPasswordModal(record)">
              <template #icon><LockOutlined /></template>
              重置密码
            </a-button>
            <a-popconfirm title="确认删除该用户？" @confirm="deleteUser(record)">
              <a-button type="link" danger>
                <template #icon><DeleteOutlined /></template>
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <div class="pagination">
      <a-pagination
        v-model:current="state.query.page"
        v-model:pageSize="state.query.page_size"
        :total="state.total"
        show-size-changer
        @change="fetchUsers"
      />
    </div>

    <a-drawer :title="modalTitle" :open="modalVisible" width="520" @close="modalVisible = false">
      <a-form :model="state.formData" layout="vertical">
        <a-form-item label="用户名">
          <a-input v-model:value="state.formData.username" :disabled="isEditing" />
        </a-form-item>
        <a-form-item
          v-if="!isEditing"
          label="密码"
        >
          <a-input-password v-model:value="state.formData.password" />
        </a-form-item>
        <a-form-item label="姓名">
          <a-input v-model:value="state.formData.name" />
        </a-form-item>
        <a-form-item label="邮箱">
          <a-input v-model:value="state.formData.email" />
        </a-form-item>
        <a-form-item label="手机号">
          <a-input v-model:value="state.formData.phone" />
        </a-form-item>
        <a-space>
          <a-checkbox v-model:checked="state.formData.is_active">启用</a-checkbox>
          <a-checkbox v-model:checked="state.formData.is_admin">管理员</a-checkbox>
        </a-space>
      </a-form>
      <template #footer>
        <a-space>
          <a-button @click="modalVisible = false">取消</a-button>
          <a-button type="primary" @click="submitForm">保存</a-button>
        </a-space>
      </template>
    </a-drawer>

    <a-modal v-model:open="passwordModalVisible" title="重置密码" @ok="submitResetPassword">
      <a-form :model="state.passwordData" layout="vertical">
        <a-form-item label="新密码">
          <a-input-password v-model:value="state.passwordData.password" />
        </a-form-item>
        <a-form-item label="确认密码">
          <a-input-password v-model:value="state.passwordData.confirmPassword" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.user-management {
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
}
</style>
