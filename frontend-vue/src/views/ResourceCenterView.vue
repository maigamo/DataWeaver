<template>
  <div class="resource-center-container">
    <div class="page-header">
      <h1>资源共享中心</h1>
      <div class="header-actions">
        <el-input
          v-model="searchTerm"
          placeholder="搜索资源名称"
          clearable
          @keyup.enter="handleSearch"
          class="search-input"
        >
          <template #append>
            <el-button @click="handleSearch">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
        
        <el-button v-if="isAdmin" type="primary" @click="openUploadDialog">
          <el-icon><Upload /></el-icon> 上传资源
        </el-button>

        <el-button v-if="isSuperAdmin" type="warning" @click="handleResetDownloadStatus">
          <el-icon><RefreshRight /></el-icon> 重置下载状态
        </el-button>
      </div>
    </div>
    
    <el-card class="resource-list-card">
      <el-table
        :data="resources"
        style="width: 100%"
        v-loading="loading"
        border
      >
        <el-table-column prop="resource_name" label="资源名称" min-width="300">
          <template #default="{row}">
            <el-tooltip :content="row.resource_name" placement="top" :show-after="500">
              <div class="resource-name-container">
                <span class="resource-name">{{ row.resource_name }}</span>
                <el-tag size="small" type="info" style="margin-left: 8px">
                  {{ new Date(row.created_at).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }) }}
                </el-tag>
              </div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="上传者" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="文件大小" width="120">
          <template #default="{row}">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="download_count" label="下载次数" width="100" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{row}">
            <el-button
              size="small"
              type="primary"
              :loading="downloadingResourceId === row.id"
              :disabled="downloadingResourceId !== null"
              @click="downloadResource(row)"
            >
              <el-icon><Download /></el-icon> 下载
            </el-button>
            
            <el-button
              v-if="isSuperAdmin"
              size="small"
              type="danger"
              @click="deleteResource(row)"
            >
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
    
    <!-- 上传资源对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传资源"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="资源名称">
          <el-input 
            v-model="resourceName" 
            placeholder="请输入资源名称（12-256个字符）" 
            :maxlength="256"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="上传文件">
          <el-upload
            multiple
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleRemoveFile"
            :before-upload="beforeUpload"
            :file-list="fileList"
          >
            <el-button type="primary">
              <el-icon><Plus /></el-icon> 添加文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                最多上传5个文件，总大小不超过500MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <!-- 显示磁盘空间信息 -->
        <el-form-item label="磁盘空间">
          <el-card class="disk-space-card" shadow="hover">
            <template #header>
              <div class="disk-space-header">
                <el-icon><Disk /></el-icon>
                <span>存储空间使用情况</span>
                <el-tooltip
                  content="红色部分表示已用空间，蓝色部分表示可用空间"
                  placement="top"
                >
                  <el-icon class="info-icon"><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
            </template>
            <el-progress 
              :percentage="diskSpace ? Math.round((diskSpace.used / diskSpace.total) * 100) : 0" 
              :format="() => ''" 
              :status="''"
              :stroke-width="20"
              class="disk-space-progress"
              :color="'#F56C6C'"
              :background-color="'#409EFF'"
            />
            <div class="disk-space-info" v-if="diskSpace">
              <el-row :gutter="20">
                <el-col :span="8">
                  <div class="space-item total">
                    <div class="label">
                      <el-icon><Storage /></el-icon>
                      总空间
                    </div>
                    <div class="value">{{ formatFileSize(diskSpace.total) }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="space-item used">
                    <div class="label">
                      <el-icon><WarningFilled /></el-icon>
                      已用空间
                    </div>
                    <div class="value">{{ formatFileSize(diskSpace.used) }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="space-item free">
                    <div class="label">
                      <el-icon><Check /></el-icon>
                      可用空间
                    </div>
                    <div class="value">{{ formatFileSize(diskSpace.free) }}</div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-card>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="uploadLoading" @click="handleUpload">
            上传
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshRight } from '@element-plus/icons-vue'
import apiClient from '../api/config'

// 定义API响应类型
interface Resource {
  id: number
  resource_name: string
  creator_name: string
  created_at: string
  file_size: number
  download_count: number
}

interface ResourceResponse {
  resources: Resource[]
  total: number
  disk_space?: {
    used: number
    total: number
    free: number
    used_gb: number
    total_gb: number
  }
}

interface DownloadStatusResponse {
  status: 'downloading' | 'completed' | 'failed'
  error_message?: string
  can_retry?: boolean
}

// 资源列表数据
const resources = ref<Resource[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchTerm = ref('')

// 上传相关
const uploadDialogVisible = ref(false)
const resourceName = ref('')
const fileList = ref<UploadFile[]>([])
const uploadLoading = ref(false)
const diskSpace = ref<ResourceResponse['disk_space']>(undefined)

// 用户角色
const userRole = ref(localStorage.getItem('userRole'))
const isAdmin = computed(() => ['超级管理员', '普通管理员'].includes(userRole.value || ''))
const isSuperAdmin = computed(() => userRole.value === '超级管理员')

// 下载状态
const downloadingResourceId = ref<number | null>(null)
const checkDownloadInterval = ref<number | null>(null)

// 获取资源列表
const fetchResources = async () => {
  loading.value = true
  try {
    const response = await apiClient.get<ResourceResponse>('/resource-center/resources', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        search_term: searchTerm.value
      }
    })
    resources.value = response.data.resources
    total.value = response.data.total
  } catch (error) {
    console.error('获取资源列表失败:', error)
    ElMessage.error('获取资源列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索资源
const handleSearch = () => {
  currentPage.value = 1
  fetchResources()
}

// 分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchResources()
}

// 打开上传对话框
const openUploadDialog = async () => {
  uploadDialogVisible.value = true
  resourceName.value = ''
  fileList.value = []
  
  // 获取磁盘空间信息
  try {
    const response = await apiClient.get('/resource-center/disk-space')
    if (response.data) {
      diskSpace.value = response.data
    } else {
      console.error('未获取到磁盘空间信息')
      ElMessage.warning('未能获取磁盘空间信息')
    }
  } catch (error) {
    console.error('获取磁盘空间信息失败:', error)
    ElMessage.error('获取磁盘空间信息失败')
  }
}

interface UploadFile {
  name: string
  size: number
  uid: string
  raw?: File
}

// 文件上传前验证
const beforeUpload = (file: File) => {
  // 检查文件数量
  if (fileList.value.length >= 5) {
    ElMessage.warning('最多只能上传5个文件')
    return false
  }
  
  // 检查文件大小
  const totalSize = fileList.value.reduce((sum, f) => sum + f.size, 0) + file.size
  if (totalSize > 500 * 1024 * 1024) { // 500MB
    ElMessage.warning('上传文件总大小不能超过500MB')
    return false
  }
  
  // 检查文件名是否重复
  const existingFile = fileList.value.find(f => f.name === file.name)
  if (existingFile) {
    ElMessage.warning(`文件 ${file.name} 已经添加，不能重复上传`)
    return false
  }
  
  return true
}

// 文件列表变化
const handleFileChange = (_file: UploadFile, uploadFiles: UploadFile[]) => {
  fileList.value = uploadFiles
}

// 移除文件
const handleRemoveFile = (file: UploadFile) => {
  fileList.value = fileList.value.filter(f => f.uid !== file.uid)
}

// 提交上传
const handleUpload = async () => {
  // 验证资源名称
  if (!resourceName.value || resourceName.value.length < 12 || resourceName.value.length > 256) {
    ElMessage.warning('资源名称长度必须在12到256个字符之间')
    return
  }
  
  // 验证是否包含非法字符
  if (/[<>:"/\\|?*]/.test(resourceName.value)) {
    ElMessage.warning('资源名称包含非法字符')
    return
  }
  
  // 验证文件列表
  if (fileList.value.length === 0) {
    ElMessage.warning('请至少上传一个文件')
    return
  }

  // 再次验证文件总大小
  const totalSize = fileList.value.reduce((sum, file) => sum + file.size, 0)
  if (totalSize > 500 * 1024 * 1024) { // 500MB
    ElMessage.warning('上传文件总大小不能超过500MB')
    return
  }
  
  uploadLoading.value = true
  
  try {
    const formData = new FormData()
    formData.append('resource_name', resourceName.value)
    
    fileList.value.forEach(file => {
      if (file.raw instanceof File) {
        formData.append('files', file.raw)
      }
    })
    
    await apiClient.post('/resource-center/resources', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    ElMessage.success('资源上传成功')
    uploadDialogVisible.value = false
    fetchResources()
  } catch (error: any) {
    console.error('上传资源失败:', error)
    ElMessage.error(error.response?.data?.detail || '上传资源失败')
  } finally {
    uploadLoading.value = false
  }
}

// 下载资源
const downloadResource = async (resource: Resource) => {
  try {
    // 获取认证令牌
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('未登录或会话已过期')
      return
    }
    
    // 检查是否已有下载任务
    try {
      const statusCheck = await apiClient.get<DownloadStatusResponse>(`/resource-center/resources/download-status`)
      if (statusCheck.data.status === 'downloading') {
        ElMessage.warning('您有正在进行的下载任务，请等待完成后再下载其他文件')
        return
      }
    } catch (error) {
      // 如果检查失败，继续尝试下载
      console.error('检查下载状态失败:', error)
    }
    
    // 创建下载链接并添加认证头
    const downloadUrl = `${apiClient.defaults.baseURL}/resource-center/resources/${resource.id}/download`
    const response = await fetch(downloadUrl, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error(`下载失败: ${response.status} ${response.statusText}`)
    }
    
    // 设置下载状态
    downloadingResourceId.value = resource.id
    
    // 开始检查下载状态
    checkDownloadInterval.value = window.setInterval(() => {
      checkDownloadStatus(resource.id)
    }, 2000) // 每2秒检查一次
    
    // 获取文件名
    const contentDisposition = response.headers.get('content-disposition')
    let filename = `${resource.resource_name}.zip`
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/)
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1]
      }
    }
    
    // 下载文件
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    // 更新下载次数
    fetchResources()
  } catch (error: any) {
    console.error('下载资源失败:', error)
    ElMessage.error(error.message || '下载资源失败')
  } finally {
    // 清除下载状态和定时器
    if (checkDownloadInterval.value) {
      clearInterval(checkDownloadInterval.value)
      checkDownloadInterval.value = null
    }
    downloadingResourceId.value = null
  }
}

