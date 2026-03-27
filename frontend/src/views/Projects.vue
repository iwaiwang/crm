<template>
  <div class="projects-page">
    <div class="page-header">
      <h2>项目进度</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon> 新增项目
      </el-button>
    </div>

    <!-- 状态看板 -->
    <el-card class="kanban-card">
      <el-row :gutter="10">
        <el-col :span="4" v-for="status in statusList" :key="status.value">
          <div class="kanban-item" :style="{ borderLeftColor: status.color }">
            <div class="kanban-count">{{ status.count }}</div>
            <div class="kanban-label">{{ status.label }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="搜索">
          <el-input v-model="searchForm.search" placeholder="项目名称" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="接触洽谈" value="contact" />
            <el-option label="投标" value="bidding" />
            <el-option label="签约" value="signing" />
            <el-option label="实施" value="implementation" />
            <el-option label="验收" value="acceptance" />
            <el-option label="售后" value="after_sales" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 项目列表 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="name" label="项目名称" min-width="200" />
        <el-table-column prop="customer_name" label="客户" width="120" />
        <el-table-column prop="manager" label="负责人" width="100" />
        <el-table-column label="进度" width="150">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :status="row.progress === 100 ? 'success' : ''" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="end_date" label="预计结束" width="110" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">详情</el-button>
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
          :total="pagination.total" layout="total, sizes, prev, pager, next"
          @current-change="loadProjects" @size-change="loadProjects" />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="formData.id ? '编辑项目' : '新增项目'" width="650px">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="项目名称" prop="name">
              <el-input v-model="formData.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户" prop="customer_id">
              <el-select v-model="formData.customer_id" placeholder="请选择客户" style="width: 100%">
                <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="负责人" prop="manager">
              <el-input v-model="formData.manager" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="formData.status" style="width: 100%">
                <el-option label="接触洽谈" value="contact" />
                <el-option label="投标" value="bidding" />
                <el-option label="签约" value="signing" />
                <el-option label="实施" value="implementation" />
                <el-option label="验收" value="acceptance" />
                <el-option label="售后" value="after_sales" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker v-model="formData.start_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计结束" prop="end_date">
              <el-date-picker v-model="formData.end_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="进度" prop="progress">
          <el-slider v-model="formData.progress" :max="100" />
        </el-form-item>

        <el-divider content-position="left">投标信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="预算金额" prop="budget_amount">
              <el-input-number v-model="formData.budget_amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="中标金额" prop="bid_amount">
              <el-input-number v-model="formData.bid_amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="投标日期" prop="bid_date">
              <el-date-picker v-model="formData.bid_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="中标结果" prop="bid_result">
              <el-input v-model="formData.bid_result" placeholder="中标/未中标" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="竞争对手" prop="competitor">
          <el-input v-model="formData.competitor" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 项目详情对话框 -->
    <el-dialog v-model="showDetailDlg" title="项目详情" width="800px">
      <div v-if="currentProject">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="项目名称">{{ currentProject.name }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ currentProject.manager }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentProject.status)">{{ getStatusLabel(currentProject.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="进度">{{ currentProject.progress }}%</el-descriptions-item>
          <el-descriptions-item label="开始日期">{{ currentProject.start_date }}</el-descriptions-item>
          <el-descriptions-item label="预计结束">{{ currentProject.end_date }}</el-descriptions-item>
        </el-descriptions>

        <el-tabs>
          <el-tab-pane label="销售跟进">
            <el-button size="small" type="primary" @click="showFollowupDlg = true">添加跟进</el-button>
            <el-timeline class="followup-timeline">
              <el-timeline-item v-for="f in followups" :key="f.id" :timestamp="f.followup_date" placement="top">
                <el-card>
                  <p><strong>跟进方式：</strong>{{ f.followup_method }}</p>
                  <p><strong>内容：</strong>{{ f.content }}</p>
                  <p><strong>结果：</strong>{{ f.result }}</p>
                  <p><strong>下一步：</strong>{{ f.next_plan }}</p>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </el-tab-pane>
          <el-tab-pane label="实施计划">
            <el-button size="small" type="primary" @click="showPhaseDlg = true">添加阶段</el-button>
            <el-table :data="phases" style="margin-top: 10px">
              <el-table-column prop="name" label="阶段名称" />
              <el-table-column prop="plan_start" label="计划开始" />
              <el-table-column prop="plan_end" label="计划结束" />
              <el-table-column label="进度">
                <template #default="{ row }"><el-progress :percentage="row.progress" /></template>
              </el-table-column>
              <el-table-column label="状态">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'in_progress' ? 'warning' : 'info'">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="任务列表">
            <el-button size="small" type="primary" @click="showTaskDlg = true">添加任务</el-button>
            <el-table :data="tasks" style="margin-top: 10px">
              <el-table-column prop="name" label="任务名称" />
              <el-table-column prop="assignee" label="负责人" />
              <el-table-column prop="due_date" label="截止日期" />
              <el-table-column label="进度">
                <template #default="{ row }"><el-progress :percentage="row.progress" /></template>
              </el-table-column>
              <el-table-column label="状态">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'completed' ? 'success' : 'warning'">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer>
        <el-button @click="showDetailDlg = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProjects, createProject, updateProject, getProjectFollowups, createFollowup, getProjectPhases, createPhase, getProjectTasks, createTask, deleteProject } from '@/api/project'
