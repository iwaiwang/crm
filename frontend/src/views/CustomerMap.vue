<template>
  <div class="map-page">
    <div class="page-header">
      <h2>客户分布</h2>
    </div>

    <!-- 过滤栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="分类">
          <el-select v-model="filters.category" placeholder="全部分类" clearable @change="loadData">
            <el-option label="潜在" value="potential" />
            <el-option label="普通" value="normal" />
            <el-option label="VIP" value="vip" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.customer_type" placeholder="全部类型" clearable @change="loadData">
            <el-option label="医院" value="hospital" />
            <el-option label="代理商" value="agent" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <span class="stats-info">
            已标注省份客户：<strong>{{ totalWithProvince }}</strong> 个
            <template v-if="hoveredProvince">
              | {{ hoveredProvince }}：<strong>{{ hoveredCount || 0 }}</strong> 个
            </template>
          </span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 地图 + 侧栏 -->
    <el-card class="map-card">
      <div v-if="loading" class="map-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      <div v-show="!loading" class="map-body">
        <div ref="mapContainer" class="map-container"></div>
        <div v-if="selectedProvince" class="province-panel">
          <div class="panel-header">
            <h3>{{ selectedProvince }}</h3>
            <span class="panel-count">{{ selectedCustomers.length }} 个客户</span>
            <el-button link @click="selectedProvince = ''; selectedCustomers = []; clearSelectedPath()">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
          <div class="panel-list" v-loading="panelLoading">
            <div v-for="c in selectedCustomers" :key="c.id" class="customer-item">
              <div class="customer-name">{{ c.name }}</div>
              <div class="customer-meta">
                <el-tag size="small" :type="getCategoryType(c.category)">{{ getCategoryLabel(c.category) }}</el-tag>
                <el-tag size="small" v-if="c.customer_type" :type="c.customer_type === 'hospital' ? 'primary' : ''">
                  {{ c.customer_type === 'hospital' ? '医院' : '代理商' }}
                </el-tag>
              </div>
              <div v-if="c.contacts && c.contacts.length" class="customer-contact">
                <span v-for="(ct, i) in c.contacts" :key="ct.id">
                  {{ ct.name }}{{ ct.phone ? ' ' + ct.phone : '' }}{{ i < c.contacts.length - 1 ? ' | ' : '' }}
                </span>
              </div>
            </div>
            <div v-if="!panelLoading && selectedCustomers.length === 0" class="empty-hint">该省份暂无客户</div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { Loading, Close } from '@element-plus/icons-vue'
import request from '@/api/request'
import { getCustomers } from '@/api/customer'

const mapContainer = ref(null)
const loading = ref(true)
const totalWithProvince = ref(0)
const hoveredProvince = ref('')
const hoveredCount = ref(0)
const selectedProvince = ref('')
const selectedCustomers = ref([])
const panelLoading = ref(false)

const filters = reactive({
  category: '',
  customer_type: '',
})

const enToCh = {
  'Anhui': '安徽', 'Beijing': '北京', 'Chongqing': '重庆', 'Fujian': '福建',
  'Guangdong': '广东', 'Gansu': '甘肃', 'Guangxi Zhuang': '广西', 'Guizhou': '贵州',
  'Hainan': '海南', 'Hebei': '河北', 'Henan': '河南', 'Hong Kong': '香港',
  'Heilongjiang': '黑龙江', 'Hunan': '湖南', 'Hubei': '湖北', 'Jilin': '吉林',
  'Jiangsu': '江苏', 'Jiangxi': '江西', 'Liaoning': '辽宁', 'Macau': '澳门',
  'Nei Mongol': '内蒙古', 'Ningxia Hui': '宁夏', 'Quinghai': '青海', 'Shaanxi': '陕西',
  'Sichuan': '四川', 'Shandong': '山东', 'Shanghai': '上海', 'Shanxi': '山西',
  'Tianjin': '天津', 'Taiwan': '台湾', 'Xinjiang Uygur': '新疆', 'Xizang (Tibet) ': '西藏',
  'Yunnan': '云南', 'Zhejiang': '浙江',
}

let mapSvg = null
let distributionData = {}
let selectedPath = null

const HIGHLIGHT_COLOR = '#fff3cd'

function getColor(count, max) {
  if (!count || max === 0) return '#e8e8e8'
  const ratio = count / max
  if (ratio > 0.8) return '#2376b5'
  if (ratio > 0.5) return '#4393c3'
  if (ratio > 0.2) return '#92c5de'
  return '#d1e5f0'
}

async function loadData() {
  loading.value = true
  try {
    const params = {}
    if (filters.category) params.category = filters.category
    if (filters.customer_type) params.customer_type = filters.customer_type
    const res = await request.get('/customers/distribution', { params })
    distributionData = res.distribution || {}
    totalWithProvince.value = res.total_with_province || 0
    hoveredProvince.value = ''
    hoveredCount.value = 0
    selectedProvince.value = ''
    selectedCustomers.value = []
    selectedPath = null
    await nextTick()
    colorMap()
  } catch (e) {
    console.error('Failed to load distribution data:', e)
  } finally {
    loading.value = false
  }
}

