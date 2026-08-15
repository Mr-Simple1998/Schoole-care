<template>
  <div class="page-container">
    <el-card shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-radio-group v-model="filterCat" @change="applyFilter">
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button value="学科">学科</el-radio-button>
            <el-radio-button value="非学科">非学科</el-radio-button>
          </el-radio-group>
        </div>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增学科</el-button>
      </div>

      <el-table :data="filteredSubjects" stripe>
        <el-table-column prop="name" label="学科名称" width="200" />
        <el-table-column prop="category" label="分类" width="150">
          <template #default="{ row }">
            <el-tag :type="row.category === '学科' ? 'primary' : 'warning'" size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort" label="排序" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openDialog(row)">编辑</el-button>
            <el-button size="small" :type="row.is_active ? 'warning' : 'success'" link @click="toggleActive(row)">
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑学科对话框 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑学科' : '新增学科'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="学科名称" prop="name">
          <el-input v-model="form.name" placeholder="如：语文 / 魔方" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-radio-group v-model="form.category">
            <el-radio value="学科">学科</el-radio>
            <el-radio value="非学科">非学科</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'

const filterCat = ref('')
const subjects = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()

const emptyForm = () => ({ id: null, name: '', category: '学科', sort: 0 })
const form = reactive(emptyForm())

const rules = {
  name: [{ required: true, message: '请输入学科名称', trigger: 'blur' }],
}

const filteredSubjects = computed(() => {
  if (!filterCat.value) return subjects.value
  return subjects.value.filter((s) => s.category === filterCat.value)
})

async function loadSubjects() {
  subjects.value = await request.get('/subjects')
}

function openDialog(row) {
  Object.assign(form, emptyForm(), row || {})
  dialogVisible.value = true
}

function applyFilter() {}

async function handleSave() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (form.id) {
        await request.put(`/subjects/${form.id}`, form)
        ElMessage.success('修改成功')
      } else {
        await request.post('/subjects', form)
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      loadSubjects()
    } finally {
      saving.value = false
    }
  })
}

async function toggleActive(row) {
  await request.put(`/subjects/${row.id}`, { is_active: !row.is_active })
  ElMessage.success(row.is_active ? '已停用' : '已启用')
  loadSubjects()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除学科「${row.name}」吗？相关学生将解除该学科关联。`, '提示', { type: 'warning' })
  await request.delete(`/subjects/${row.id}`)
  ElMessage.success('已删除')
  loadSubjects()
}

onMounted(loadSubjects)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

/* 分类标签颜色更新 */
:deep(.el-tag--primary) {
  --el-tag-bg-color: #e0f2fe;
  --el-tag-border-color: #bae6fd;
  --el-tag-text-color: #0369a1;
}
:deep(.el-tag--warning) {
  --el-tag-bg-color: #fef3c7;
  --el-tag-border-color: #fde68a;
  --el-tag-text-color: #b45309;
}

/* 表格行 hover 过渡 */
.el-table tbody tr {
  transition: background-color 0.25s ease;
}
</style>