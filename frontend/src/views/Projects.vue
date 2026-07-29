<template>
  <div class="pipeline-page">
    <!-- Header -->
    <div class="page-header">
      <h2>项目进度管理</h2>
      <div class="header-right">
        <el-input v-model="searchForm.search" placeholder="搜索项目名称、客户..." clearable style="width:260px" @keyup.enter="handleSearch" />
        <el-button @click="handleReset">重置</el-button>
        <el-button type="primary" @click="showQuickCreate = true">+ 快速创建</el-button>
      </div>
    </div>

    <!-- Funnel Stats (clickable) -->
    <div class="funnel-section">
      <div class="funnel-title">销售漏斗</div>
      <div class="funnel-row">
        <div class="funnel-stage" v-for="s in funnelData" :key="s.status"
          :class="{ active: activeStage === s.status }"
          @click="activeStage = s.status">
          <div class="funnel-label">{{ s.label }}</div>
          <div class="funnel-bar-wrap">
            <div class="funnel-bar" :style="{ height: funnelHeight(s.total_amount) + 'px', background: funnelColor(s.status) }" />
          </div>
          <div class="funnel-amount">¥ {{ formatAmount(s.total_amount) }}</div>
          <div class="funnel-count">{{ s.count }} 个项目</div>
        </div>
      </div>
    </div>

    <!-- Card Grid -->
    <div class="card-grid" v-loading="loading">
      <div class="card" v-for="p in activeProjects" :key="p.id"
        :class="{ warning: isStale(p), lost: p.status === 'lost' }"
        @click="openDetail(p)">
        <div class="card-body">
          <div class="card-header">
            <span class="card-title">{{ p.name }}</span>
            <span class="card-probability">{{ p.probability || 0 }}%</span>
          </div>
          <div class="card-customer">🏥 {{ p.customer_name }}</div>
          <div class="card-meta">
            <span class="card-amount">¥ {{ formatAmount(p.budget_amount) }}</span>
            <span v-if="p.competitor" class="card-competitor">竞品: {{ p.competitor }}</span>
          </div>
          <div class="card-footer">
            <div class="card-owner"><span class="card-avatar">{{ (p.manager || '?')[0] }}</span>{{ p.manager || '-' }}</div>
            <div class="card-date">预计: {{ p.expected_sign_date || '-' }}</div>
            <div class="card-warning-tag" v-if="isStale(p)">⚠ {{ daysSinceFollowup(p) }}天</div>
          </div>
        </div>
        <div class="card-actions" @click.stop>
          <el-select v-model="p.status" size="small" @change="(val) => handleStageChange(p, val)" style="width:100%">
            <el-option v-for="s in statusList" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </div>
      </div>
      <el-empty v-if="activeProjects.length === 0" description="暂无项目" />
    </div>

    <!-- Quick Create Modal -->
    <el-dialog v-model="showQuickCreate" title="快速创建项目" width="440px" :close-on-click-modal="false">
      <el-form :model="quickForm" :rules="quickRules" ref="quickFormRef" label-width="80px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="quickForm.name" placeholder="例如：XX医院病案无纸化项目" />
        </el-form-item>
        <el-form-item label="客户" prop="customer_id">
          <el-select v-model="quickForm.customer_id" placeholder="请选择客户" style="width:100%">
            <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="预算金额">
          <el-input-number v-model="quickForm.budget_amount" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="quickForm.manager" placeholder="负责人姓名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showQuickCreate = false">取消</el-button>
        <el-button type="primary" @click="handleQuickCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- Detail Panel -->
    <el-drawer v-model="showDetail" :title="detailProject?.name" size="560px" direction="rtl">
      <template v-if="detailProject">
        <div class="panel-section">
          <div class="panel-title">基本信息</div>
          <div class="info-grid">
            <div class="info-item"><label>客户</label><div class="val">{{ detailProject.customer_name }}</div></div>
            <div class="info-item"><label>负责人</label><div class="val">{{ detailProject.manager }}</div></div>
            <div class="info-item"><label>当前阶段</label><div class="val"><el-tag :type="getStatusType(detailProject.status)" size="small">{{ getStatusLabel(detailProject.status) }}</el-tag></div></div>
            <div class="info-item"><label>中标概率</label><div class="val">{{ detailProject.probability || 0 }}%</div></div>
            <div class="info-item"><label>预算金额</label><div class="val" style="color:#409EFF;font-weight:600">¥ {{ formatAmount(detailProject.budget_amount) }}</div></div>
            <div class="info-item"><label>预计签单</label><div class="val">{{ detailProject.expected_sign_date || '-' }}</div></div>
            <div class="info-item"><label>竞品</label><div class="val" style="color:#E6A23C">{{ detailProject.competitor || '-' }}</div></div>
            <div class="info-item"><label>开始日期</label><div class="val">{{ detailProject.start_date || '-' }}</div></div>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-title">编辑信息</div>
          <el-form :model="editForm" label-width="80px" size="small">
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="阶段">
                  <el-select v-model="editForm.status" style="width:100%" @change="handleSaveEdit">
                    <el-option v-for="s in statusList" :key="s.value" :label="s.label" :value="s.value" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="中标概率">
                  <el-input-number v-model="editForm.probability" :min="0" :max="100" style="width:100%" @change="handleSaveEdit" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="预算金额">
                  <el-input-number v-model="editForm.budget_amount" :min="0" :precision="2" style="width:100%" @change="handleSaveEdit" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="中标金额">
                  <el-input-number v-model="editForm.bid_amount" :min="0" :precision="2" style="width:100%" @change="handleSaveEdit" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="预计签单">
                  <el-date-picker v-model="editForm.expected_sign_date" type="date" placeholder="选择日期" style="width:100%" value-format="YYYY-MM-DD" @change="handleSaveEdit" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="竞品">
                  <el-input v-model="editForm.competitor" placeholder="竞争对手" @change="handleSaveEdit" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="关联合同">
                  <el-select v-model="editForm.contract_id" placeholder="选择合同" clearable style="width:100%" @change="handleSaveEdit">
                    <el-option v-for="c in contracts" :key="c.id" :label="c.contract_no + ' - ' + c.name" :value="c.id" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="中标日期">
                  <el-date-picker v-model="editForm.bid_date" type="date" placeholder="选择日期" style="width:100%" value-format="YYYY-MM-DD" @change="handleSaveEdit" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <el-tabs v-model="activeTab">
          <el-tab-pane label="跟进记录" name="followups">
            <div style="margin-bottom:12px">
              <el-button size="small" type="primary" @click="showFollowupForm = true">添加跟进</el-button>
            </div>
            <div class="timeline">
              <div class="timeline-item" v-for="f in followups" :key="f.id">
                <div class="timeline-dot"></div>
                <div class="timeline-date">{{ f.followup_date }} · {{ f.followup_method }} · {{ f.followup_by }}</div>
                <div class="timeline-content">
                  <p><strong>内容：</strong>{{ f.content || '-' }}</p>
                  <p><strong>结果：</strong>{{ f.result || '-' }}</p>
                  <p><strong>下一步：</strong>{{ f.next_plan || '-' }}</p>
                </div>
              </div>
              <el-empty v-if="followups.length === 0" description="暂无跟进记录" />
            </div>
            <el-form v-if="showFollowupForm" :model="followupForm" label-width="80px" size="small" style="margin-top:16px;padding:16px;background:#f5f7fa;border-radius:8px">
              <el-form-item label="跟进日期">
                <el-date-picker v-model="followupForm.followup_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
              </el-form-item>
              <el-form-item label="跟进方式">
                <el-select v-model="followupForm.followup_method" style="width:100%">
                  <el-option label="上门拜访" value="上门拜访" />
                  <el-option label="电话沟通" value="电话沟通" />
                  <el-option label="微信" value="微信" />
                  <el-option label="邮件" value="邮件" />
                </el-select>
              </el-form-item>
              <el-form-item label="跟进人">
                <el-input v-model="followupForm.followup_by" />
              </el-form-item>
              <el-form-item label="跟进内容">
                <el-input v-model="followupForm.content" type="textarea" :rows="2" />
              </el-form-item>
              <el-form-item label="跟进结果">
                <el-input v-model="followupForm.result" />
              </el-form-item>
              <el-form-item label="下一步">
                <el-input v-model="followupForm.next_plan" type="textarea" :rows="2" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" size="small" @click="handleAddFollowup" :loading="savingFollowup">保存</el-button>
                <el-button size="small" @click="showFollowupForm = false">取消</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="实施阶段" name="phases">
            <el-button size="small" type="primary" @click="showPhaseForm = true" style="margin-bottom:12px">添加阶段</el-button>
            <el-form v-if="showPhaseForm" :model="phaseForm" label-width="80px" size="small" style="margin-bottom:12px;padding:16px;background:#f5f7fa;border-radius:8px">
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="阶段名称">
                    <el-input v-model="phaseForm.name" placeholder="如：需求分析" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="状态">
                    <el-select v-model="phaseForm.status" style="width:100%">
                      <el-option label="未开始" value="not_started" />
                      <el-option label="进行中" value="in_progress" />
                      <el-option label="已完成" value="completed" />
                      <el-option label="暂停" value="suspended" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="计划开始">
                    <el-date-picker v-model="phaseForm.plan_start" type="date" value-format="YYYY-MM-DD" style="width:100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="计划结束">
                    <el-date-picker v-model="phaseForm.plan_end" type="date" value-format="YYYY-MM-DD" style="width:100%" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item>
                <el-button type="primary" size="small" @click="handleAddPhase">保存</el-button>
                <el-button size="small" @click="showPhaseForm = false">取消</el-button>
              </el-form-item>
            </el-form>
            <el-table :data="phases" size="small" v-if="phases.length">
              <el-table-column prop="name" label="阶段名称" />
              <el-table-column prop="plan_start" label="计划开始" width="100" />
              <el-table-column prop="plan_end" label="计划结束" width="100" />
              <el-table-column label="进度" width="120">
                <template #default="{ row }"><el-progress :percentage="row.progress" /></template>
              </el-table-column>
              <el-table-column label="状态" width="80">
                <template #default="{ row }"><el-tag :type="row.status==='completed'?'success':row.status==='in_progress'?'warning':'info'" size="small">{{ row.status }}</el-tag></template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无实施阶段" />
          </el-tab-pane>

          <el-tab-pane label="任务" name="tasks">
            <el-button size="small" type="primary" @click="showTaskForm = true" style="margin-bottom:12px">添加任务</el-button>
            <el-form v-if="showTaskForm" :model="taskForm" label-width="80px" size="small" style="margin-bottom:12px;padding:16px;background:#f5f7fa;border-radius:8px">
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="任务名称">
                    <el-input v-model="taskForm.name" placeholder="任务名称" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="负责人">
                    <el-input v-model="taskForm.assignee" placeholder="负责人" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="截止日期">
                    <el-date-picker v-model="taskForm.due_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item>
                <el-button type="primary" size="small" @click="handleAddTask">保存</el-button>
                <el-button size="small" @click="showTaskForm = false">取消</el-button>
              </el-form-item>
            </el-form>
            <el-table :data="tasks" size="small" v-if="tasks.length">
              <el-table-column prop="name" label="任务名称" />
              <el-table-column prop="assignee" label="负责人" width="80" />
              <el-table-column prop="due_date" label="截止日期" width="100" />
              <el-table-column label="进度" width="120">
                <template #default="{ row }"><el-progress :percentage="row.progress" /></template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无任务" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getProjects, createProject, updateProject, getProjectFollowups, createFollowup, getProjectPhases, getProjectTasks, getFunnelStats, createPhase, createTask } from '@/api/project'
