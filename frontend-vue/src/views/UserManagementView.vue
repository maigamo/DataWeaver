<template>
  <div class="user-management-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2><el-icon><User /></el-icon> 用户管理</h2>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon> 创建新用户
          </el-button>
        </div>
      </template>

      <div class="search-bar">
        <el-input
          v-model="searchTerm"
          placeholder="搜索用户"
          class="search-input"
          clearable
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button @click="handleSearch">搜索</el-button>
          </template>
        </el-input>

        <el-select v-model="pageSize" class="page-size-select">
          <el-option :value="10" label="10条/页" />
          <el-option :value="20" label="20条/页" />
          <el-option :value="50" label="50条/页" />
        </el-select>
      </div>

      <el-table :data="users" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80">
          <template #label>
            <el-icon><Key /></el-icon> ID
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名">
          <template #label>
            <el-icon><User /></el-icon> 用户名
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色">
          <template #label>
            <el-icon><UserFilled /></el-icon> 角色
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #label>
            <el-icon><CircleCheck /></el-icon> 状态
          </template>
          <template #default="{ row }">
            <el-tag :type="row.status === '启用' ? 'success' : 'danger'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #label>
            <el-icon><Calendar /></el-icon> 创建时间
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录">
          <template #label>
            <el-icon><Timer /></el-icon> 最后登录
          </template>
          <template #default="{ row }">
            {{ row.last_login || '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #label>
            <el-icon><Setting /></el-icon> 操作
          </template>
          <template #default="{ row }: { row: User }">
            <el-button
              size="small"
              type="primary"
              @click="handleEdit(row)"
              :disabled="row.username === 'admin' && row.role === '超级管理员'"
            >
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
              :disabled="row.username === 'admin' && row.role === '超级管理员'"
            >
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建新用户"
      width="500px"
    >
      <el-form :model="createForm" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username" required>
          <el-input v-model="createForm.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password" required>
          <el-input v-model="createForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="createForm.role">
            <el-option label="操作员" value="操作员" />
            <el-option label="普通用户" value="普通用户" />
            <el-option label="普通管理员" value="普通管理员" />
            <el-option label="超级管理员" value="超级管理员" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" required>
          <el-select v-model="createForm.status">
            <el-option label="启用" value="启用" />
            <el-option label="禁用" value="禁用" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createUser">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑用户"
      width="500px"
    >
      <el-form :model="editForm" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username" required>
          <el-input v-model="editForm.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="editForm.password"
            type="password"
            show-password
            placeholder="留空表示不修改"
          />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="editForm.role">
            <el-option label="操作员" value="操作员" />
            <el-option label="普通用户" value="普通用户" />
            <el-option label="普通管理员" value="普通管理员" />
            <el-option label="超级管理员" value="超级管理员" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" required>
          <el-select v-model="editForm.status">
            <el-option label="启用" value="启用" />
            <el-option label="禁用" value="禁用" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Plus, Search, Edit, Delete, Key, UserFilled, CircleCheck, Calendar, Timer, Setting } from '@element-plus/icons-vue'
import apiClient from '../api/config'

interface User {
  id: number
  username: string
  role: string
  status: string
  created_at: string
  last_login: string | null
}

const users = ref<User[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchTerm = ref('')

const showCreateDialog = ref(false)
const showEditDialog = ref(false)

const createForm = reactive({
  username: '',
  password: '',
  role: '操作员',
  status: '启用'
})

const editForm = reactive({
  id: null as number | null,
  username: '',
  password: '',
  role: '',
  status: ''
})

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6位', trigger: 'blur' },
    { max: 256, message: '密码长度不能超过256个字符', trigger: 'blur' }
  ]
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    const response = await apiClient.get('/users', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        search_term: searchTerm.value
      }
    })
    users.value = response.data.users
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  }
}

// 创建用户
const createUser = async () => {
  if (!createForm.username || !createForm.password) {
    ElMessage.warning('请填写必填项')
    return
  }

  try {
    await apiClient.post(
      '/users',
      {
        username: createForm.username,
        password: createForm.password,
        role: createForm.role,
        status: createForm.status
      }
    )
    ElMessage.success('用户创建成功')
    showCreateDialog.value = false
    fetchUsers()
    // 重置表单
    Object.assign(createForm, {
      username: '',
      password: '',
      role: '操作员',
      status: '启用'
    })
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建用户失败')
  }
}

// 编辑用户
const handleEdit = (row: User) => {
  Object.assign(editForm, {
    id: row.id,
    username: row.username,
    password: '',
    role: row.role,
    status: row.status
  })
  showEditDialog.value = true
}

// 更新用户
const updateUser = async () => {
  if (!editForm.username) {
    ElMessage.warning('用户名不能为空')
    return
  }

  try {
    const data = {
      username: editForm.username,
      role: editForm.role,
      status: editForm.status,
      ...(editForm.password ? { password: editForm.password } : {})
    }

    await apiClient.put(
      `/users/${editForm.id}`,
      data
    )
    ElMessage.success('用户更新成功')
    showEditDialog.value = false
    fetchUsers()
  } catch (error: any) {
    let errorMessage = '更新用户失败'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    }
    ElMessage.error(errorMessage)
  }
}

// 删除用户
const handleDelete = (row: User) => {
  if (row.username === 'admin' && row.role === '超级管理员') {
    ElMessage.warning('不能删除默认超级管理员账号')
    return
  }

  ElMessageBox.confirm(
    `确定要删除用户 ${row.username} 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await apiClient.delete(`/users/${row.id}`)
      ElMessage.success('用户删除成功')
      fetchUsers()
    } catch (error) {
      ElMessage.error('删除用户失败')
    }
  })
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

// 分页
const handleSizeChange = () => {
  currentPage.value = 1
  fetchUsers()
}

const handleCurrentChange = () => {
  fetchUsers()
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-management-container {
  padding: 20px;
  max-width: 2048px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  display: flex;
  margin-bottom: 20px;
  gap: 10px;
}

.search-input {
  width: 300px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>