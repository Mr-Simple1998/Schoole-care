<template>
  <div class="page-container">
    <el-card shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input v-model="keyword" placeholder="搜索姓名/学号" clearable style="width: 220px" @input="handleSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="filterSubjectId" placeholder="按学科筛选" clearable style="width: 160px" @change="handleSearch">
            <el-option-group v-if="subjectGroups.学科.length" label="学科">
              <el-option v-for="s in subjectGroups.学科" :key="s.id" :label="s.name" :value="s.id" />
            </el-option-group>
            <el-option-group v-if="subjectGroups['非学科'].length" label="非学科">
              <el-option v-for="s in subjectGroups['非学科']" :key="s.id" :label="s.name" :value="s.id" />
            </el-option-group>
          </el-select>
        </div>
        <el-button type="primary" :icon="Plus" class="btn-add" @click="openDialog()">新增学生</el-button>
      </div>

      <el-table :data="filteredStudents" stripe>
        <el-table-column prop="student_no" label="学号" width="110" />
        <el-table-column prop="name" label="姓名" width="110" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column prop="school" label="学校" width="120" />
        <el-table-column prop="grade" label="年级" width="110">
          <template #default="{ row }">
            <span style="white-space: nowrap">{{ row.grade || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="enrollment_date" label="入学时间" width="110" />
        <el-table-column label="学科" min-width="160">
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
        <el-table-column prop="guardian_name" label="监护人" width="100" />
        <el-table-column prop="guardian_phone" label="联系电话" width="130" />
        <el-table-column label="负责教师" width="100">
          <template #default="{ row }">
            <span v-if="row.teacher_name">{{ row.teacher_name }}</span>
            <span v-else style="color:#c0c4cc">未分配</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === '在读' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="points" label="积分" width="80" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="$router.push(`/student/${row.id}`)">学习档案</el-button>
            <el-button size="small" type="success" link @click="openAttendance(row)">打卡</el-button>
            <el-button size="small" link @click="openDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑学生' : '新增学生'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio value="男">男</el-radio>
            <el-radio value="女">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="学校">
          <el-input v-model="form.school" placeholder="如：XX小学" />
        </el-form-item>
        <el-form-item label="年级">
          <el-select v-model="form.grade" placeholder="请选择年级" style="width: 100%" filterable>
            <el-option-group label="小学">
              <el-option label="小学一年级" value="小学一年级" />
              <el-option label="小学二年级" value="小学二年级" />
              <el-option label="小学三年级" value="小学三年级" />
              <el-option label="小学四年级" value="小学四年级" />
              <el-option label="小学五年级" value="小学五年级" />
              <el-option label="小学六年级" value="小学六年级" />
            </el-option-group>
            <el-option-group label="初中">
              <el-option label="初中一年级" value="初中一年级" />
              <el-option label="初中二年级" value="初中二年级" />
              <el-option label="初中三年级" value="初中三年级" />
            </el-option-group>
            <el-option-group label="高中">
              <el-option label="高中一年级" value="高中一年级" />
              <el-option label="高中二年级" value="高中二年级" />
              <el-option label="高中三年级" value="高中三年级" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="所属学科">
          <el-select v-model="form.subject_ids" multiple filterable placeholder="可多选（学科/非学科）" style="width: 100%" @change="onSubjectChange">
            <el-option-group v-if="subjectGroups.学科.length" label="学科">
              <el-option v-for="s in subjectGroups.学科" :key="s.id" :label="s.name" :value="s.id" />
            </el-option-group>
            <el-option-group v-if="subjectGroups['非学科'].length" label="非学科">
              <el-option v-for="s in subjectGroups['非学科']" :key="s.id" :label="s.name" :value="s.id" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <!-- 课时配置：为每个已选学科设置课时 -->
        <el-form-item v-if="form.subject_ids.length > 0" label="课时配置">
          <div class="session-config">
            <div v-for="sid in form.subject_ids" :key="sid" class="session-row">
              <span class="session-label">{{ getSubjectName(sid) }}</span>
              <el-input-number
                v-model="form.sessionMap[sid]"
                :min="0"
                :max="999"
                placeholder="课时数"
                controls-position="right"
                style="width: 140px"
              />
              <span class="session-hint">次</span>
              <template v-if="!form.sessionMap[sid]">
                <input
                  v-model="form.durationValueMap[sid]"
                  :type="'number'"
                  min="0"
                  placeholder="时长"
                  style="width: 80px; margin-left: 8px"
                />
                <el-select v-model="form.durationUnitMap[sid]" placeholder="单位" style="width: 80px; margin-left: 6px">
                  <el-option label="天" value="天" />
                  <el-option label="月" value="月" />
                  <el-option label="年" value="年" />
                </el-select>
              </template>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="监护人">
          <el-input v-model="form.guardian_name" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.guardian_phone" />
        </el-form-item>
        <el-form-item label="入学日期">
          <el-date-picker v-model="form.enrollment_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 打卡对话框 -->
    <el-dialog v-model="attVisible" title="考勤打卡" width="480px">
      <el-form :model="attForm" label-width="80px">
        <el-form-item label="学生">
          <span style="font-weight:600">{{ attStudent?.name }}</span>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="attForm.subject_id" placeholder="请选择打卡学科" style="width:100%" filterable clearable>
            <el-option
              v-for="ss in attStudent?.subject_sessions || []"
              :key="ss.subject_id"
              :label="`${ss.subject_name}${ss.remaining !== null ? ' (剩' + ss.remaining + '次)' : ''}`"
              :value="ss.subject_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="attForm.status" style="width:100%">
            <el-option label="正常" value="正常" /><el-option label="迟到" value="迟到" /><el-option label="早退" value="早退" />
            <el-option label="请假" value="请假" /><el-option label="缺勤" value="缺勤" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="attForm.remark" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="attVisible = false">取消</el-button>
        <el-button type="primary" :loading="attSaving" @click="saveAttendance">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import request from '@/utils/request'

const keyword = ref('')
const filterSubjectId = ref(null)
const students = ref([])
const subjects = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const attVisible = ref(false)
const attSaving = ref(false)
const attStudent = ref(null)
const attForm = reactive({ subject_id: null, status: '正常', remark: '' })

// 学科按分类分组
const subjectGroups = computed(() => {
  const groups = { 学科: [], 非学科: [] }
  subjects.value.forEach((s) => {
    if (s.is_active) groups[s.category]?.push(s)
  })
  return groups
})

const emptyForm = () => ({
  id: null, name: '', gender: '男', school: '', grade: '',
  guardian_name: '', guardian_phone: '', enrollment_date: '', notes: '',
  subject_ids: [],
  sessionMap: {},  // { subject_id: total_sessions }
  expireMap: {},   // { subject_id: expire_date }
  durationValueMap: {},  // { subject_id: 时长数值 }
  durationUnitMap: {},   // { subject_id: 天/月/年 }
})
const form = reactive(emptyForm())

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
}

const filteredStudents = computed(() => {
  const k = keyword.value.trim()
  return students.value.filter((s) => {
    const matchK = !k || s.name.includes(k) || s.student_no.includes(k)
    const matchS = !filterSubjectId.value || (s.subjects || []).some((x) => x.id === filterSubjectId.value)
    return matchK && matchS
  })
})

function getSubjectName(sid) {
  const s = subjects.value.find((x) => x.id === sid)
  return s ? s.name : '未知'
}

function onSubjectChange(ids) {
  // 清理已移除学科的课时配置
  const newMap = {}
  const newExpireMap = {}
  const newDurValMap = {}
  const newDurUnitMap = {}
  ids.forEach((id) => {
    newMap[id] = form.sessionMap[id] ?? null
    newExpireMap[id] = form.expireMap[id] ?? null
    newDurValMap[id] = form.durationValueMap[id] ?? null
    newDurUnitMap[id] = form.durationUnitMap[id] ?? null
  })
  form.sessionMap = newMap
  form.expireMap = newExpireMap
  form.durationValueMap = newDurValMap
  form.durationUnitMap = newDurUnitMap
}

async function loadStudents() {
  students.value = await request.get('/students')
}

async function loadSubjects() {
  subjects.value = await request.get('/subjects')
}

function openDialog(row) {
  Object.assign(form, emptyForm(), row || {})
  // 把已选学科 id 填入 subject_ids
  form.subject_ids = (row?.subjects || []).map((s) => s.id)
  // 把已有课时配置填入 sessionMap
  form.sessionMap = {}
  form.expireMap = {}
  form.durationValueMap = {}
  form.durationUnitMap = {}
  if (row?.subject_sessions) {
    row.subject_sessions.forEach((ss) => {
      form.sessionMap[ss.subject_id] = ss.total_sessions
      form.expireMap[ss.subject_id] = ss.expire_date || null
      form.durationValueMap[ss.subject_id] = ss.duration_value || null
      form.durationUnitMap[ss.subject_id] = ss.duration_unit || null
    })
  }
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      // 构建 subject_sessions
      const subject_sessions = Object.entries(form.sessionMap)
        .map(([sid, total]) => ({
          subject_id: parseInt(sid),
          total_sessions: total || null,
          duration_value: form.durationValueMap[sid] || null,
          duration_unit: form.durationUnitMap[sid] || null,
          expire_date: form.expireMap[sid] || null,
        }))

      const payload = {
        name: form.name,
        gender: form.gender,
        school: form.school || null,
        grade: form.grade || null,
        class_name: form.class_name || null,
        guardian_name: form.guardian_name || null,
        guardian_phone: form.guardian_phone || null,
        enrollment_date: form.enrollment_date || null,
        notes: form.notes || null,
        subject_ids: form.subject_ids,
        subject_sessions: subject_sessions.length > 0 ? subject_sessions : null,
      }

      if (form.id) {
        await request.put(`/students/${form.id}`, payload)
        ElMessage.success('修改成功')
      } else {
        await request.post('/students', payload)
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      loadStudents()
    } finally {
      saving.value = false
    }
  })
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除学生「${row.name}」吗？`, '提示', { type: 'warning' })
  await request.delete(`/students/${row.id}`)
  ElMessage.success('已删除')
  loadStudents()
}

// 打卡：从列表行数据直接打卡（列表已含 subject_sessions）
function todayStr() {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${dd}`
}