import { getCustomers } from '@/api/customer'
import { getContracts } from '@/api/contract'

const loading = ref(false)
const creating = ref(false)
const savingFollowup = ref(false)
const showQuickCreate = ref(false)
const showDetail = ref(false)
const showFollowupForm = ref(false)
const showPhaseForm = ref(false)
const showTaskForm = ref(false)
const activeTab = ref('followups')
const activeStage = ref('contact')
const quickFormRef = ref(null)

const tableData = ref([])
const customers = ref([])
const detailProject = ref(null)
const followups = ref([])
const contracts = ref([])
const phases = ref([])
const tasks = ref([])
const funnelData = ref([])

const searchForm = reactive({ search: '', status: '' })
const quickForm = reactive({ name: '', customer_id: '', budget_amount: 0, manager: '' })
const quickRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
}

const editForm = reactive({ status: '', probability: 0, budget_amount: 0, bid_amount: 0, expected_sign_date: '', competitor: '', contract_id: '', bid_date: '' })
const followupForm = reactive({ followup_date: '', followup_method: '上门拜访', followup_by: '', content: '', result: '', next_plan: '' })
const phaseForm = reactive({ name: '', plan_start: '', plan_end: '', progress: 0, status: 'not_started' })
const taskForm = reactive({ name: '', assignee: '', due_date: '', progress: 0, status: 'pending' })