import { getCustomers } from '@/api/customer'

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const showDetailDlg = ref(false)
const showFollowupDlg = ref(false)
const showPhaseDlg = ref(false)
const showTaskDlg = ref(false)
const formRef = ref(null)
const tableData = ref([])
const customers = ref([])
const currentProject = ref(null)
const followups = ref([])
const phases = ref([])
const tasks = ref([])

const statusList = reactive([
  { value: 'contact', label: '接触洽谈', count: 0, color: '#909399' },
  { value: 'bidding', label: '投标', count: 0, color: '#409EFF' },
  { value: 'signing', label: '签约', count: 0, color: '#E6A23C' },
  { value: 'implementation', label: '实施', count: 0, color: '#F56C6C' },
  { value: 'acceptance', label: '验收', count: 0, color: '#67C23A' },
  { value: 'after_sales', label: '售后', count: 0, color: '#909399' },
])

const searchForm = reactive({ search: '', status: '' })
const pagination = reactive({ page: 1, page_size: 20, total: 0 })
const formData = reactive({
  id: '', name: '', customer_id: '', manager: '', start_date: '', end_date: '',
  progress: 0, status: 'contact', budget_amount: 0, bid_amount: 0, bid_date: '',
  bid_result: '', competitor: '', remark: '',
})

const rules = { name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }], customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }] }

const loadProjects = async () => {
  loading.value = true
  try {
    const res = await getProjects({ page: pagination.page, page_size: pagination.page_size, ...searchForm })
    tableData.value = res.items
    pagination.total = res.total
    // 更新状态统计
    statusList.forEach(s => { s.count = res.items.filter(i => i.status === s.value).length })
  } catch (error) { console.error('加载失败:', error) } finally { loading.value = false }
}

const loadCustomers = async () => {
  try { const res = await getCustomers({ page_size: 100 }); customers.value = res.items } catch (error) { console.error('加载客户失败:', error) }
}

const handleSearch = () => { pagination.page = 1; loadProjects() }
const handleReset = () => { searchForm.search = ''; searchForm.status = ''; handleSearch() }
const handleEdit = (row) => { showDialog.value = true; Object.assign(formData, row) }

const openAddDialog = () => {
  showDialog.value = true
  Object.assign(formData, {
    id: '',
    name: '',
    customer_id: '',
    manager: '',
    status: 'contact',
    start_date: '',
    end_date: '',
    progress: 0,
    budget_amount: 0,
    bid_amount: 0,
    bid_date: '',
    bid_result: '',
    competitor: '',
    remark: '',
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该项目吗？', '提示', { type: 'warning' })
    await deleteProject(row.id)
    ElMessage.success('删除成功')
    loadProjects()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleView = async (row) => {
  currentProject.value = row
  showDetailDlg.value = true
  try {
    followups.value = await getProjectFollowups(row.id)
    phases.value = await getProjectPhases(row.id)
    tasks.value = await getProjectTasks(row.id)
  } catch (error) { console.error('加载详情失败:', error) }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (formData.id) { await updateProject(formData.id, formData); ElMessage.success('更新成功') }
        else { await createProject(formData); ElMessage.success('创建成功') }
        showDialog.value = false; loadProjects()
      } catch (error) { console.error('提交失败:', error) } finally { submitting.value = false }
    }
  })
}

const getStatusType = (status) => {
  const map = { contact: '', bidding: 'info', signing: 'warning', implementation: 'danger', acceptance: 'success', after_sales: '' }
  return map[status] || ''
}
const getStatusLabel = (status) => {
  const map = { contact: '接触洽谈', bidding: '投标', signing: '签约', implementation: '实施', acceptance: '验收', after_sales: '售后' }
  return map[status] || status
}

onMounted(() => { loadProjects(); loadCustomers() })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.kanban-card { margin-bottom: 20px; }
.kanban-item { border-left: 4px solid; padding: 15px; text-align: center; background: #f5f7fa; border-radius: 4px; }
.kanban-count { font-size: 24px; font-weight: bold; }
.kanban-label { font-size: 12px; color: #909399; margin-top: 5px; }
.search-card { margin-bottom: 20px; }
.table-card { margin-bottom: 20px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 20px; }
.followup-timeline { margin-top: 15px; max-height: 400px; overflow-y: auto; }
</style>
