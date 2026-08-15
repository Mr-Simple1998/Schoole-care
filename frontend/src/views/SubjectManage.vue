<template>
  <div class="page-container">
    <!-- 数据概览：学科 / 非学科 / 启用状态 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon is-teal"><el-icon :size="24"><Collection /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value num-strong">{{ stats.total }}</div>
          <div class="stat-label">学科总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon is-blue"><el-icon :size="24"><Reading /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value num-strong">{{ stats.academic }}</div>
          <div class="stat-label">学科类</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon is-amber"><el-icon :size="24"><Star /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value num-strong">{{ stats.nonAcademic }}</div>
          <div class="stat-label">非学科类</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon is-green"><el-icon :size="24"><CircleCheck /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value num-strong">{{ stats.active }}</div>
          <div class="stat-label">启用中</div>
        </div>
      </div>
    </div>

    <el-card shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-radio-group v-model="filterCat" @change="applyFilter">
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button value="学科">学科</el-radio-button>
            <el-radio-button value="非学科">非学科</el-radio-button>
          </el-radio-group>
        </div>
        <el-button v-if="userStore.isPrincipal" type="primary" :icon="Plus" @click="openDialog()">新增学科</el-button>
      </div>

      <el-table :data="filteredSubjects" stripe>
        <el-table-column prop="name" label="学科名称" min-width="220">
          <template #default="{ row }">
            <div class="subject-cell">
              <span class="subject-avatar" :class="row.category === '学科' ? 'is-academic' : 'is-other'">
                {{ row.name ? row.name.charAt(0) : '?' }}
              </span>
              <span class="subject-name">{{ row.name || '—' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="140" align="center">
          <template #default="{ row }">
            <el-tag :type="row.category === '学科' ? 'primary' : 'warning'" effect="light" round size="small">
              {{ row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="排序" width="100" align="center">
          <template #default="{ row }">
            <span class="sort-badge">#{{ row.sort }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <span class="status-dot" :class="row.is_active ? 'is-success' : 'is-info'">
              {{ row.is_active ? '启用中' : '已停用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column v-if="userStore.isPrincipal" label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openDialog(row)">编辑</el-button>
            <el-button size="small" :type="row.is_active ? 'warning' : 'success'" link @click="toggleActive(row)">
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无学科数据，点击右上角「新增学科」开始添加" :image-size="90" />
        </template>
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
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
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

// 纯展示：顶部概览统计（仅由现有数据派生，不触碰任何接口）
const stats = computed(() => {
  const list = subjects.value
  return {
    total: list.length,
    academic: list.filter((s) => s.category === '学科').length,
    nonAcademic: list.filter((s) => s.category === '非学科').length,
    active: list.filter((s) => s.is_active).length,
  }
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
/* 顶部概览统计卡 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}
.stat-body {
  min-width: 0;
}
.stat-icon.is-teal {
  background: linear-gradient(135deg, #34d399, #059669);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.25);
}
.stat-icon.is-blue {
  background: linear-gradient(135deg, #60a5fa, #2563eb);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.25);
}
.stat-icon.is-amber {
  background: linear-gradient(135deg, #fbbf24, #d97706);
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.25);
}
.stat-icon.is-green {
  background: linear-gradient(135deg, #4ade80, #16a34a);
  box-shadow: 0 6px 16px rgba(34, 197, 94, 0.25);
}

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

/* 学科名称：首字头像 + 名称 */
.subject-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.subject-avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}
.subject-avatar.is-academic {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
}
.subject-avatar.is-other {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}
.subject-name {
  font-weight: 500;
  color: var(--text);
}

/* 排序徽标 */
.sort-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* 分类标签颜色更新（学科=蓝 / 非学科=琥珀） */
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