const statusList = [
  { value: 'contact', label: '接触洽谈', color: '#909399' },
  { value: 'bidding', label: '投标', color: '#409EFF' },
  { value: 'signing', label: '签约', color: '#E6A23C' },
  { value: 'implementation', label: '实施', color: '#F56C6C' },
  { value: 'acceptance', label: '验收', color: '#67C23A' },
  { value: 'after_sales', label: '售后', color: '#909399' },
  { value: 'lost', label: '流失', color: '#C0C4CC' },
]

const statusMap = Object.fromEntries(statusList.map(s => [s.value, s.label]))

const activeProjects = computed(() => {
  return tableData.value.filter(p => p.status === activeStage.value)
})

const stageCount = (status) => {
  return tableData.value.filter(p => p.status === status).length
}

const loadProjects = async () => {
  loading.value = true
  try {
    const res = await getProjects({ page: 1, page_size: 100, ...searchForm })
    tableData.value = res.items
  } catch (e) { console.error('加载项目失败:', e) } finally { loading.value = false }
}

const loadFunnel = async () => {
  try {
    const res = await getFunnelStats()
    funnelData.value = res.stages
  } catch (e) { console.error('加载漏斗统计失败:', e) }
}

const loadCustomers = async () => {
  try { const res = await getCustomers({ page_size: 100 }); customers.value = res.items } catch (e) { console.error('加载客户失败:', e) }
}

