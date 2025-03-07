<template>
  <div class="sql-generator-container">
    <el-row :gutter="20" class="main-row">
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="generator-card">
          <template #header>
            <div class="card-header">
              <h3><el-icon><Document /></el-icon> SQL生成器</h3>
            </div>
          </template>

          <el-form :model="formData" :rules="rules" ref="formRef" label-width="140px" v-if="canGenerateSQL">
            <el-form-item label="用户初始序号" required>
              <el-tooltip
                content="起始用户ID，从此序号开始生成用户数据"
                placement="right"
                effect="light"
              >
                <el-input-number v-model="formData.userStartIndex" :min="1" />
              </el-tooltip>
            </el-form-item>

            <el-form-item label="用户最大序号" required>
              <el-tooltip
                content="结束用户ID，生成用户数据的上限"
                placement="right"
                effect="light"
              >
                <el-input-number v-model="formData.userMaxIndex" :min="1" />
              </el-tooltip>
            </el-form-item>

            <el-form-item label="当前部门序号" required>
              <el-tooltip
                content="部门起始编号，从此序号开始生成部门数据"
                placement="right"
                effect="light"
              >
                <el-input-number v-model="formData.departmentIndex" :min="1" />
              </el-tooltip>
            </el-form-item>

            <el-form-item label="每个部门用户数" required>
              <el-tooltip
                content="单个部门包含的用户数量，决定部门规模"
                placement="right"
                effect="light"
              >
                <el-input-number v-model="formData.usersPerDepartment" :min="1" />
              </el-tooltip>
            </el-form-item>

            <el-form-item label="用户初始设备序号" required>
              <el-tooltip
                content="每个用户的起始设备编号，从此序号开始生成设备数据"
                placement="right"
                effect="light"
              >
                <el-input-number v-model="formData.deviceStartIndex" :min="1" />
              </el-tooltip>
            </el-form-item>

            <el-form-item label="用户最大设备序号" required>
              <el-tooltip
                content="每个用户最多拥有的设备数量，决定用户设备上限"
                placement="right"
                effect="light"
              >
                <el-input-number v-model="formData.deviceMaxIndex" :min="1" />
              </el-tooltip>
            </el-form-item>

            <el-form-item label="分支" required>
              <el-tooltip
                content="选择目标分支，生成的SQL脚本将应用于所选分支"
                placement="right"
                effect="light"
              >
                <el-select v-model="formData.branch" placeholder="请选择分支">
                <el-option
                  v-for="branch in branches"
                  :key="branch.name"
                  :label="branch.name"
                  :value="branch.name"
                >
                  <div style="display: flex; flex-direction: column; gap: 4px;">
                    <span>{{ branch.name }}</span>
                    <span style="font-size: 12px; color: #909399;">{{ branch.description }}</span>
                    <div style="font-size: 12px; color: #909399;">
                      <span>创建人: {{ branch.created_by }}</span>
                      <span style="margin-left: 10px;">创建时间: {{ branch.created_at }}</span>
                    </div>
                  </div>
                </el-option>
              </el-select>
              </el-tooltip>
            </el-form-item>

            <el-form-item>
              <el-tooltip
                content="点击生成SQL脚本，生成的文件将显示在右侧列表中"
                placement="top"
                effect="light"
              >
                <el-button type="primary" @click="generateScript" :loading="generating">
                  <el-icon><DocumentAdd /></el-icon> 生成脚本
                </el-button>
              </el-tooltip>
            </el-form-item>
          </el-form>
          
          <div v-else class="no-permission-message">
            <el-alert
              title="无生成权限"
              type="info"
              description="您当前的角色无法使用SQL生成功能，但可以查看和下载已生成的文件。"
              show-icon
              :closable="false"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="files-card">
          <template #header>
            <div class="card-header">
              <h3><el-icon><Folder /></el-icon> 生成的文件</h3>
              <div class="search-bar">
                <el-input
                  v-model="searchTerm"
                  placeholder="搜索文件"
                  clearable
                  @clear="handleSearch"
                  @input="handleSearch"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                  <template #append>
                    <el-button @click="handleSearch">
                      <el-icon><Search /></el-icon> 搜索
                    </el-button>
                  </template>
                </el-input>
              </div>
            </div>
          </template>

          <el-table :data="files" style="width: 100%">
            <el-table-column prop="fileName" label="文件名" />
            <el-table-column prop="createdAt" label="创建时间" width="180" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="downloadFile(row.fileName)">
                  <el-icon><Download /></el-icon> 下载
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
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElAlert } from 'element-plus'
import apiClient from '../api/config'

interface Branch {
  id: number
  name: string
  description: string
  created_at: string
  created_by: string
}

