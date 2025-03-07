<template>
  <div class="data-query-container">
    <el-card class="filter-card">
      <template #header>
        <div class="card-header">
          <h2><el-icon><DataLine /></el-icon> 数据查询</h2>
        </div>
      </template>
      <div class="filter-section">
        <el-form :inline="true" :model="queryParams" class="query-form">
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="queryParams.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item label="用户">
            <el-input
              v-model="queryParams.username"
              placeholder="输入用户名进行模糊查询"
              clearable
            />
          </el-form-item>
          <el-form-item label="操作类型">
            <el-select v-model="queryParams.operationType" placeholder="选择操作类型">
              <el-option label="全部" value="" />
              <el-option label="登录" value="login" />
              <el-option label="下载文件" value="download" />
              <el-option label="生成SQL" value="generate" />
              <el-option label="上传文件" value="upload" />
              <el-option label="系统配置" value="config" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleQuery">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button @click="resetQuery">
              <el-icon><RefreshRight /></el-icon> 重置
            </el-button>
            <el-button type="success" @click="exportData">
              <el-icon><Download /></el-icon> 导出数据
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card class="table-card">
      <el-table
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="operation_type" label="操作类型" width="120" />
        <el-table-column prop="operation_time" label="操作时间" width="180" />
        <el-table-column prop="username" label="操作用户" width="120" />
        <el-table-column prop="file_name" label="操作描述" />
        <el-table-column label="状态" width="100">
          <template #default="_">
            <el-tag type="success">成功</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DataLine, Search, RefreshRight, Download } from '@element-plus/icons-vue'
import type { DateModelType } from 'element-plus'
import apiClient from '../api/config'

// 用户接口定义
interface User {
  id: number | string
  name: string
}

// 查询参数
const queryParams = reactive({
  dateRange: [] as DateModelType[],
  username: '',
  operationType: '',
  userId: ''
})

// 表格数据
const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const userList = ref<User[]>([])  // 添加User类型注解

// 获取用户列表
const fetchUserList = async () => {
  try {
    const { data } = await apiClient.get<User[]>('/users')  // 添加响应类型注解
    userList.value = data
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  }
}

// 查询参数接口定义
interface QueryParams {
  page: number
  page_size: number
  start_date?: string
  end_date?: string
  user_id?: string | number
  username?: string
  operation_type?: string
}

// 查询数据
const handleQuery = async () => {
  loading.value = true
  try {
    const params: QueryParams = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    // 添加日期范围参数
    if (queryParams.dateRange && queryParams.dateRange.length === 2) {
      // 确保日期值以字符串形式传递
      params.start_date = String(queryParams.dateRange[0])
      params.end_date = String(queryParams.dateRange[1])
    }
    
    // 添加用户ID参数
    if (queryParams.userId) {
      params.user_id = queryParams.userId
    }
    
    // 添加用户名参数
    if (queryParams.username) {
      params.username = queryParams.username
    }

    // 添加操作类型参数
    if (queryParams.operationType) {
      params.operation_type = queryParams.operationType
    }
    
    // 通过GET请求获取数据
    const { data } = await apiClient.get('/api/operation-logs', { params })
    tableData.value = data.logs || []
    total.value = data.total || 0
  } catch (error) {
    ElMessage.error('查询数据失败')
    console.error('查询失败:', error)
  } finally {
    loading.value = false
  }
}

// 重置查询
const resetQuery = () => {
  queryParams.dateRange = []
  queryParams.username = ''
  queryParams.operationType = ''
  handleQuery()
}

// 导出数据
const exportData = async () => {
  try {
    const formData = new FormData()
    formData.append('export_type', 'operation_logs')
    formData.append('page_size', '1000')
    formData.append('compression_level', '9')
    formData.append('split_size', '100')  // 添加分卷大小参数，设置为100MB
    if (queryParams.dateRange && queryParams.dateRange.length === 2) {
      formData.append('start_date', String(queryParams.dateRange[0]))
      formData.append('end_date', String(queryParams.dateRange[1]))
    }
    interface ExportResponse {
      download_url: string
    }
    const response = await apiClient.post<ExportResponse>('/api/operations/export', formData)
    
    // 检查响应中是否包含数据和下载URL
    if (response.data.download_url) {
      // 获取文件名（从URL中提取）
      const urlParts = response.data.download_url.split('/')
      const filename = urlParts[urlParts.length - 1]
      
      // 创建下载链接
      const downloadLink = document.createElement('a')
      downloadLink.href = response.data.download_url
      downloadLink.download = filename
      document.body.appendChild(downloadLink)
      downloadLink.click()
      document.body.removeChild(downloadLink)
      
      // 显示成功消息
      ElMessage.success('数据导出成功')
    } else {
      ElMessage.error('导出数据失败：未获取到下载链接')
    }
  } catch (error) {
    console.error('导出数据失败:', error)
    ElMessage.error('导出数据失败')
  }
}

// 处理分页
const handleSizeChange = (val: number) => {
  pageSize.value = val
  handleQuery()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  handleQuery()
}

onMounted(() => {
  fetchUserList()
  handleQuery()
})
</script>

<style scoped>
.data-query-container {
  padding: 20px;
  max-width: 2048px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-section {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.query-form {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.query-form .el-form-item {
  margin-bottom: 10px;
  margin-right: 0;
}

.query-form .el-select {
  width: 160px;
}

.table-card {
  margin-top: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>