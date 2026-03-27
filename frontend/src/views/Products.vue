<template>
  <div class="products-page">
    <div class="page-header">
      <h2>产品库存</h2>
      <div>
        <el-button type="warning" @click="showStockMoveDlg = true; stockMoveForm.type = 'in'">
          <el-icon><Download /></el-icon> 入库
        </el-button>
        <el-button type="danger" @click="showStockMoveDlg = true; stockMoveForm.type = 'out'">
          <el-icon><Upload /></el-icon> 出库
        </el-button>
        <el-button type="primary" @click="openAddDialog">
          <el-icon><Plus /></el-icon> 新增产品
        </el-button>
      </div>
    </div>

    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="搜索">
          <el-input v-model="searchForm.search" placeholder="产品名称/规格" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="库存">
          <el-select v-model="searchForm.low_stock" placeholder="全部" clearable>
            <el-option label="库存预警" :value="true" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="name" label="产品名称" min-width="150" />
        <el-table-column prop="spec" label="规格型号" width="120" />
        <el-table-column prop="unit" label="单位" width="60" />
        <el-table-column prop="price" label="单价" width="100" align="right">
          <template #default="{ row }">¥{{ Number(row.price).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="stock_qty" label="库存" width="80" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.stock_qty <= row.min_stock ? 'red' : '', fontWeight: row.stock_qty <= row.min_stock ? 'bold' : '' }">
              {{ row.stock_qty }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="min_stock" label="安全库存" width="80" align="right" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.stock_qty <= row.min_stock ? 'danger' : 'success'">
              {{ row.stock_qty <= row.min_stock ? '预警' : '充足' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
          :total="pagination.total" layout="total, sizes, prev, pager, next"
          @current-change="loadProducts" @size-change="loadProducts" />
      </div>
    </el-card>

    <!-- 新增/编辑产品对话框 -->
    <el-dialog v-model="showDialog" :title="formData.id ? '编辑产品' : '新增产品'" width="500px">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="产品名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="规格型号" prop="spec">
          <el-input v-model="formData.spec" />
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-input v-model="formData.unit" />
        </el-form-item>
        <el-form-item label="单价" prop="price">
          <el-input-number v-model="formData.price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="安全库存" prop="min_stock">
          <el-input-number v-model="formData.min_stock" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-input v-model="formData.category" />
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

    <!-- 出入库对话框 -->
    <el-dialog v-model="showStockMoveDlg" :title="stockMoveForm.type === 'in' ? '入库登记' : '出库登记'" width="450px">
      <el-form :model="stockMoveForm" ref="stockMoveFormRef" label-width="80px">
        <el-form-item label="选择产品">
          <el-select v-model="stockMoveForm.product_id" placeholder="请选择产品" style="width: 100%">
            <el-option v-for="p in tableData" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="stockMoveForm.qty" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="原因">
          <el-select v-model="stockMoveForm.reason" style="width: 100%">
            <el-option :label="stockMoveForm.type === 'in' ? '采购入库' : '销售出库'" :value="stockMoveForm.type === 'in' ? 'purchase' : 'sales'" />
            <el-option label="退货入库" value="return_in" v-if="stockMoveForm.type === 'in'" />
            <el-option label="退货出库" value="return_out" v-if="stockMoveForm.type === 'out'" />
            <el-option label="盘点调整" value="adjustment" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="stockMoveForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStockMoveDlg = false">取消</el-button>
        <el-button type="primary" @click="handleStockMove" :loading="stockMoveLoading">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProducts, createProduct, updateProduct, createStockMove, deleteProduct } from '@/api/product'

const loading = ref(false)
const submitting = ref(false)
const stockMoveLoading = ref(false)
const showDialog = ref(false)
const showStockMoveDlg = ref(false)
const formRef = ref(null)
const tableData = ref([])

const searchForm = reactive({ search: '', low_stock: null })
const pagination = reactive({ page: 1, page_size: 20, total: 0 })
const formData = reactive({ id: '', name: '', spec: '', unit: '件', price: 0, min_stock: 0, category: '', remark: '' })
const stockMoveForm = reactive({ product_id: '', type: 'in', qty: 1, reason: '', remark: '' })

const rules = { name: [{ required: true, message: '请输入产品名称', trigger: 'blur' }] }

const loadProducts = async () => {
  loading.value = true
  try {
    const res = await getProducts({ page: pagination.page, page_size: pagination.page_size, ...searchForm })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) { console.error('加载失败:', error) } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadProducts() }
const handleReset = () => { searchForm.search = ''; searchForm.low_stock = null; handleSearch() }
const handleEdit = (row) => { showDialog.value = true; Object.assign(formData, row) }

const openAddDialog = () => {
  showDialog.value = true
  Object.assign(formData, {
    id: '',
    name: '',
    spec: '',
    unit: '件',
    price: 0,
    min_stock: 0,
    category: '',
    remark: '',
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该产品吗？', '提示', { type: 'warning' })
    await deleteProduct(row.id)
    ElMessage.success('删除成功')
    loadProducts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (formData.id) { await updateProduct(formData.id, formData); ElMessage.success('更新成功') }
        else { await createProduct(formData); ElMessage.success('创建成功') }
        showDialog.value = false; loadProducts()
      } catch (error) { console.error('提交失败:', error) } finally { submitting.value = false }
    }
  })
}

const handleStockMove = async () => {
  if (!stockMoveForm.product_id || !stockMoveForm.qty) {
    ElMessage.warning('请选择产品和数量')
    return
  }
  stockMoveLoading.value = true
  try {
    await createStockMove(stockMoveForm)
    ElMessage.success(stockMoveForm.type === 'in' ? '入库成功' : '出库成功')
    showStockMoveDlg.value = false; loadProducts()
  } catch (error) { console.error('操作失败:', error) } finally { stockMoveLoading.value = false }
}

onMounted(() => { loadProducts() })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.search-card { margin-bottom: 20px; }
.table-card { margin-bottom: 20px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 20px; }
</style>
