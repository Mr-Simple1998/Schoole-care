<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>教师账号管理</span>
          <el-button type="primary" size="small" :icon="Plus" @click="openDialog">新增教师账号</el-button>
        </div>
      </template>

      <!-- 顶部小统计（纯展示，基于 teachers 计算） -->
      <div class="mini-stats teacher-stats">
        <div class="mini-stat">
          <div class="ms-label">教师总数</div>
          <div class="ms-value">{{ teacherStats.total }}</div>
          <div class="ms-sub">含校长管理号 {{ teacherStats.heads }} 个</div>
        </div>
        <div class="mini-stat">
          <div class="ms-label">启用中</div>
          <div class="ms-value is-active">{{ teacherStats.active }}</div>
          <div class="ms-sub">可正常登录使用</div>
        </div>
        <div class="mini-stat">
          <div class="ms-label">已停用</div>
          <div class="ms-value is-inactive">{{ teacherStats.inactive }}</div>
          <div class="ms-sub">停用后无法登录</div>
        </div>
        <div class="mini-stat">
          <div class="ms-label">覆盖学科</div>
          <div class="ms-value">{{ teacherStats.subjects }}</div>
          <div class="ms-sub">教师学科去重统计</div>
        </div>
      </div>

      <!-- 校区筛选（校长可按校区查看教师情况） -->
      <div v-if="userStore.isPrincipal" class="toolbar">
        <div class="toolbar-left">
          <el-select v-model="filterCampusId" placeholder="全部校区" clearable style="width: 180px" @change="handleFilterChange">
            <el-option v-for="c in campuses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <span class="result-count">共 <b>{{ filteredTeachers.length }}</b> 名教师</span>
        </div>
      </div>

      <el-table :data="filteredTeachers" stripe>
        <el-table-column prop="username" label="账号" width="110" />
        <el-table-column prop="name" label="姓名" width="110">
          <template #default="{ row }">
            <div class="name-cell">
              <span class="teacher-avatar" :class="{ 'is-principal': row.role === 'principal' }">{{ (row.name || '?').slice(0, 1) }}</span>
              <span class="cell-value">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="110">
          <template #default="{ row }">
            <el-tag size="small" round effect="light" :type="roleTagType(row.role)">
              {{ roleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="所属校区" width="110">
          <template #default="{ row }">
            <span v-if="row.campus_name" class="campus-tag">{{ row.campus_name }}</span>
            <span v-else class="cell-empty">未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="所属学科" min-width="180">
          <template #default="{ row }">
            <template v-if="row.subjects && row.subjects.length">
              <el-tag
                v-for="s in row.subjects"
                :key="s.id"
                size="small"
                effect="plain"
                :type="s.category === '学科' ? 'primary' : 'warning'"
                style="margin-right: 4px"
              >{{ s.name }}</el-tag>
            </template>
            <span v-else class="cell-empty">未设置</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="电话" width="130">
          <template #default="{ row }">
            <span :class="row.phone ? 'cell-value' : 'cell-empty'">{{ row.phone || '未设置' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱">
          <template #default="{ row }">
            <span :class="row.email ? 'cell-value' : 'cell-empty'">{{ row.email || '未设置' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <span v-if="row.resigned" class="status-dot is-danger">已离职</span>
            <span v-else class="status-dot" :class="row.is_active ? 'is-success' : 'is-danger'">
              {{ row.is_active ? '启用' : '停用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="380">
          <template #default="{ row }">
            <template v-if="row.role !== 'principal' && !(userStore.isSubPrincipal && row.role !== 'teacher')">
              <el-button size="small" link type="primary" @click="openEditDialog(row)">编辑学科</el-button>
              <el-button size="small" link type="warning" @click="openResetPwd(row)">重置密码</el-button>
              <el-button v-if="row.is_active" size="small" link type="warning" @click="handleToggle(row, false)">停用</el-button>
              <el-button v-else size="small" link type="success" @click="handleToggle(row, true)">重新启用</el-button>
              <el-button
                v-if="row.role === 'teacher' && row.is_active"
                size="small"
                link
                type="danger"
                @click="handleResign(row)"
              >离职</el-button>
              <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增账号对话框 -->
    <el-dialog v-model="dialogVisible" title="新增教师账号" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" placeholder="登录账号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="登录密码" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="所属校区" v-if="userStore.isPrincipal">
          <el-select v-model="form.campus_id" placeholder="选择校区（可选）" clearable style="width: 100%">
            <el-option v-for="c in campuses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属学科">
          <el-select v-model="form.subject_ids" multiple filterable placeholder="可多选（学科/非学科）" style="width: 100%">
            <el-option-group v-if="subjectGroups.学科.length" label="学科">
              <el-option v-for="s in subjectGroups.学科" :key="s.id" :label="s.name" :value="s.id" />
            </el-option-group>
            <el-option-group v-if="subjectGroups['非学科'].length" label="非学科">
              <el-option v-for="s in subjectGroups['非学科']" :key="s.id" :label="s.name" :value="s.id" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑教师对话框 -->
    <el-dialog v-model="editVisible" title="编辑教师信息" width="480px">
      <div style="margin-bottom: 12px">教师：<b>{{ editTarget?.name }}</b></div>
      <el-form label-width="80px">
        <el-form-item label="所属校区" v-if="userStore.isPrincipal">
          <el-select v-model="editCampusId" placeholder="选择校区（可选）" clearable style="width: 100%">
            <el-option v-for="c in campuses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属学科">
          <el-select v-model="editSubjectIds" multiple filterable placeholder="可多选（学科/非学科）" style="width: 100%">
            <el-option-group v-if="subjectGroups.学科.length" label="学科">
              <el-option v-for="s in subjectGroups.学科" :key="s.id" :label="s.name" :value="s.id" />
            </el-option-group>
            <el-option-group v-if="subjectGroups['非学科'].length" label="非学科">
              <el-option v-for="s in subjectGroups['非学科']" :key="s.id" :label="s.name" :value="s.id" />
            </el-option-group>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleEditSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="pwdVisible" title="重置教师密码" width="460px">
      <div style="margin-bottom: 12px">教师：<b>{{ pwdTarget?.name }}</b>（{{ pwdTarget?.username }}）</div>
      <el-input v-model="pwdForm.password" type="password" show-password placeholder="输入新密码（至少 6 位）" />
      <div class="tip-text">教师忘记密码时，校长可在此为其重置登录密码。</div>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="warning" @click="handleResetPwd">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const teachers = ref([])
const subjects = ref([])
const campuses = ref([])
const filterCampusId = ref(null)
const dialogVisible = ref(false)
const editVisible = ref(false)
const pwdVisible = ref(false)
const editTarget = ref(null)
const pwdTarget = ref(null)
const editSubjectIds = ref([])
const editCampusId = ref(null)
const pwdForm = reactive({ password: '' })
const saving = ref(false)
const formRef = ref()

function roleText(role) {
  if (role === 'principal') return '总校长'
  if (role === 'sub_principal' || role === 'campus_head') return '校长管理号'
  return '教师'
}
function roleTagType(role) {
  if (role === 'principal') return 'danger'
  if (role === 'sub_principal' || role === 'campus_head') return 'success'
  return 'primary'
}

const subjectGroups = computed(() => {
  const groups = { 学科: [], 非学科: [] }
  subjects.value.forEach((s) => {
    if (s.is_active) groups[s.category]?.push(s)
  })
  return groups
})

// 按校区筛选（校长视角；校区负责人后端已限定本校区）
const filteredTeachers = computed(() => {
  if (!filterCampusId.value) return teachers.value
  return teachers.value.filter((t) => t.campus_id === filterCampusId.value)
})

// ===== 纯展示统计（不参与任何业务逻辑，仅用于顶部指标展示） =====
const teacherStats = computed(() => {
  const list = filteredTeachers.value
  const heads = list.filter((t) => t.role === 'sub_principal' || t.role === 'campus_head').length
  const active = list.filter((t) => t.is_active).length
  const subjectSet = new Set()
  list.forEach((t) => (t.subjects || []).forEach((s) => subjectSet.add(s.name)))
  return {
    total: list.length,
    heads,
    active,
    inactive: list.length - active,
    subjects: subjectSet.size,
  }
})

const form = reactive({ username: '', password: '', name: '', role: 'teacher', phone: '', email: '', campus_id: null, subject_ids: [] })
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
}

async function loadTeachers() {
  teachers.value = await request.get('/auth/teachers')
}

async function loadSubjects() {
  subjects.value = await request.get('/subjects')
}

async function loadCampuses() {
  try {
    campuses.value = await request.get('/campuses/options')
  } catch (e) {
    campuses.value = []
  }
}

function handleFilterChange() {}

function openDialog() {
  Object.assign(form, { username: '', password: '', name: '', role: 'teacher', phone: '', email: '', campus_id: null, subject_ids: [] })
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      await request.post('/auth/register', form)
      ElMessage.success('账号创建成功')
      dialogVisible.value = false
      loadTeachers()
    } finally {
      saving.value = false
    }
  })
}

function openEditDialog(row) {
  editTarget.value = row
  editSubjectIds.value = (row.subjects || []).map((s) => s.id)
  editCampusId.value = row.campus_id ?? null
  editVisible.value = true
}

async function handleEditSave() {
  saving.value = true
  try {
    await request.put(`/auth/users/${editTarget.value.id}`, {
      subject_ids: editSubjectIds.value,
      campus_id: editCampusId.value,
    })
    ElMessage.success('教师信息已更新')
    editVisible.value = false
    loadTeachers()
  } finally {
    saving.value = false
  }
}

async function handleToggle(row, active) {
  const verb = active ? '重新启用' : '停用'
  await ElMessageBox.confirm(`确定${verb}账号「${row.name}」吗？`, '提示', { type: 'warning' })
  await request.put(`/auth/users/${row.id}`, { is_active: active })
  ElMessage.success(active && row.resigned ? '已重新启用（离职标记已清除）' : `已${verb}`)
  loadTeachers()
}

async function handleResign(row) {
  await ElMessageBox.confirm(
    `确定办理「${row.name}」的离职吗？\n离职后其账号将停用，名下所有学生数据保留，并暂存至所在校区负责人处；之后可分配给其他教师或新账号。`,
    '教师离职',
    { type: 'warning', confirmButtonText: '办理离职', confirmButtonClass: 'el-button--danger' },
  )
  try {
    const res = await request.post(`/auth/users/${row.id}/resign`)
    const n = res.students_transferred || 0
    ElMessage.success(`离职办理完成：${n} 名学生已暂存至校区负责人处，可再分配`)
    loadTeachers()
  } catch (e) {
    // 全局拦截器已提示错误
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(
    `确定删除教师账号「${row.name}」吗？删除后无法恢复。`,
    '删除确认',
    { type: 'warning', confirmButtonText: '删除', confirmButtonClass: 'el-button--danger' },
  )
  try {
    await request.delete(`/auth/teachers/${row.id}`)
    ElMessage.success('已删除')
    loadTeachers()
  } catch {
    // 全局拦截器已提示错误（如名下有在读学生）
  }
}

function openResetPwd(row) {
  pwdTarget.value = row
  pwdForm.password = ''
  pwdVisible.value = true
}

async function handleResetPwd() {
  if (!pwdForm.password || pwdForm.password.length < 6) {
    ElMessage.warning('请输入至少 6 位的新密码')
    return
  }
  await request.put(`/auth/users/${pwdTarget.value.id}/reset-password`, { password: pwdForm.password })
  ElMessage.success('密码已重置')
  pwdVisible.value = false
}

onMounted(() => {
  loadTeachers()
  loadSubjects()
  loadCampuses()
  // 从校区管理页跳转带入校区筛选
  if (route.query.campus) {
    filterCampusId.value = Number(route.query.campus) || null
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tip-text {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}

/* 表格行 hover 过渡 */
.el-table tbody tr {
  transition: background-color 0.25s ease;
}

/* 按钮组间距优化 */
:deep(.el-table .el-button + .el-button) {
  margin-left: 2px;
}

/* 对话框样式优化 */
:deep(.el-dialog__header) {
  padding: 20px 24px 12px;
  border-bottom: 1px solid #f0f0f0;
}
:deep(.el-dialog__body) {
  padding: 20px 24px;
}
:deep(.el-dialog__footer) {
  padding: 12px 24px 20px;
  border-top: 1px solid #f0f0f0;
}

/* ===== 顶部小统计 ===== */
.teacher-stats {
  margin-bottom: 16px;
}
.teacher-stats .ms-value.is-active {
  color: var(--primary);
}
.teacher-stats .ms-value.is-inactive {
  color: var(--text-muted);
}

/* ===== 姓名头像 ===== */
.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.teacher-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary-lighter);
  color: var(--primary-dark);
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.teacher-avatar.is-principal {
  background: var(--danger-light);
  color: var(--danger);
}

/* ===== 表格单元格空值/普通值 ===== */
.cell-value {
  color: var(--text);
}
.cell-empty {
  color: var(--text-muted);
  font-size: 12px;
}
.campus-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 20px;
  background: var(--primary-lighter);
  color: var(--primary-dark);
  font-size: 12px;
  font-weight: 500;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  gap: 12px;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.result-count {
  font-size: 13px;
  color: var(--text-secondary);
  margin-left: 4px;
}
.result-count b {
  color: var(--primary);
  font-size: 15px;
}
</style>