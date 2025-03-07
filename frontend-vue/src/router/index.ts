import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/sql-generator',
      name: 'sqlGenerator',
      component: () => import('../views/SQLGeneratorView.vue'),
      meta: { requiresAuth: true, roles: ['内部用户', '操作员', '普通管理员', '超级管理员'] }
    },
    {
      path: '/user-management',
      name: 'userManagement',
      component: () => import('../views/UserManagementView.vue'),
      meta: { requiresAuth: true, roles: ['超级管理员'] }
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: () => import('../views/StatisticsView.vue'),
      meta: { requiresAuth: true, roles: ['超级管理员'] }
    },
    {
      path: '/branch-management',
      name: 'branchManagement',
      component: () => import('../views/BranchManagementView.vue'),
      meta: { requiresAuth: true, roles: ['超级管理员'] }
    },
    {
      path: '/data-query',
      name: 'dataQuery',
      component: () => import('../views/DataQueryView.vue'),
      meta: { requiresAuth: true, roles: ['内部用户', '超级管理员'] }
    },
    {
      path: '/resource-center',
      name: 'resourceCenter',
      component: () => import('../views/ResourceCenterView.vue'),
      meta: { requiresAuth: true, roles: ['内部用户', '操作员', '普通管理员', '超级管理员', '普通用户'] }
    },
    {
      path: '/system-config',
      name: 'systemConfig',
      component: () => import('../views/SystemConfigView.vue'),
      meta: { requiresAuth: true, roles: ['超级管理员'] }
    }
  ]
})

// 导航守卫
router.beforeEach((to, _, next) => {
  // 如果是登录页面，直接放行，不检查登录状态
  if (to.path === '/login') {
    next()
    return
  }

  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')

  if (to.meta.requiresAuth && !token) {
    next({ name: 'login' })
  } else if (to.meta.roles && Array.isArray(to.meta.roles) && !to.meta.roles.includes(userRole ?? '')) {
    next({ name: 'resourceCenter' })
  } else {
    next()
  }
})

export default router