const loadContracts = async () => {
  try { const res = await getContracts({ page_size: 100 }); contracts.value = res.items } catch (e) { console.error('加载合同失败:', e) }
}

const handleSearch = () => loadProjects()
const handleReset = () => { searchForm.search = ''; searchForm.status = ''; loadProjects() }

const handleStageChange = async (project, newStatus) => {
  try {
    await updateProject(project.id, { status: newStatus })
    loadProjects(); loadFunnel()
    ElMessage.success(`已移至"${statusMap[newStatus]}"`)
  } catch (e) { console.error('移动失败:', e) }
}

const handleQuickCreate = async () => {
  if (!quickFormRef.value) return
  await quickFormRef.value.validate(async (valid) => {
    if (!valid) return
    creating.value = true
    try {
      await createProject({ ...quickForm, status: 'contact', progress: 0, probability: 20 })
      ElMessage.success('项目创建成功')
      showQuickCreate.value = false
      Object.assign(quickForm, { name: '', customer_id: '', budget_amount: 0, manager: '' })
      loadProjects(); loadFunnel()
    } catch (e) { console.error('创建失败:', e) } finally { creating.value = false }
  })
}

const openDetail = async (project) => {
  detailProject.value = project
  Object.assign(editForm, {
    status: project.status,
    probability: project.probability || 0,
    budget_amount: project.budget_amount || 0,
    bid_amount: project.bid_amount || 0,
    expected_sign_date: project.expected_sign_date || '',
    competitor: project.competitor || '',
    contract_id: project.contract_id || '',
    bid_date: project.bid_date || '',
  })
  showDetail.value = true
  activeTab.value = 'followups'
  showFollowupForm.value = false
  try {
    followups.value = await getProjectFollowups(project.id)
    phases.value = await getProjectPhases(project.id)
    tasks.value = await getProjectTasks(project.id)
  } catch (e) { console.error('加载详情失败:', e) }
}