async function loadSvg() {
  const res = await fetch('/china-map.svg')
  const svgText = await res.text()
  if (mapContainer.value) {
    mapContainer.value.innerHTML = svgText
    mapSvg = mapContainer.value.querySelector('svg')
    if (mapSvg) {
      mapSvg.style.width = '100%'
      mapSvg.style.height = '100%'
      setupProvinceEvents()
    }
  }
}

function colorMap() {
  if (!mapSvg) return
  const counts = Object.values(distributionData)
  const max = counts.length > 0 ? Math.max(...counts) : 0
  const paths = mapSvg.querySelectorAll('path[title]')
  paths.forEach(path => {
    const en = path.getAttribute('title')
    const ch = enToCh[en] || en
    const count = distributionData[ch] || 0
    const color = getColor(count, max)
    path.setAttribute('fill', color)
    path.style.setProperty('fill', color, 'important')
    path.removeAttribute('class')
  })
  // Re-highlight selected path if any
  if (selectedPath) {
    selectedPath.style.setProperty('fill', HIGHLIGHT_COLOR, 'important')
    selectedPath.setAttribute('fill', HIGHLIGHT_COLOR)
  }
}

function clearSelectedPath() {
  if (selectedPath) {
    const en = selectedPath.getAttribute('title')
    const ch = enToCh[en] || en
    const count = distributionData[ch] || 0
    const counts = Object.values(distributionData)
    const max = counts.length > 0 ? Math.max(...counts) : 0
    const color = getColor(count, max)
    selectedPath.setAttribute('fill', color)
    selectedPath.style.setProperty('fill', color, 'important')
    selectedPath = null
  }
}

async function selectProvince(path, ch) {
  // Clear previous selection
  clearSelectedPath()
  // Set new selection
  selectedPath = path
  path.style.setProperty('fill', HIGHLIGHT_COLOR, 'important')
  path.setAttribute('fill', HIGHLIGHT_COLOR)
  selectedProvince.value = ch
  panelLoading.value = true
  try {
    const params = { province: ch, page_size: 100 }
    if (filters.category) params.category = filters.category
    if (filters.customer_type) params.customer_type = filters.customer_type
    const res = await getCustomers(params)
    selectedCustomers.value = res.items || []
  } catch (e) {
    console.error('Failed to load customers for province:', e)
    selectedCustomers.value = []
  } finally {
    panelLoading.value = false
  }
}

function setupProvinceEvents() {
  if (!mapSvg) return
  const svgStyle = mapSvg.querySelector('style')
  if (svgStyle) svgStyle.remove()
  const paths = mapSvg.querySelectorAll('path[title]')
  mapSvg.addEventListener('click', () => {
    requestAnimationFrame(() => colorMap())
  })
  paths.forEach(path => {
    let originalFill = ''

    path.addEventListener('mouseenter', () => {
      const en = path.getAttribute('title')
      const ch = enToCh[en] || en
      hoveredProvince.value = ch
      hoveredCount.value = distributionData[ch] || 0
      if (path !== selectedPath) {
        originalFill = path.getAttribute('fill')
        path.style.setProperty('fill', HIGHLIGHT_COLOR, 'important')
        path.setAttribute('fill', HIGHLIGHT_COLOR)
      }
    })
    path.addEventListener('mouseleave', () => {
      hoveredProvince.value = ''
      hoveredCount.value = 0
      if (path !== selectedPath && originalFill) {
        path.setAttribute('fill', originalFill)
        path.style.setProperty('fill', originalFill, 'important')
      }
    })
    path.addEventListener('click', (e) => {
      e.stopPropagation()
      const en = path.getAttribute('title')
      const ch = enToCh[en] || en
      selectProvince(path, ch)
    })
    path.style.transition = 'fill 0.2s'
    path.style.outline = 'none'
    path.setAttribute('tabindex', '-1')
  })
}

function getCategoryType(cat) {
  const map = { potential: 'info', normal: 'primary', vip: 'warning' }
  return map[cat] || 'info'
}

function getCategoryLabel(cat) {
  const map = { potential: '潜在', normal: '普通', vip: 'VIP' }
  return map[cat] || cat
}

onMounted(async () => {
  await loadSvg()
  await loadData()
})
</script>

<style scoped>
.map-page {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 { margin: 0; }

.filter-card {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.stats-info {
  font-size: 14px;
  color: #606266;
}

.map-card {
  flex: 1;
  min-height: 550px;
  display: flex;
  flex-direction: column;
}

.map-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  padding: 0;
  overflow: hidden;
}

.map-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.map-container {
  flex: 1;
  min-width: 0;
  user-select: none;
  -webkit-user-select: none;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.map-container :deep(svg) {
  max-width: 100%;
  max-height: 100%;
}

.map-container :deep(path) {
  outline: none;
  -webkit-tap-highlight-color: transparent;
  cursor: pointer;
  transition: fill 0.2s;
}

.map-container :deep(path:focus),
.map-container :deep(path:active),
.map-container :deep(path:focus-visible) {
  outline: none;
}

.province-panel {
  width: 280px;
  flex-shrink: 0;
  border-left: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  flex: 1;
}

.panel-count {
  font-size: 13px;
  color: #909399;
}

.panel-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.customer-item {
  background: #fff;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
}

.customer-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
}

.customer-meta {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}

.customer-contact {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.empty-hint {
  text-align: center;
  color: #c0c4cc;
  padding: 32px 0;
  font-size: 14px;
}

.map-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  color: #909399;
  height: 100%;
}
</style>
