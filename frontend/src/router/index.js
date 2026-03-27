import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' },
      },
      {
        path: 'customers',
        name: 'Customers',
        component: () => import('@/views/Customers.vue'),
        meta: { title: '客户管理' },
      },
      {
        path: 'contracts',
        name: 'Contracts',
        component: () => import('@/views/Contracts.vue'),
        meta: { title: '合同管理' },
      },
      {
        path: 'contracts/new',
        name: 'ContractNew',
        component: () => import('@/views/ContractDetail.vue'),
        meta: { title: '新增合同' },
      },
      {
        path: 'contracts/:id',
        name: 'ContractDetail',
        component: () => import('@/views/ContractDetail.vue'),
        meta: { title: '合同详情' },
      },
      {
        path: 'invoices',
        name: 'Invoices',
        component: () => import('@/views/Invoices.vue'),
        meta: { title: '发票管理' },
      },
      {
        path: 'receivables',
        name: 'Receivables',
        component: () => import('@/views/Receivables.vue'),
        meta: { title: '应收款管理' },
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/views/Products.vue'),
        meta: { title: '产品库存' },
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/Projects.vue'),
        meta: { title: '项目进度' },
      },
      {
        path: 'incomes',
        name: 'Incomes',
        component: () => import('@/views/Incomes.vue'),
        meta: { title: '收入管理' },
      },
      {
        path: 'expenses',
        name: 'Expenses',
        component: () => import('@/views/Expenses.vue'),
        meta: { title: '支出管理' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 未登录检查
  if (to.path !== '/login' && !userStore.token) {
    next('/login')
    return
  }

  // 已登录访问登录页，重定向到首页
  if (to.path === '/login' && userStore.token) {
    next('/dashboard')
    return
  }

  // 登录页直接访问
  if (to.path === '/login') {
    next()
    return
  }

  // 检查菜单权限
  const user = userStore.user
  if (user) {
    // 管理员可以访问所有页面
    if (user.role !== 'admin') {
      const menuPermissions = user.menu_permissions || []

      // 定义每个路由需要的权限
      const menuMap = {
        'Dashboard': 'dashboard',
        'Customers': 'customers',
        'Contracts': 'contracts',
        'ContractNew': 'contracts',
        'ContractDetail': 'contracts',
        'Invoices': 'invoices',
        'Receivables': 'receivables',
        'Products': 'products',
        'Projects': 'projects',
        'Incomes': 'cashflow',
        'Expenses': 'cashflow',
        'Profile': 'profile',
        'Users': 'users',
        'Settings': 'settings',
      }

      const requiredMenu = menuMap[to.name]

      // Users 和 Settings 页面需要 admin 角色
      if (to.name === 'Users' || to.name === 'Settings') {
        ElMessage.error('没有权限访问该页面')
        next('/dashboard')
        return
      }

      // Profile 页面所有登录用户可访问
      if (to.name === 'Profile') {
        next()
        return
      }

      // 其他页面检查权限
      if (requiredMenu && !menuPermissions.includes(requiredMenu)) {
        ElMessage.error('没有权限访问该页面')
        next('/dashboard')
        return
      }
    }
  }

  next()
})

export default router