// 重置下载状态
const handleResetDownloadStatus = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有下载状态吗？这将清除所有卡住的下载任务。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await apiClient.post('/resource-center/resources/reset-download-status')
    ElMessage.success('下载状态已重置')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('重置下载状态失败:', error)
      ElMessage.error('重置下载状态失败')
    }
  }
}

// 检查下载状态
const checkDownloadStatus = async (resourceId: number) => {
  try {
    const response = await apiClient.get<DownloadStatusResponse>(`/resource-center/resources/${resourceId}/download-status`)
    const status = response.data.status
    
    if (status === 'completed') {
      // 下载完成，清除状态
      if (checkDownloadInterval.value) {
        clearInterval(checkDownloadInterval.value)
        checkDownloadInterval.value = null
      }
      downloadingResourceId.value = null
    } else if (status === 'failed') {
      // 下载失败
      if (checkDownloadInterval.value) {
        clearInterval(checkDownloadInterval.value)
        checkDownloadInterval.value = null
      }
      downloadingResourceId.value = null
      
      if (response.data.error_message) {
        ElMessage.error(response.data.error_message)
      } else {
        ElMessage.error('下载失败')
      }
      
      // 如果可以重试
      if (response.data.can_retry) {
        ElMessageBox.confirm(
          '下载失败，是否重试？',
          '下载提示',
          {
            confirmButtonText: '重试',
            cancelButtonText: '取消',
            type: 'warning'
          }
        ).then(() => {
          // 重新下载
          const resource = resources.value.find(r => r.id === resourceId)
          if (resource) {
            downloadResource(resource)
          }
        }).catch(() => {
          // 取消重试
        })
      }
    }
    // 如果状态是downloading，继续等待
  } catch (error) {
    console.error('检查下载状态失败:', error)
    // 出错时也清除状态
    // 页面卸载时清理下载状态
    onUnmounted(() => {
      // 如果有正在进行的下载任务，通知后端取消下载
      if (downloadingResourceId.value) {
        // 发送取消下载的请求
        apiClient.post(`/resource-center/resources/${downloadingResourceId.value}/cancel-download`)
          .catch(error => {
            console.error('取消下载失败:', error)
          })
      }
      
      // 清理前端状态
      if (checkDownloadInterval.value) {
        clearInterval(checkDownloadInterval.value)
        checkDownloadInterval.value = null
      }
      downloadingResourceId.value = null
    })

    onMounted(() => {
      fetchResources()
    })
  }
}

