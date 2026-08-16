<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <div class="att-head">
          <div class="att-title">
            <span>全体学生考勤日历</span>
            <el-date-picker v-model="month" type="month" value-format="YYYY-MM" placeholder="选择月份" style="width: 140px" @change="loadSummary" />
          </div>
          <div class="cal-legend">
            <span class="leg"><i class="cal-dot is-normal"></i>正常</span>
            <span class="leg"><i class="cal-dot is-late"></i>迟到</span>
            <span class="leg"><i class="cal-dot is-absent"></i>缺勤</span>
            <span class="leg"><i class="cal-dot is-leave"></i>请假</span>
            <span class="leg"><i class="cal-dot is-early"></i>早退</span>
            <span class="leg"><i class="cal-dot is-empty"></i>未记录</span>
          </div>
        </div>
      </template>

      <div v-if="calendarStudents.length" class="cal-scroll">
        <table class="cal-table">
          <thead>
            <tr>
              <th class="cal-name-th">学生</th>
              <th v-for="d in monthDays" :key="d.dayStr" class="cal-day" :class="{ 'is-today': d.isToday }">{{ d.day }}</th>
              <th class="cal-act-th">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in calendarStudents" :key="s.student_id">
              <td class="cal-name">{{ s.student_name }}</td>
              <td v-for="d in monthDays" :key="d.dayStr" class="cal-cell" :title="s.student_name + ' ' + d.dayStr + ' ' + (cellStatus(s, d.dayStr) || '未记录')">
                <i class="cal-dot" :class="'is-' + statusClass(cellStatus(s, d.dayStr))"></i>
              </td>
              <td class="cal-act">
                <el-button size="small" link type="primary" @click="openAttendance(s)">打卡</el-button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <el-empty v-else description="该月暂无学生考勤数据" :image-size="80" />
    </el-card>

    <!-- 分学科打卡 -->
    <el-dialog v-model="attVisible" title="考勤打卡" width="480px">
      <el-form label-width="80px">
        <el-form-item label="学生">
          <span style="font-weight:600">{{ attStudent?.student_name }}</span>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="attForm.subject_id" placeholder="请选择打卡学科" style="width:100%" filterable clearable>
            <el-option
              v-for="ss in attSubjects"
              :key="ss.subject_id"
              :label="`${ss.subject_name}${ss.remaining !== null ? ' (剩' + ss.remaining + '次)' : ''}`"
              :value="ss.subject_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="attForm.date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
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
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const month = ref('')
const calendarStudents = ref([])
const students = ref([]) // 完整学生（含学科课时，用于打卡）
const attVisible = ref(false)
const attSaving = ref(false)
const attStudent = ref(null)
const attForm = reactive({ subject_id: null, date: '', status: '正常', remark: '' })

function todayStr() {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${dd}`
}

const monthDays = computed(() => {
  if (!month.value) return []
  const [y, m] = month.value.split('-').map(Number)
  const days = new Date(y, m, 0).getDate()
  const today = todayStr()
  return Array.from({ length: days }, (_, i) => {
    const day = i + 1
    const dayStr = `${month.value}-${String(day).padStart(2, '0')}`
    return { day, dayStr, isToday: dayStr === today }
  })
})

const attSubjects = computed(() => {
  if (!attStudent.value) return []
  const sid = attStudent.value.student_id
  const full = students.value.find((s) => s.id === sid)
  return full?.subject_sessions || []
})

function cellStatus(student, dayStr) {
  const rec = (student.records || []).find((r) => r.date === dayStr)
  return rec ? rec.status : ''
}

// 考勤状态 → 图标 class
const STATUS_CLASS = { 正常: 'normal', 迟到: 'late', 缺勤: 'absent', 请假: 'leave', 早退: 'early' }
function statusClass(status) {
  return STATUS_CLASS[status] || 'empty'
}

async function loadSummary() {
  try {
    const data = await request.get('/dashboard/attendance-summary', { params: { month: month.value } })
    calendarStudents.value = data.students || []
  } catch (e) {
    calendarStudents.value = []
  }
}

async function loadStudents() {
  try {
    students.value = await request.get('/students')
  } catch (e) {
    students.value = []
  }
}

function openAttendance(s) {
  attStudent.value = s
  attForm.subject_id = null
  attForm.date = todayStr()
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
      student_id: attStudent.value.student_id,
      subject_id: attForm.subject_id,
      date: attForm.date,
      status: attForm.status,
      remark: attForm.remark || null,
    })
    ElMessage.success('打卡成功')
    attVisible.value = false
    loadSummary()
  } finally {
    attSaving.value = false
  }
}

onMounted(() => {
  const d = new Date()
  month.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  loadSummary()
  loadStudents()
})
</script>

<style scoped>
.att-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.att-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}
.cal-legend {
  display: flex;
  gap: 14px;
  font-size: 12px;
  color: #6b7280;
  flex-wrap: wrap;
  align-items: center;
}
.cal-legend .leg {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.cal-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.cal-dot.is-normal { background: #10b981; }
.cal-dot.is-late { background: #f59e0b; }
.cal-dot.is-absent { background: #ef4444; }
.cal-dot.is-leave { background: #3b82f6; }
.cal-dot.is-early { background: #8b5cf6; }
.cal-dot.is-empty { background: #e5e7eb; }
.cal-scroll { overflow-x: auto; }
.cal-table { border-collapse: collapse; width: 100%; min-width: 720px; }
.cal-table th, .cal-table td { border: 1px solid #f0f0f0; text-align: center; }
.cal-table th.cal-name-th, .cal-table td.cal-name {
  text-align: left;
  padding: 6px 10px;
  white-space: nowrap;
  font-size: 13px;
  min-width: 90px;
  font-weight: 500;
  position: sticky;
  left: 0;
  background: #fff;
}
.cal-table th.cal-act-th, .cal-table td.cal-act {
  min-width: 60px;
  position: sticky;
  right: 0;
  background: #fff;
}
.cal-day { font-size: 12px; color: #909399; padding: 4px 2px; min-width: 22px; font-weight: 500; }
.cal-day.is-today { background: #ecfdf5; color: #059669; font-weight: 700; }
.cal-cell { padding: 4px 2px; }
.cal-cell .cal-dot { display: block; margin: 0 auto; }
</style>