function openAttendance(row) {
  attStudent.value = row
  attForm.subject_id = null
  attForm.status = '正常'
  attForm.remark = ''
  attVisible.value = true
}

async function saveAttendance() {
  if (!attForm.subject_id) {
    ElMessage.warning('请选择打卡学科')
    return
  }
  attSaving.value = true
  try {
    await request.post('/learning/attendance', {
      student_id: attStudent.value.id,
      subject_id: attForm.subject_id,
      date: todayStr(),
      status: attForm.status,
      remark: attForm.remark,
    })
    ElMessage.success('打卡成功')
    attVisible.value = false
    // 提示核销信息
    const ss = attStudent.value.subject_sessions.find(s => s.subject_id === attForm.subject_id)
    if (ss && ss.remaining !== null) {
      ElMessage.info(`「${ss.subject_name}」剩余课时：${ss.remaining} 次`)
    }
    loadStudents()
  } finally {
    attSaving.value = false
  }
}

function handleSearch() {}

onMounted(() => {
  loadStudents()
  loadSubjects()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
:deep(.el-input__wrapper) {
  border-radius: 8px;
}
:deep(.el-table__body tr) {
  transition: background-color 0.3s ease;
}
.btn-add {
  --el-button-bg-color: #10b981;
  --el-button-border-color: #10b981;
  --el-button-hover-bg-color: #059669;
  --el-button-hover-border-color: #059669;
  --el-button-active-bg-color: #047857;
  --el-button-active-border-color: #047857;
}
.session-config {
  width: 100%;
}
.session-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.session-label {
  width: 60px;
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
}
.session-hint {
  font-size: 12px;
  color: #909399;
}
</style>