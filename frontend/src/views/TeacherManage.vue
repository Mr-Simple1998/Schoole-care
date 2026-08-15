<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>教师账号管理</span>
          <el-button type="primary" size="small" :icon="Plus" @click="openDialog">新增教师账号</el-button>
        </div>
      </template>

      <el-table :data="teachers" stripe>
        <el-table-column prop="username" label="账号" width="110" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="role" label="角色" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.role === 'principal' ? 'danger' : 'primary'">
              {{ row.role === 'principal' ? '校长' : '教师' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="所属学科" min-width="180">
          <template #default="{ row }">
            <template v-if="row.subjects && row.subjects.length">
              <el-tag
                v-for="s in row.subjects"
                :key="s.id"
                size="small"
                :type="s.category === '学科' ? 'primary' : 'warning'"
                style="margin-right: 4px"
              >{{ s.name }}</el-tag>
            </template>
            <span v-else style="color:#c0c4cc">未设置</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="330">
          <template #default="{ row }">
            <template v-if="row.role !== 'principal'">
              <el-button size="small" link type="primary" @click="openEditDialog(row)">编辑学科</el-button>
              <el-button size="small" link type="warning" @click="openResetPwd(row)">重置密码</el-button>
              <el-button v-if="row.is_active" size="small" link type="warning" @click="handleToggle(row, false)">停用</el-button>
              <el-button v-else size="small" link type="success" @click="handleToggle(row, true)">重新启用</el-button>
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
        <el-form-item label="角色">
          <el-radio-group v-model="form.role">
            <el-radio value="teacher">教师</el-radio>
            <el-radio value="principal">校长（管理员）</el-radio>
          </el-radio-group>
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

    <!-- 编辑学科对话框 -->
    <el-dialog v-model="editVisible" title="编辑教师所属学科" width="480px">
      <div style="margin-bottom: 12px">教师：<b>{{ editTarget?.name }}</b></div>
      <el-select v-model="editSubjectIds" multiple filterable placeholder="可多选（学科/非学科）" style="width: 100%">
        <el-option-group v-if="subjectGroups.学科.length" label="学科">
          <el-option v-for="s in subjectGroups.学科" :key="s.id" :label="s.name" :value="s.id" />
        </el-option-group>
        <el-option-group v-if="subjectGroups['非学科'].length" label="非学科">
          <el-option v-for="s in subjectGroups['非学科']" :key="s.id" :label="s.name" :value="s.id" />
        </el-option-group>
      </el-select>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'

const teachers = ref([])
const subjects = ref([])
const dialogVisible = ref(false)
const editVisible = ref(false)
const pwdVisible = ref(false)
const editTarget = ref(null)
const pwdTarget = ref(null)
const editSubjectIds = ref([])
const pwdForm = reactive({ password: '' })
const saving = ref(false)
const formRef = ref()

const subjectGroups = computed(() => {
  const groups = { 学科: [], 非学科: [] }
  subjects.value.forEach((s) => {
    if (s.is_active) groups[s.category]?.push(s)
  })
  return groups
})

const form = reactive({ username: '', password: '', name: '', role: 'teacher', phone: '', email: '', subject_ids: [] })
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

function openDialog() {
  Object.assign(form, { username: '', password: '', name: '', role: 'teacher', phone: '', email: '', subject_ids: [] })
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
  editVisible.value = true
}

async function handleEditSave() {
  saving.value = true
  try {
    await request.put(`/auth/users/${editTarget.value.id}`, { subject_ids: editSubjectIds.value })
    ElMessage.success('学科已更新')
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
  ElMessage.success(`已${verb}`)
  loadTeachers()
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
</style>