const handleSaveEdit = async () => {
  if (!detailProject.value) return
  try {
    const data = { ...editForm }
    if (!data.expected_sign_date) data.expected_sign_date = null
    if (!data.bid_date) data.bid_date = null
    data.budget_amount = data.budget_amount || null
    data.bid_amount = data.bid_amount || null
    data.competitor = data.competitor || null
    await updateProject(detailProject.value.id, data)
    Object.assign(detailProject.value, data)
    loadProjects(); loadFunnel()
  } catch (e) { console.error('保存失败:', e) }
}

const handleAddFollowup = async () => {
  if (!detailProject.value) return
  if (!followupForm.followup_date) { ElMessage.warning('请选择跟进日期'); return }
  if (!followupForm.followup_by.trim()) { ElMessage.warning('请输入跟进人'); return }
  savingFollowup.value = true
  try {
    const data = { ...followupForm, project_id: detailProject.value.id }
    if (!data.followup_date) data.followup_date = new Date().toISOString().split('T')[0]
    await createFollowup(detailProject.value.id, data)
    ElMessage.success('跟进记录已添加')
    showFollowupForm.value = false
    followups.value = await getProjectFollowups(detailProject.value.id)
    loadProjects(); loadFunnel()
    Object.assign(followupForm, { followup_date: '', followup_method: '上门拜访', followup_by: detailProject.value?.manager || '', content: '', result: '', next_plan: '' })
  } catch (e) { console.error('添加跟进失败:', e) } finally { savingFollowup.value = false }
}

const handleAddPhase = async () => {
  if (!detailProject.value) return
  if (!phaseForm.name.trim()) { ElMessage.warning('请输入阶段名称'); return }
  try {
    await createPhase(detailProject.value.id, { ...phaseForm, project_id: detailProject.value.id })
    ElMessage.success('阶段已添加')
    showPhaseForm.value = false
    phases.value = await getProjectPhases(detailProject.value.id)
    Object.assign(phaseForm, { name: '', plan_start: '', plan_end: '', progress: 0, status: 'not_started' })
  } catch (e) { console.error('添加阶段失败:', e) }
}

const handleAddTask = async () => {
  if (!detailProject.value) return
  if (!taskForm.name.trim()) { ElMessage.warning('请输入任务名称'); return }
  try {
    await createTask(detailProject.value.id, { ...taskForm, project_id: detailProject.value.id })
    ElMessage.success('任务已添加')
    showTaskForm.value = false
    tasks.value = await getProjectTasks(detailProject.value.id)
    Object.assign(taskForm, { name: '', assignee: '', due_date: '', progress: 0, status: 'pending' })
  } catch (e) { console.error('添加任务失败:', e) }
}

const formatAmount = (val) => {
  const n = Number(val)
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}

const funnelHeight = (amount) => {
  const max = Math.max(...funnelData.value.map(s => s.total_amount), 1)
  return Math.max(4, (amount / max) * 28)
}

const funnelColor = (status) => {
  const colors = { contact: '#409EFF', bidding: '#409EFF', signing: '#409EFF', implementation: '#67C23A', acceptance: '#67C23A', after_sales: '#E6A23C', lost: '#C0C4CC' }
  return colors[status] || '#409EFF'
}

const isStale = (p) => {
  if (!p.last_followup_at) return true
  const last = new Date(p.last_followup_at)
  const now = new Date()
  return (now - last) / (1000 * 60 * 60 * 24) > 7
}

const daysSinceFollowup = (p) => {
  if (!p.last_followup_at) return 99
  const last = new Date(p.last_followup_at)
  const now = new Date()
  return Math.floor((now - last) / (1000 * 60 * 60 * 24))
}

