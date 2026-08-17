<template>
  <div class="page-container">
    <el-card shadow="never">
      <!-- 数据概览 -->
      <div class="mini-stats mb-16">
        <div class="mini-stat">
          <div class="ms-label">👥 学生总数</div>
          <div class="ms-value">{{ summary.total }}</div>
        </div>
        <div class="mini-stat">
          <div class="ms-label">✅ 在读学生</div>
          <div class="ms-value" style="color: var(--success)">{{ summary.active }}</div>
          <div class="ms-sub">在读率 {{ summary.activeRate }}%</div>
        </div>
        <div class="mini-stat">
          <div class="ms-label">📚 启用学科</div>
          <div class="ms-value" style="color: var(--info)">{{ summary.subjCount }}</div>
        </div>
        <div class="mini-stat">
          <div class="ms-label">📅 本月入学</div>
          <div class="ms-value" style="color: var(--warning)">{{ summary.thisMonth }}</div>
        </div>
      </div>

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
          <el-select v-if="userStore.isPrincipal" v-model="filterCampusId" placeholder="全部校区" clearable style="width: 160px" @change="handleSearch">
            <el-option v-for="c in campuses" :key="c.id" :label="c.name" :value="c.id" />
            <el-option label="未分校区" :value="0" />
          </el-select>
          <span class="result-count">共 <b>{{ filteredStudents.length }}</b> 名学生</span>
          <el-checkbox v-if="canAssign" v-model="onlyUnassigned" @change="handleSearch">只看暂存学生</el-checkbox>
        </div>
        <div class="toolbar-right">
          <el-button v-if="canAssign" type="warning" :disabled="!selectedRows.length" @click="openAssignDialog">分配教师</el-button>
          <el-button type="primary" :icon="Plus" class="btn-add" @click="openDialog()">新增学生</el-button>
        </div>
      </div>

      <el-table :data="filteredStudents" stripe @selection-change="onSelectionChange">
        <el-table-column v-if="canAssign" type="selection" width="45" />
        <el-table-column prop="student_no" label="学号" width="110" />
        <el-table-column prop="name" label="姓名" width="110" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column prop="school" label="学校" width="120" />
        <el-table-column label="校区" width="110">
          <template #default="{ row }">
            <span v-if="row.campus_name" class="campus-cell">{{ row.campus_name }}</span>
            <span v-else class="empty-inline">未分校区</span>
          </template>
        </el-table-column>
        <el-table-column prop="grade" label="年级" width="110">
          <template #default="{ row }">
            <span style="white-space: nowrap">{{ row.grade || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="enrollment_date" label="入学时间" width="110" />
        <el-table-column label="学科" min-width="180">
          <template #default="{ row }">
            <div class="subject-cell">
              <div class="subject-tags">
                <template v-if="row.subjects && row.subjects.length">
                  <el-tag
                    v-for="s in row.subjects"
                    :key="s.id"
                    size="small"
                    :type="s.category === '学科' ? 'primary' : 'warning'"
                    style="margin-right: 4px"
                  >{{ s.name }}</el-tag>
                </template>
                <span v-else class="empty-inline">未设置</span>
              </div>
              <div v-if="urgentSession(row)" class="mini-progress subject-progress">
                <div class="mp-track">
                  <div class="mp-bar" :class="progressClass(row)" :style="{ width: progressWidth(row) + '%' }"></div>
                </div>
                <span class="mp-text">{{ urgentSession(row).subject_name }}剩{{ urgentSession(row).remaining }}次</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="guardian_name" label="监护人" width="100" />
        <el-table-column prop="guardian_phone" label="联系电话" width="130" />
        <el-table-column label="负责教师" width="130">
          <template #default="{ row }">
            <span v-if="row.teacher_name" class="teacher-cell">
              <span class="teacher-avatar">{{ row.teacher_name[0] }}</span>{{ row.teacher_name }}
            </span>
            <el-tag v-else size="small" type="warning" effect="plain">暂存校区</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <span :class="row.status === '在读' ? 'status-dot is-success' : 'status-dot'">{{ row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="points" label="积分" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.points > 0" class="points-num">★ {{ row.points }}</span>
            <span v-else class="empty-inline">0</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="340" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="$router.push(`/student/${row.id}`)">学习档案</el-button>
            <!-- 学生分开管理：各角色只能给自己负责的学生打卡（校长/校区负责人/教师均可拥有自己的学生） -->
            <template v-if="row.teacher_id === userStore.user?.id">
              <!-- 已打卡：今天打过卡后显示“已打卡”，不再重复打卡；需要补历史日期用“补卡” -->
              <el-tag v-if="row.attended_today" size="small" type="success" effect="plain" class="att-done-tag">已打卡</el-tag>
              <el-button v-else size="small" type="success" link @click="openAttendance(row, false)">打卡</el-button>
              <el-button size="small" type="warning" link class="att-makeup-btn" @click="openAttendance(row, true)">补卡</el-button>
            </template>
            <el-button size="small" link @click="openDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :description="keyword || filterSubjectId ? '没有符合条件的学生' : '暂无学生数据，点击右上角新增'" :image-size="80" />
        </template>
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
        <el-form-item label="所属校区" v-if="userStore.isPrincipal || userStore.isSubPrincipal">
          <el-select v-model="form.campus_id" placeholder="选择校区（可选）" clearable style="width: 100%" @change="onCampusChange">
            <el-option v-for="c in campuses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="canAssign" label="负责教师">
          <el-select v-model="form.teacher_id" placeholder="选择教师（可留空=暂存至校区负责人）" clearable filterable style="width: 100%">
            <el-option
              v-for="t in teacherOptions"
              :key="t.id"
              :label="`${t.name}（${t.username}）${t.role === 'sub_principal' || t.role === 'campus_head' ? '· 校区负责人' : t.role === 'principal' ? '· 校长' : ''}`"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属学科">
          <el-select v-model="form.subject_ids" multiple filterable placeholder="可多选（学科/非学科）" style="width: 100%" @change="onSubjectChange">            <el-option-group v-if="subjectGroups.学科.length" label="学科">
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

    <!-- 批量分配教师对话框（离职交接：把暂存学生分配给其他教师/新账号） -->
    <el-dialog v-model="assignVisible" :title="`分配教师（已选 ${selectedRows.length} 名学生）`" width="480px">
      <el-form label-width="90px">
        <el-form-item label="负责教师">
          <el-select v-model="assignTeacherId" placeholder="选择教师（留空=暂存至校区负责人）" clearable filterable style="width: 100%">
            <el-option
              v-for="t in assignTeacherOptions"
              :key="t.id"
              :label="`${t.name}（${t.username}）${t.campus_name ? ' · ' + t.campus_name : ''}`"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <div class="assign-tip">学生数据（档案、课时、收费、积分等）全部保留，仅变更负责教师。所选学生须与目标教师同校区。</div>
      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleAssign">确认分配</el-button>
      </template>
    </el-dialog>

    <!-- 打卡/补卡对话框（共用；补卡可补打过去任意日期） -->
    <el-dialog v-model="attVisible" :title="attTitle" width="480px">
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
        <el-form-item label="日期">
          <el-date-picker v-model="attForm.date" type="date" value-format="YYYY-MM-DD" placeholder="选择打卡日期（可补卡）" style="width:100%" :clearable="false" />
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
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const keyword = ref('')
const filterSubjectId = ref(null)
const filterCampusId = ref(null)
const onlyUnassigned = ref(false)
const students = ref([])
const subjects = ref([])
const campuses = ref([])
const teacherOptions = ref([])
const selectedRows = ref([])
const assignVisible = ref(false)
const assignTeacherId = ref(null)
const assignTeacherOptions = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const attVisible = ref(false)
const attSaving = ref(false)
const attStudent = ref(null)
const attTitle = ref('考勤打卡')
const attForm = reactive({ subject_id: null, date: todayStr(), status: '正常', remark: '' })

// 校长/校区负责人可分配负责教师
const canAssign = computed(() => userStore.isPrincipal || userStore.isSubPrincipal)

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
  campus_id: null,
  teacher_id: null,
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
    const matchC =
      filterCampusId.value == null ||
      (filterCampusId.value === 0 ? !s.campus_id : s.campus_id === filterCampusId.value)
    const matchU = !onlyUnassigned.value || !s.teacher_id
    return matchK && matchS && matchC && matchU
  })
})

