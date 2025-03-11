<template>
  <div class="login-container">
    <el-card class="login-card">
      <div class="login-header">
        <h1><span class="text-primary">Data</span> <span class="text-secondary">Weaver</span></h1>
        <h3>欢迎使用</h3>
      </div>

      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            prefix-icon="User"
            placeholder="用户名"
            maxlength="256"
            show-word-limit
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            prefix-icon="Lock"
            type="password"
            placeholder="密码"
            show-password
            maxlength="256"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="login-button">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <el-collapse>
        <el-collapse-item title="💡 使用说明">
          <div class="admin-info">
            <p><el-icon><InfoFilled /></el-icon> 如需申请账号，请联系系统管理员</p>
            <p><el-icon><Service /></el-icon> 使用过程中遇到问题，请及时联系管理员</p>
            <p><el-icon><Message /></el-icon> 管理员邮箱：admin@example.com</p>
            <!-- <p class="tip">温馨提示：首次登录后请及时修改密码</p> -->
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { InfoFilled, Service, Message } from '@element-plus/icons-vue'
import apiClient from '../api/config'
import type { FormInstance } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const loginError = ref('')
const loginFormRef = ref<FormInstance>()

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { max: 256, message: '用户名长度不能超过256个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { max: 256, message: '密码长度不能超过256个字符', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6位', trigger: 'blur' }
  ]
}

// 检查并清理过期的token
const checkTokenExpiration = () => {
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const tokenData = JSON.parse(atob(token.split('.')[1]))
      if (tokenData.exp * 1000 < Date.now()) {
        // Token已过期，清理所有相关数据
        localStorage.removeItem('token')
        localStorage.removeItem('userRole')
        localStorage.removeItem('username')
      }
    } catch (error) {
      // Token格式无效，清理所有相关数据
      localStorage.removeItem('token')
      localStorage.removeItem('userRole')
      localStorage.removeItem('username')
    }
  }
}

// 定期检查token是否过期
let tokenCheckInterval: number
onMounted(() => {
  checkTokenExpiration()
  tokenCheckInterval = window.setInterval(checkTokenExpiration, 5 * 60 * 1000) // 每5分钟检查一次
})

onUnmounted(() => {
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval)
  }
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    loginError.value = ''
    
    try {
      const formData = new URLSearchParams()
      formData.append('username', loginForm.username)
      formData.append('password', loginForm.password)
      
      const response = await apiClient.post('token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      const userResponse = await apiClient.get('/users/me', {
        headers: {
          Authorization: `Bearer ${response.data.access_token}`
        }
      })

      // 保存用户信息和token
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('userRole', userResponse.data.role)
      localStorage.setItem('username', userResponse.data.username)

      ElMessage.success('登录成功')
      // 根据用户角色跳转到相应页面
      const userRole = userResponse.data.role
      if (userRole === '普通管理员') {
        router.push('/resource-center')
      } else {
        router.push('/sql-generator')
      }
    } catch (error: any) {
      let errorMessage = '登录失败，请检查用户名和密码'
      
      // 处理后端返回的验证错误信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        if (detail) {
          // 如果detail不为空，直接显示
          errorMessage = detail
        } else if (Array.isArray(detail)) {
          // 处理数组类型的验证错误
          const errorDetails = detail.map(err => {
            if (err.type === 'string_too_short' && err.loc.includes('password')) {
              return '密码长度不能少于6个字符'
            }
            return err.msg
          })
          errorMessage = errorDetails.join('\n')
        }
      }
      
      loginError.value = errorMessage
      ElMessage.error(errorMessage)
      setTimeout(() => {
        loading.value = false
      }, 2000)
    } finally {
      // 移除这里的 loading.value = false，因为已经在 setTimeout 中设置了
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  max-width: 2048px;
  margin: 0 auto;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 20px;
  margin: 0 15px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  margin-bottom: 10px;
}

.text-primary {
  color: #1E88E5;
}

.text-secondary {
  color: #424242;
}

.login-button {
  width: 100%;
}

.admin-info {
  padding: 15px;
  background-color: #f4f4f5;
  border-radius: 4px;
}

.warning {
  color: #e6a23c;
  margin-top: 10px;
}

.tip {
  color: #409EFF;
  margin-top: 10px;
}
</style>