const getStatusType = (s) => {
  const m = { contact: 'info', bidding: 'info', signing: 'warning', implementation: 'danger', acceptance: 'success', after_sales: 'primary', lost: 'info' }
  return m[s] || 'info'
}
const getStatusLabel = (s) => statusMap[s] || s

onMounted(() => { loadProjects(); loadFunnel(); loadCustomers(); loadContracts() })
</script>

<style scoped>
.pipeline-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { font-size: 20px; font-weight: 600; margin: 0; }
.header-right { display: flex; gap: 10px; align-items: center; }

/* Funnel */
.funnel-section { background: #fff; border-radius: 8px; padding: 20px 24px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.funnel-title { font-size: 15px; font-weight: 600; margin-bottom: 16px; }
.funnel-row { display: flex; gap: 12px; align-items: flex-end; }
.funnel-stage { flex: 1; text-align: center; cursor: pointer; padding: 8px; border-radius: 8px; transition: background .2s; }
.funnel-stage:hover { background: #f5f7fa; }
.funnel-stage.active { background: #ecf5ff; }
.funnel-label { font-size: 13px; color: #666; margin-bottom: 4px; }
.funnel-stage.active .funnel-label { color: #409EFF; font-weight: 600; }
.funnel-bar-wrap { height: 32px; display: flex; align-items: flex-end; justify-content: center; margin-bottom: 6px; }
.funnel-bar { width: 85%; border-radius: 4px; min-height: 4px; transition: height .3s; }
.funnel-amount { font-size: 16px; font-weight: 700; color: #303133; }
.funnel-count { font-size: 12px; color: #909399; }

/* Card Grid */
.card-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; padding-bottom: 16px; min-height: 200px; }
.card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.06); cursor: pointer; transition: box-shadow .2s; border-left: 3px solid transparent; display: flex; flex-direction: column; gap: 10px; }
.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.12); }
.card.warning { border-left-color: #F56C6C; }
.card.lost { opacity: 0.5; filter: grayscale(0.8); }
.card-body { min-width: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
.card-title { font-size: 14px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-customer { font-size: 12px; color: #909399; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 2px; }
.card-amount { font-weight: 600; color: #409EFF; font-size: 15px; }
.card-probability { font-size: 12px; background: #ecf5ff; color: #409EFF; padding: 1px 6px; border-radius: 3px; font-weight: 600; }
.card-competitor { color: #E6A23C; font-size: 11px; }
.card-footer { display: flex; align-items: center; gap: 8px; font-size: 11px; color: #909399; }
.card-owner { display: flex; align-items: center; gap: 3px; color: #606266; white-space: nowrap; }
.card-avatar { width: 20px; height: 20px; border-radius: 50%; background: #409EFF; color: #fff; font-size: 10px; display: inline-flex; align-items: center; justify-content: center; }
.card-date { color: #c0c4cc; white-space: nowrap; }
.card-warning-tag { display: inline-flex; align-items: center; gap: 2px; font-size: 11px; color: #F56C6C; margin-left: auto; }
.card-actions { }

/* Panel */
.panel-section { margin-bottom: 20px; }
.panel-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item label { display: block; font-size: 12px; color: #909399; margin-bottom: 2px; }
.info-item .val { font-size: 14px; color: #303133; }

/* Timeline */
.timeline { position: relative; padding-left: 20px; }
.timeline::before { content: ''; position: absolute; left: 6px; top: 0; bottom: 0; width: 2px; background: #e8e8e8; }
.timeline-item { margin-bottom: 14px; position: relative; }
.timeline-dot { position: absolute; left: -18px; top: 2px; width: 10px; height: 10px; border-radius: 50%; background: #409EFF; border: 2px solid #fff; box-shadow: 0 0 0 2px #409EFF; }
.timeline-date { font-size: 12px; color: #909399; margin-bottom: 4px; }
.timeline-content { background: #f5f7fa; padding: 12px; border-radius: 6px; font-size: 13px; }
.timeline-content p { margin-bottom: 2px; }
</style>
