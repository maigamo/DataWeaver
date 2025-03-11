<template>
  <div class="system-config-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2><el-icon><Setting /></el-icon> 系统配置</h2>
        </div>
      </template>

      <el-table :data="configs" style="width: 100%">
        <el-table-column prop="config_key" label="配置项">
          <template #default="{ row }">
            {{ getConfigDisplayName(row.config_key) }}
          </template>
        </el-table-column>
        <el-table-column prop="config_value" label="配置值">
          <template #default="{ row }">
            <el-switch
              v-if="row.config_key === 'enable_download_limit'"
              v-model="row.config_value"
              :active-value="'true'"
              :inactive-value="'false'"
              @change="handleConfigChange(row)"
            />
            <span v-else>{{ row.config_value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" />
        <el-table-column prop="updated_at" label="更新时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import type { SystemConfig } from '@/types'

const userStore = useUserStore()
const configs = ref<SystemConfig[]>([])

// 获取配置项显示名称
const getConfigDisplayName = (key: string) => {
  const displayNames: Record<string, string> = {
    'enable_download_limit': '下载限制功能'
  }
  return displayNames[key] || key
}

// 获取系统配置列表
const fetchConfigs = async () => {
  try {
    const response = await fetch('/api/system-config/configs', {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (!response.ok) throw new Error('获取配置失败')
    const data = await response.json()
    configs.value = data.configs
  } catch (error) {
    ElMessage.error('获取系统配置失败')
    console.error(error)
  }
}

// 更新配置值
const handleConfigChange = async (config: SystemConfig) => {
  try {
    const response = await fetch(`/api/system-config/configs/${config.config_key}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ config_value: config.config_value })
    })
    if (!response.ok) throw new Error('更新配置失败')
    ElMessage.success('配置更新成功')
    await fetchConfigs()
  } catch (error) {
    ElMessage.error('更新配置失败')
    console.error(error)
  }
}

onMounted(() => {
  fetchConfigs()
})
</script>

<style scoped>
.system-config-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>