// ===== 纯展示：数据概览（不改变任何业务逻辑） =====
const summary = computed(() => {
  const total = students.value.length
  const active = students.value.filter((s) => s.status === '在读').length
  const now = new Date()
  const ym = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  const thisMonth = students.value.filter((s) => (s.enrollment_date || '').startsWith(ym)).length
  const subjCount = Object.values(subjectGroups.value).reduce((a, b) => a + b.length, 0)
  return {
    total,
    active,
    activeRate: total ? Math.round((active / total) * 100) : 0,
    subjCount,
    thisMonth,
  }
})

// 课时最紧张（剩余最少）的学科，用于进度条展示
function urgentSession(row) {
  const ss = (row.subject_sessions || []).filter((x) => x.remaining !== null && x.remaining !== undefined)
  if (!ss.length) return null
  return ss.reduce((a, b) => (a.remaining < b.remaining ? a : b))
}
function progressWidth(row) {
  const s = urgentSession(row)
  if (!s) return 0
  const total = s.total_sessions || s.remaining
  if (!total) return 0
  return Math.max(0, Math.min(100, Math.round((s.remaining / total) * 100)))
}
function progressClass(row) {
  const w = progressWidth(row)
  return w < 20 ? 'is-danger' : w < 50 ? 'is-warn' : ''
}

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

