<script setup lang="ts">
import { RouterView, useRoute, useRouter } from 'vue-router'
import { ref, computed } from 'vue'
import { ElMenu, ElMenuItem, ElDropdown, ElDropdownMenu, ElDropdownItem } from 'element-plus'

interface MenuItem {
  path: string
  label: string
  roles: string[]
}

const activeIndex = ref('1')
const route = useRoute()
const router = useRouter()
const isLoginPage = computed(() => route.name === 'login')
const token = computed(() => localStorage.getItem('token'))
const username = computed(() => localStorage.getItem('username'))
const userRole = computed(() => localStorage.getItem('userRole'))

const menuItems: MenuItem[] = [
  { path: '/sql-generator', label: 'SQL生成器', roles: ['内部用户', '操作员', '普通管理员', '超级管理员'] },
  { path: '/data-query', label: '数据查询', roles: ['内部用户', '超级管理员'] },
  { path: '/resource-center', label: '资源共享中心', roles: ['普通用户', '内部用户', '操作员', '普通管理员', '超级管理员'] },
  { path: '/branch-management', label: '分支管理', roles: ['超级管理员'] },
  { path: '/user-management', label: '用户管理', roles: ['超级管理员'] },
  { path: '/statistics', label: '统计信息', roles: ['超级管理员'] },
  { path: '/system-config', label: '系统配置', roles: ['超级管理员'] }
]

const filteredMenuItems = computed(() => {
  return menuItems.filter(item => item.roles.includes(userRole.value || ''))
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('userRole')
  router.push('/')
}
</script>

<template>
  <div class="app-container">
    <header class="app-header" v-if="!isLoginPage && token">
      <div class="logo-container">
        <img src="/src/assets/logo.svg" class="logo" alt="DataWeaver logo" />
        <h1>DataWeaver</h1>
      </div>
      <el-menu
        :default-active="activeIndex"
        class="main-menu"
        mode="horizontal"
        router
      >
        <el-menu-item v-for="item in filteredMenuItems" :key="item.path" :index="item.path">
          {{ item.label }}
        </el-menu-item>
      </el-menu>
      <div class="user-menu">
        <el-dropdown trigger="click">
          <span class="user-info">
            {{ username }}
            <i class="el-icon-arrow-down"></i>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1440px; /* 添加最大宽度限制 */
  margin: 0 auto; /* 居中显示 */
}

.app-header {
  display: flex;
  align-items: center;
  padding: 0 20px;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  height: 60px;
  width: 100%;
}

.logo-container {
  display: flex;
  align-items: center;
  margin-right: 40px;
}

.logo {
  height: 32px;
  margin-right: 10px;
  will-change: filter;
  transition: filter 300ms;
}

.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}

.logo-container h1 {
  font-size: 1.5em;
  color: #333;
  margin: 0;
}

.main-menu {
  flex: 1;
}

.app-main {
  flex: 1;
  padding: 20px;
  width: 100%;
  max-width: 100%; /* 确保内容不超过容器宽度 */
}

/* 添加媒体查询，适应不同屏幕尺寸 */
@media (max-width: 1440px) {
  .app-container {
    max-width: 100%;
    padding: 0 20px;
  }
}

@media (max-width: 768px) {
  .app-header {
    flex-direction: column;
    height: auto;
    padding: 10px;
  }

  .logo-container {
    margin-right: 0;
    margin-bottom: 10px;
  }

  .main-menu {
    width: 100%;
  }
}

.user-menu {
  margin-left: 20px;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #333;
}

.user-info:hover {
  color: #409EFF;
}
</style>