// 用户角色权限控制
const userRole = computed(() => localStorage.getItem('userRole'))
const canGenerateSQL = computed(() => ['超级管理员', '普通管理员'].includes(userRole.value || ''))

const formRef = ref()
const formData = reactive({
  userStartIndex: 2,
  userMaxIndex: 8000,
  departmentIndex: 0,
  usersPerDepartment: 2500,
  deviceStartIndex: 1,
  deviceMaxIndex: 1,
  branch: ''
})

const rules = reactive({
  userStartIndex: [
    { required: true, message: '请输入用户初始序号', trigger: 'blur' },
    { type: 'number', min: 1, message: '序号必须大于0', trigger: 'blur' }
  ],
  userMaxIndex: [
    { required: true, message: '请输入用户最大序号', trigger: 'blur' },
    { type: 'number', min: 1, message: '序号必须大于0', trigger: 'blur' }
  ],
  departmentIndex: [
    { required: true, message: '请输入当前部门序号', trigger: 'blur' },
    { type: 'number', min: 0, message: '序号必须大于等于0', trigger: 'blur' }
  ],
  usersPerDepartment: [
    { required: true, message: '请输入每个部门用户数', trigger: 'blur' },
    { type: 'number', min: 1, message: '用户数必须大于0', trigger: 'blur' }
  ],
  deviceStartIndex: [
    { required: true, message: '请输入用户初始设备序号', trigger: 'blur' },
    { type: 'number', min: 1, message: '序号必须大于0', trigger: 'blur' }
  ],
  deviceMaxIndex: [
    { required: true, message: '请输入用户最大设备序号', trigger: 'blur' },
    { type: 'number', min: 1, message: '序号必须大于0', trigger: 'blur' }
  ],
  branch: [
    { required: true, message: '请选择分支', trigger: 'change' }
  ]
})

const branches = ref<Branch[]>([])
const generating = ref(false)
interface FileItem {
  fileName: string
  createdAt: string
  downloadUrl: string
}

const files = ref<FileItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchTerm = ref('')

// 获取分支列表
const fetchBranches = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未找到登录凭证，请先登录')
      return
    }
    const response = await apiClient.get('/branches', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    if (response.data && response.data.branches) {
      branches.value = response.data.branches
    } else {
      ElMessage.warning('获取分支列表数据格式异常')
    }
  } catch (error: any) {
    console.error('获取分支列表失败:', error)
    ElMessage.error(error.response?.data?.message || '获取分支列表失败，请检查网络连接')
  }
}

interface FileResponse {
  name: string
  created_at: string
  download_url: string
}

// 获取文件列表
const fetchFiles = async () => {
  try {
    const response = await apiClient.get('/files', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        search_term: searchTerm.value
      },
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    files.value = response.data.files.map((file: FileResponse) => ({
      fileName: file.name,
      createdAt: file.created_at,
      downloadUrl: file.download_url
    }))
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('获取文件列表失败')
  }
}

// 生成脚本
const generateScript = async () => {
  if (!formRef.value) return
  
  // 检查是否选择了分支
  if (!formData.branch) {
    ElMessage.error('请选择分支，这是必选项')
    return
  }
  
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) {
      ElMessage.error('请填写完整的表单信息')
      return
    }
    generating.value = true
    try {
      await apiClient.post(
        '/generate-script',
        formData,
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      )
      ElMessage.success('脚本生成成功')
      fetchFiles()
    } catch (error) {
      ElMessage.error('生成脚本失败')
    } finally {
      generating.value = false
    }
  })
}

// 下载文件
const downloadFile = async (fileName: string) => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未找到登录凭证，请先登录')
      return
    }
    const response = await apiClient.get(`/download/${fileName}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('文件下载成功')
  } catch (error) {
    ElMessage.error('下载文件失败')
  }
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  fetchFiles()
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchFiles()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchFiles()
}

onMounted(() => {
  fetchBranches()
  fetchFiles()
})
</script>

<style scoped>
.sql-generator-container {
  padding: 20px;
  max-width: 2048px;
  margin: 0 auto;
  overflow-x: hidden;
}

.generator-card,
.files-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.search-bar {
  flex: 1;
  max-width: 400px;
  margin-left: auto;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  width: 100%;
  overflow-x: auto;
}

@media (max-width: 768px) {
  .sql-generator-container {
    padding: 10px;
  }

  .card-header h3 {
    width: 100%;
    margin-bottom: 10px;
  }

  .search-bar {
    max-width: 100%;
    margin-bottom: 10px;
  }

  .el-form-item {
    margin-bottom: 15px;
  }

  .el-input-number,
  .el-select {
    width: 100%;
  }
}
</style>