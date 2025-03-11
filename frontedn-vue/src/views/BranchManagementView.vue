<template>
  <div class="branch-management-container">
    <h1>分支管理</h1>
    <el-card class="branch-card">
      <div class="branch-header">
        <el-button type="primary" @click="dialogVisible = true">
          <el-icon><Plus /></el-icon> 新建分支
        </el-button>
        <el-input
          v-model="searchQuery"
          placeholder="搜索分支"
          class="search-input"
          clearable
          :prefix-icon="Search"
        />
      </div>

      <el-table :data="filteredBranches" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="分支名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column prop="created_by" label="创建人" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="editBranch(scope.row)">编辑</el-button>
            <el-popconfirm
              title="确定删除该分支吗？"
              @confirm="deleteBranch(scope.row.name)"
            >
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑分支对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑分支' : '新建分支'"
      width="500px"
    >
      <el-form :model="branchForm" label-width="80px">
        <el-form-item label="分支名称">
          <el-input v-model="branchForm.name" placeholder="请输入分支名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="branchForm.description"
            type="textarea"
            placeholder="请输入分支描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveBranch" :loading="saveLoading">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import axios from 'axios'

interface Branch {
  id: number
  name: string
  description: string
  created_at: string
  created_by: string
}

const branches = ref<Branch[]>([])
const loading = ref(false)
const saveLoading = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const searchQuery = ref('')

const branchForm = reactive({
  id: 0,
  name: '',
  description: ''
})

const filteredBranches = computed(() => {
  if (!searchQuery.value) return branches.value
  return branches.value.filter(branch => 
    branch.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    branch.description.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const fetchBranches = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未登录或会话已过期')
      return
    }

    const response = await axios.get('/api/branches', {
      headers: { Authorization: `Bearer ${token}` }
    })

    // 修正：后端返回的是 {branches: [...]} 格式，需要正确获取branches数组
    branches.value = response.data.branches || []
  } catch (error) {
    ElMessage.error('获取分支数据失败')
    console.error('获取分支数据失败:', error)
  } finally {
    loading.value = false
  }
}

const editBranch = (branch: Branch) => {
  isEditing.value = true
  branchForm.id = branch.id
  branchForm.name = branch.name
  branchForm.description = branch.description
  dialogVisible.value = true
}

const resetForm = () => {
  branchForm.id = 0
  branchForm.name = ''
  branchForm.description = ''
  isEditing.value = false
}

const saveBranch = async () => {
  if (!branchForm.name) {
    ElMessage.warning('请输入分支名称')
    return
  }

  saveLoading.value = true
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未登录或会话已过期')
      return
    }

    if (isEditing.value) {
      await axios.put(`/api/branches/${branchForm.id}`, {
        name: branchForm.name,
        description: branchForm.description
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      ElMessage.success('分支更新成功')
    } else {
      // 创建FormData对象用于上传文件
      const formData = new FormData()
      formData.append('branch_name', branchForm.name)
      
      // 创建一个空的SQL文件
      const emptyFile = new File(['-- 空SQL模板文件'], 'j_initData.sql', { type: 'text/plain' })
      formData.append('sql_file', emptyFile)
      
      await axios.post('/api/branches', formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      })
      ElMessage.success('分支创建成功')
    }

    dialogVisible.value = false
    resetForm()
    fetchBranches()
  } catch (error) {
    ElMessage.error(isEditing.value ? '更新分支失败' : '创建分支失败')
    console.error('保存分支失败:', error)
  } finally {
    saveLoading.value = false
  }
}

const deleteBranch = async (branchName: string) => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未登录或会话已过期')
      return
    }

    await axios.delete(`/api/branches/${branchName}`, {
      headers: { Authorization: `Bearer ${token}` }
    })

    ElMessage.success('分支删除成功')
    fetchBranches()
  } catch (error) {
    ElMessage.error('删除分支失败')
    console.error('删除分支失败:', error)
  }
}

onMounted(() => {
  fetchBranches()
})
</script>

<style scoped>
.branch-management-container {
  padding: 20px;
  max-width: 2048px;
  margin: 0 auto;
}

.branch-card {
  margin-top: 20px;
}

.branch-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.search-input {
  width: 300px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
</style>