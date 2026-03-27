<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <h3>CRM 管理系统</h3>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/customers" v-if="hasPermission('customers')">
          <el-icon><User /></el-icon>
          <span>客户管理</span>
        </el-menu-item>
        <el-menu-item index="/contracts" v-if="hasPermission('contracts')">
          <el-icon><Document /></el-icon>
          <span>合同管理</span>
        </el-menu-item>
        <el-menu-item index="/invoices" v-if="hasPermission('invoices')">
          <el-icon><Tickets /></el-icon>
          <span>发票管理</span>
        </el-menu-item>
        <el-menu-item index="/receivables" v-if="hasPermission('receivables')">
          <el-icon><Coin /></el-icon>
          <span>应收款管理</span>
        </el-menu-item>
        <el-sub-menu index="cashflow" v-if="hasPermission('cashflow')">
          <template #title>
            <el-icon><Money /></el-icon>
            <span>现金流管理</span>
          </template>
          <el-menu-item index="/incomes">收入管理</el-menu-item>
          <el-menu-item index="/expenses">支出管理</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/products" v-if="hasPermission('products')">
          <el-icon><Goods /></el-icon>
          <span>产品库存</span>
        </el-menu-item>
        <el-menu-item index="/projects" v-if="hasPermission('projects')">
          <el-icon><Finished /></el-icon>
          <span>项目进度</span>
        </el-menu-item>
        <el-menu-item index="/settings" v-if="userStore.user?.role === 'admin'">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部 Header -->
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ $route.meta.title || '当前页面' }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="userStore.user?.avatar || ''" :icon="userStore.user?.avatar ? undefined : UserFilled" />
              <span class="username">{{ userStore.user?.username || '用户' }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="settings" v-if="userStore.user?.role === 'admin'">系统设置</el-dropdown-item>
                <el-dropdown-item command="users" v-if="userStore.user?.role === 'admin'">用户管理</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区域 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { logout } from '@/api/auth'
import { ElMessageBox } from 'element-plus'
import { UserFilled, DataLine, User, Document, Tickets, Coin, Goods, Finished, Money, Setting } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const hasPermission = (menu) => {
  if (!userStore.user) return false
  if (userStore.user.role === 'admin') return true
  const menuPermissions = userStore.user.menu_permissions || []
  return menuPermissions.includes(menu)
}

const handleCommand = async (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'settings') {
    router.push('/settings')
  } else if (command === 'users') {
    router.push('/users')
  } else if (command === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await logout()
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  overflow-x: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2b3a4b;
}

.logo h3 {
  color: #fff;
  margin: 0;
  font-size: 18px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.username {
  font-size: 14px;
  color: #606266;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