async function loadCampuses() {
  try {
    campuses.value = await request.get('/campuses/options')
  } catch (e) {
    campuses.value = []
  }
}

// 教师下拉（按校区过滤；校区负责人后端自动限定其管辖校区）
async function loadTeacherOptions(campusId) {
  try {
    const params = campusId ? { campus_id: campusId } : {}
    const list = await request.get('/auth/teachers', { params })
    teacherOptions.value = list.filter((t) => t.is_active && !t.resigned)
  } catch (e) {
    teacherOptions.value = []
  }
}

function onCampusChange() {
  if (canAssign.value) loadTeacherOptions(form.campus_id)
}

function onSelectionChange(rows) {
  selectedRows.value = rows
}

async function openAssignDialog() {
  assignTeacherId.value = null
  try {
    const list = await request.get('/auth/teachers')
    assignTeacherOptions.value = list.filter((t) => t.is_active && !t.resigned)
  } catch (e) {
    assignTeacherOptions.value = []
  }
  assignVisible.value = true
}

async function handleAssign() {
  saving.value = true
  try {
    const res = await request.post('/students/assign', {
      student_ids: selectedRows.value.map((s) => s.id),
      teacher_id: assignTeacherId.value ?? null,
    })
    ElMessage.success(res.detail + (res.teacher_name ? `：${res.teacher_name}` : ''))
    assignVisible.value = false
    selectedRows.value = []
    loadStudents()
  } finally {
    saving.value = false
  }
}

function openDialog(row) {
  Object.assign(form, emptyForm(), row || {})
  // 把已选学科 id 填入 subject_ids
  form.subject_ids = (row?.subjects || []).map((s) => s.id)
  form.teacher_id = row?.teacher_id ?? null
  if (canAssign.value) loadTeacherOptions(form.campus_id)  // 仅校长/校区负责人需负责人下拉；教师自动归属自己
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
        campus_id: form.campus_id || null,
        teacher_id: form.teacher_id ?? null,
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

// 补卡默认日期：昨天（漏打卡最常用场景）
function yesterdayStr() {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${dd}`
}

// isMakeup=true 时走补卡：标题改为「补卡」，日期默认昨天，也可在弹窗里改任意历史日期
function openAttendance(row, isMakeup = false) {
  attStudent.value = row
  attForm.subject_id = null
  attForm.date = isMakeup ? yesterdayStr() : todayStr()
  attForm.status = '正常'
  attForm.remark = ''
  attTitle.value = isMakeup ? `补卡 - ${row.name}` : '考勤打卡'
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
      date: attForm.date || todayStr(),
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
  loadCampuses()
  if (canAssign.value) loadTeacherOptions(null)
  // 从校区管理页跳转带入校区筛选
  if (route.query.campus) {
    filterCampusId.value = Number(route.query.campus) || null
  }
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
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.assign-tip {
  font-size: 12px;
  color: var(--text-muted);
  background: var(--bg);
  border-radius: 8px;
  padding: 8px 12px;
  line-height: 1.5;
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

/* ===== 数据直观化（仅展示层） ===== */
.result-count {
  font-size: 13px;
  color: var(--text-secondary);
  margin-left: 4px;
}
.result-count b {
  color: var(--primary);
  font-size: 15px;
}
.subject-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.subject-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.subject-progress {
  max-width: 200px;
}
.empty-inline {
  color: #c0c4cc;
  font-size: 12px;
}
.teacher-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.campus-cell {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 20px;
  background: var(--primary-lighter);
  color: var(--primary-dark);
  font-size: 12px;
  font-weight: 500;
}
.teacher-avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--primary-lighter);
  color: var(--primary-dark);
  font-size: 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.points-num {
  color: var(--warning);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.att-done-tag {
  margin-right: 8px;
  vertical-align: middle;
}
.att-makeup-btn {
  margin-left: 2px;
}
</style>