// 删除资源
const deleteResource = (resource: Resource) => {
  ElMessageBox.confirm(
    `确定要删除资源 "${resource.resource_name}" 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await apiClient.delete(`/resource-center/resources/${resource.id}`)
      ElMessage.success('资源删除成功')
      fetchResources()
    } catch (error) {
      console.error('删除资源失败:', error)
      ElMessage.error('删除资源失败')
    }
  }).catch(() => {
    // 取消删除
  })
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 页面加载时获取资源列表
onMounted(() => {
  fetchResources()
})
</script>

<style scoped>
.resource-center-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-input {
  width: 300px;
}

.resource-list-card {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 磁盘空间显示样式 */
.disk-space-card {
  margin-top: 10px;
}

.disk-space-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-icon {
  margin-left: auto;
  color: #909399;
  cursor: help;
}

.disk-space-progress {
  margin: 15px 0;
}

.disk-space-info {
  margin-top: 15px;
}

.space-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  border-radius: 4px;
  transition: all 0.3s;
}

.space-item:hover {
  background-color: #f5f7fa;
}

.space-item .label {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
  margin-bottom: 5px;
}

.space-item .value {
  font-size: 16px;
  font-weight: bold;
}

.space-item.total .value {
  color: #303133;
}

.space-item.used .value {
  color: #F56C6C;
}

.space-item.free .value {
  color: #409EFF;
}

.resource-name-container {
  display: flex;
  align-items: center;
}

.resource-name {
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>