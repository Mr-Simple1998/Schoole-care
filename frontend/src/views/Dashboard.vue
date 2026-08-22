<template>
  <div class="page-container">
    <!-- 账号到期提醒 -->
    <transition name="slide-down">
      <el-alert
        v-if="expireAlert"
        :type="expireAlert.type"
        :title="expireAlert.title"
        :description="expireAlert.description"
        :closable="false"
        show-icon
        class="expire-alert"
      />
    </transition>

    <!-- 统计卡片 -->
    <el-row :gutter="16">
      <el-col :span="(userStore.isPrincipal || userStore.isSubPrincipal) ? 6 : 12" :xs="12" v-for="card in statCards" :key="card.label">
        <div class="stat-card" :style="{ animationDelay: card.delay + 'ms' }">
          <div class="stat-icon" :style="{ background: card.color }">
            <el-icon :size="24"><component :is="card.icon" /></el-icon>
          </div>
          <div class="stat-text">
            <div class="stat-value">
              <span v-if="card.prefix" class="stat-prefix">{{ card.prefix }}</span>
              <span class="counter">{{ animatedValues[card.key] ?? card.value }}</span>
            </div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 新学员一周未交费提醒（醒目横幅 + 明细；记录收费后自动消失） -->
    <transition name="slide-down">
      <div v-if="newStudentReminders.length" class="nsb-wrap mt-16">
        <div class="nsb-banner">
          <div class="nsb-icon">⚠️</div>
          <div class="nsb-text">
            <div class="nsb-title">新学员交费提醒：{{ newStudentReminders.length }} 名学员入学一周仍未交费</div>
            <div class="nsb-desc">入学超过 7 天未记录交费，请及时联系家长交费；记录收费后本提醒将自动消失</div>
          </div>
          <el-button v-if="userStore.isPrincipal || userStore.isSubPrincipal" type="warning" size="small" @click="$router.push('/income')">去收费</el-button>
        </div>
        <el-table :data="newStudentReminders" size="small" stripe class="nsb-table">
          <el-table-column prop="student_name" label="学生" width="110" />
          <el-table-column prop="teacher_name" label="负责教师" width="110" />
          <el-table-column prop="enrollment_date" label="入学时间" width="120" />
          <el-table-column label="已过天数" width="100">
            <template #default="{ row }">
              <el-tag size="small" type="danger">{{ row.days_since }} 天</el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="userStore.isPrincipal || userStore.isSubPrincipal" label="操作" width="90">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="goFee(row)">记收费</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </transition>

    <!-- 缴费到期提醒 -->
    <transition name="slide-down">
      <el-card v-if="feeReminders.length" shadow="never" class="fee-remind-card mt-16">
        <template #header>
          <span class="remind-title">
            <el-icon color="#f59e0b"><AlarmClock /></el-icon>
            缴费到期提醒（提前5天，请通知家长交费）
          </span>
        </template>
        <el-table :data="feeReminders" size="small" stripe>
          <el-table-column prop="student_name" label="学生" width="100" />
          <el-table-column prop="teacher_name" label="负责教师" width="100" />
          <el-table-column prop="fee_type" label="项目" width="80" />
          <el-table-column label="金额" width="90">
            <template #default="{ row }"><span style="color:#f59e0b;font-weight:600">¥{{ row.amount }}</span></template>
          </el-table-column>
          <el-table-column prop="expire_date" label="到期日" width="110" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.days_left < 0 ? 'danger' : 'warning'">
                {{ row.days_left < 0 ? '已到期' : row.days_left + '天后到期' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </transition>

    <!-- 教师上下班打卡（教师端） -->
    <el-card v-if="userStore.isTeacher" shadow="never" class="mt-16">
      <div class="card-title">教师打卡</div>
      <div class="clock-bar">
        <div class="clock-info">
          <span class="clock-time">{{ myClock && myClock.time_in ? '上班 ' + myClock.time_in : '今日未打卡' }}</span>
          <span v-if="myClock && myClock.time_out" class="clock-out">下班 {{ myClock.time_out }}</span>
          <el-tag v-if="myClock" size="small" :type="myClock.status === '正常' ? 'success' : 'warning'">{{ myClock.status }}</el-tag>
        </div>
        <div class="clock-btns">
          <el-date-picker
            v-model="clockDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="打卡日期（可补卡）"
            style="width: 150px; margin-right: 8px"
            :clearable="false"
          />
          <el-button type="primary" :loading="clockLoading" @click="doClock('in')">上班打卡</el-button>
          <el-button type="warning" :loading="clockLoading" @click="doClock('out')">下班打卡</el-button>
        </div>
      </div>
      <div v-if="myClock && (myClock.work_start || myClock.work_end)" class="clock-schedule">
        规定上下班：{{ myClock.work_start || '未设' }} — {{ myClock.work_end || '未设' }}
      </div>
    </el-card>

    <!-- 本月学生考勤（日历·教师/校长/校区负责人：查看自己所负责学生的考勤） -->
    <el-card v-if="(userStore.isTeacher || userStore.isPrincipal || userStore.isSubPrincipal) && attendanceSummary.students && attendanceSummary.students.length" shadow="never" class="mt-16">
      <template #header>
        <div class="att-head">
          <div class="card-title">本月学生考勤（日历）</div>
          <div class="att-actions">
            <!-- 今日打卡进度：全部学生打卡完成后显示「今日全部已打卡」 -->
            <el-tag v-if="todayAttProgress.complete" type="success" effect="dark" size="small">今日全部已打卡 ✓</el-tag>
            <el-tag v-else-if="todayAttProgress.total" type="info" effect="plain" size="small">今日已打卡 {{ todayAttProgress.done }}/{{ todayAttProgress.total }}</el-tag>
            <el-button size="small" type="primary" @click="openDashboardAttendance">给学生打卡</el-button>
            <el-button size="small" type="primary" plain @click="$router.push('/student-attendance')">进入日历</el-button>
          </div>
        </div>
      </template>
      <div class="cal-legend">
        <span class="leg"><i class="cal-dot is-normal"></i>正常</span>
        <span class="leg"><i class="cal-dot is-late"></i>迟到</span>
        <span class="leg"><i class="cal-dot is-absent"></i>缺勤</span>
        <span class="leg"><i class="cal-dot is-leave"></i>请假</span>
        <span class="leg"><i class="cal-dot is-early"></i>早退</span>
        <span class="leg"><i class="cal-dot is-empty"></i>未记录</span>
      </div>
      <div class="cal-scroll">
        <table class="cal-table">
          <thead>
            <tr>
              <th class="cal-name-th">学生</th>
              <th v-for="d in monthDays" :key="d.dayStr" class="cal-day" :class="{ 'is-today': d.isToday }">{{ d.day }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in attPageStudents" :key="s.student_id">
              <td class="cal-name">{{ s.student_name }}</td>
              <td v-for="d in monthDays" :key="d.dayStr" class="cal-cell" :title="s.student_name + ' ' + d.dayStr + ' ' + (cellStatus(s, d.dayStr) || '未记录')">
                <i class="cal-dot" :class="'is-' + statusClass(cellStatus(s, d.dayStr))"></i>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="attPageTotal > ATT_PAGE_SIZE" class="att-pager">
        <el-pagination
          layout="prev, pager, next"
          :total="attPageTotal"
          :page-size="ATT_PAGE_SIZE"
          :current-page="attPage"
          @current-change="attPageChange"
        />
      </div>
    </el-card>

    <!-- 本月教师考勤汇总（仅校区负责人） -->
    <el-card v-if="userStore.isSubPrincipal && attendanceSummary.teachers && attendanceSummary.teachers.length" shadow="never" class="mt-16">
      <template #header>
        <div class="card-title">本月教师考勤汇总</div>
      </template>
      <el-table :data="attendanceSummary.teachers" size="small" stripe>
        <el-table-column label="教师" min-width="120">
          <template #default="{ row }">
            {{ row.teacher_name }}<span v-if="row.work_start" class="ws">（{{ row.work_start }}-{{ row.work_end || '未设' }}）</span>
          </template>
        </el-table-column>
        <el-table-column prop="normal" label="正常" width="70" align="center" />
        <el-table-column prop="late" label="迟到" width="70" align="center" />
        <el-table-column prop="early" label="早退" width="70" align="center" />
        <el-table-column prop="absent" label="缺勤" width="70" align="center" />
        <el-table-column label="标记" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.late || row.absent" type="warning" size="small">迟到{{ row.late }} · 缺勤{{ row.absent }}</el-tag>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 图表区（收入趋势仅校长/校区负责人可见本校区收入） -->
    <el-row v-if="userStore.isPrincipal || userStore.isSubPrincipal" :gutter="16" class="mt-16">
      <el-col :span="16" :xs="24">
        <el-card shadow="never">
          <div class="card-title">近14天收入趋势</div>
          <div ref="incomeChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="8" :xs="24">
        <el-card shadow="never">
          <div class="card-title">学科 / 非学科人数</div>
          <div ref="catChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 学科分布 / 快捷入口 -->
    <el-row :gutter="16" class="mt-16">
      <el-col :span="16" :xs="24">
        <el-card shadow="never">
          <div class="card-title">学科学生分布</div>
          <div ref="subjectChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="8" :xs="24">
        <el-card shadow="never">
          <div class="card-title">功能快捷入口</div>
          <div class="quick-links">
            <div class="quick-link" v-for="item in quickLinks" :key="item.path" @click="$router.push(item.path)">
              <div class="quick-link-icon" :style="{ background: item.color }">
                <el-icon :size="22" color="#fff"><component :is="item.icon" /></el-icon>
              </div>
              <span>{{ item.label }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 教师：学科/非学科人数 -->
    <el-row v-if="userStore.isTeacher" :gutter="16" class="mt-16">
      <el-col :span="12" :xs="24">
        <el-card shadow="never">
          <div class="card-title">学科 / 非学科人数</div>
          <div ref="catChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 给学生分学科打卡 -->
    <el-dialog v-model="attVisible" title="给学生打卡" width="480px">
      <el-form label-width="80px">
        <el-form-item label="学生">
          <el-select v-model="attStudentId" placeholder="选择学生" filterable style="width:100%" @change="onAttStudentChange">
            <!-- 已打卡的学生在选项中标记，便于一眼看出哪些还没打卡 -->
            <el-option
              v-for="s in myStudents"
              :key="s.id"
              :label="s.attended_today ? s.name + '（已打卡）' : s.name"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="attForm.subject_id" placeholder="请选择打卡学科" filterable style="width:100%">
            <el-option
              v-for="ss in attSubjects"
              :key="ss.subject_id"
              :label="`${ss.subject_name}${ss.remaining !== null ? ' (剩' + ss.remaining + '次)' : ''}`"
              :value="ss.subject_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="attForm.date" type="date" value-format="YYYY-MM-DD" placeholder="打卡日期（可补卡）" style="width:100%" />
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
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'
import { AlarmClock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const router = useRouter()
const incomeChartRef = ref()
const subjectChartRef = ref()
const catChartRef = ref()
let chart = null
let subjectChart = null
let catChart = null

const overview = ref({})
const subjectStats = ref({ subject_counts: [], category_counts: {}, total_students: 0 })
const animatedValues = reactive({})
const attendanceSummary = ref({})
const attPage = ref(1)
const ATT_PAGE_SIZE = 10
const attPageStudents = computed(() => {
  const all = attendanceSummary.value.students || []
  const start = (attPage.value - 1) * ATT_PAGE_SIZE
  return all.slice(start, start + ATT_PAGE_SIZE)
})
const attPageTotal = computed(() => (attendanceSummary.value.students || []).length)
function attPageChange(p) {
  attPage.value = p
}
const myClock = ref(null)
const clockLoading = ref(false)
const clockDate = ref(todayStr())
const myStudents = ref([])
const attVisible = ref(false)
const attSaving = ref(false)
const attStudentId = ref(null)
const attForm = reactive({ subject_id: null, date: '', status: '正常', remark: '' })

const expireAlert = computed(() => {
  const e = overview.value.org_expire
  if (!e || !e.expire_date) return null
  if (e.status === 'expired') {
    return {
      type: 'error',
      title: '机构账号已到期',
      description: `「${e.name}」账号已于 ${e.expire_date} 到期，请联系平台管理员续费后再正常使用。`,
    }
  }
  if (e.status === 'expiring') {
    return {
      type: 'warning',
      title: '机构账号即将到期',
      description: `「${e.name}」账号将于 ${e.expire_date} 到期，剩余 ${e.days_left} 天，请及时续费以免影响使用。`,
    }
  }
  return null
})

const feeReminders = computed(() => overview.value.fee_expire_reminders || [])
const newStudentReminders = computed(() => overview.value.new_student_fee_reminders || [])

// 去收费：跳转收费管理页并自动打开收费弹窗、预选该学生；记录收费后工作台提醒自动消失
function goFee(row) {
  router.push({ path: '/income', query: { fee_student: row.student_id } })
}

const statCards = computed(() => {
  const cards = [
    { key: 'total_students', label: '在读学生', value: overview.value.total_students ?? 0, icon: 'User', color: 'linear-gradient(135deg, #3b82f6, #6366f1)', delay: 0 },
    { key: 'today_attendance', label: '今日考勤', value: overview.value.today_attendance ?? 0, icon: 'Calendar', color: 'linear-gradient(135deg, #ef4444, #f97316)', delay: 150 },
  ]
  if (userStore.isPrincipal || userStore.isSubPrincipal) {
    cards.splice(1, 0,
      { key: 'month_income', label: '本月收入(元)', value: overview.value.month_income ?? 0, icon: 'Money', color: 'linear-gradient(135deg, #10b981, #059669)', prefix: '¥', delay: 50 },
      { key: 'total_unpaid', label: '待缴欠费(元)', value: overview.value.total_unpaid ?? 0, icon: 'Warning', color: 'linear-gradient(135deg, #f59e0b, #d97706)', prefix: '¥', delay: 100 },
    )
  }
  return cards
})

const quickLinks = computed(() => {
  const links = [
    { label: '学生管理', path: '/students', icon: 'User', color: '#3b82f6' },
    { label: '积分奖励', path: '/points', icon: 'Trophy', color: '#f59e0b' },
  ]
  if (userStore.isPrincipal || userStore.isSubPrincipal) {
    links.push({ label: '收费管理', path: '/income', icon: 'Money', color: '#10b981' })
    links.push({ label: '教师管理', path: '/teachers', icon: 'Avatar', color: '#ef4444' })
  }
  if (userStore.isPrincipal) {
    links.push({ label: '学科管理', path: '/subjects', icon: 'Grid', color: '#8b5cf6' })
  }
  return links
})

// 数字滚动动画
function animateValue(key, target) {
  if (target === 0) { animatedValues[key] = 0; return }
  const start = 0
  const duration = 800
  const startTime = performance.now()
  function step(now) {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedValues[key] = Math.round(start + (target - start) * eased)
    if (progress < 1) requestAnimationFrame(step)
    else animatedValues[key] = target
  }
  requestAnimationFrame(step)
}

async function loadData() {
  overview.value = await request.get('/dashboard/overview')
  // 触发数字动画
  statCards.value.forEach(card => animateValue(card.key, card.value))
  if (userStore.isPrincipal || userStore.isSubPrincipal) {
    const income = await request.get('/dashboard/recent-income')
    renderIncomeChart(income)
  }
  subjectStats.value = await request.get('/subjects/stats')
  renderSubjectCharts()
  // 月度考勤汇总（教师/校长/校区负责人：查看自己所负责学生的考勤）+ 教师今日打卡
  try {
    attendanceSummary.value = await request.get('/dashboard/attendance-summary')
    attPage.value = 1
    if (userStore.isTeacher || userStore.isPrincipal || userStore.isSubPrincipal) {
      myStudents.value = await request.get('/students')
    }
    if (userStore.isTeacher) {
      const list = await request.get('/learning/teacher-attendance')
      const today = todayStr()
      myClock.value = list.find((x) => x.date === today) || null
    }
  } catch (e) {
    attendanceSummary.value = {}
  }
}

function todayStr() {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${dd}`
}

async function doClock(action) {
  clockLoading.value = true
  try {
    const payload = { action }
    if (clockDate.value) payload.date = clockDate.value
    myClock.value = await request.post('/learning/teacher-attendance', payload)
    ElMessage.success(action === 'in' ? '上班打卡成功' : '下班打卡成功')
  } finally {
    clockLoading.value = false
  }
}

// 日历：当月各天（学生考勤日历展示用）
const monthDays = computed(() => {
  const month = attendanceSummary.value.month || todayStr().slice(0, 7)
  const [y, m] = month.split('-').map(Number)
  const days = new Date(y, m, 0).getDate()
  const today = todayStr()
  return Array.from({ length: days }, (_, i) => {
    const day = i + 1
    const dayStr = `${month}-${String(day).padStart(2, '0')}`
    return { day, dayStr, isToday: dayStr === today }
  })
})

function cellStatus(student, dayStr) {
  const rec = (student.records || []).find((r) => r.date === dayStr)
  return rec ? rec.status : ''
}

// 今天是否已打卡（优先看当月记录，跨月时回退到 /students 的 attended_today）
function checkedInToday(s) {
  if (cellStatus(s, todayStr())) return true
  const full = myStudents.value.find((x) => x.id === s.student_id)
  return full ? !!full.attended_today : false
}

// 今日打卡进度：全部学生打卡完成后 complete=true（显示「今日全部已打卡」）
const todayAttProgress = computed(() => {
  const list = attendanceSummary.value.students || []
  const total = list.length
  if (!total) return { total: 0, done: 0, complete: false }
  const done = list.filter((s) => checkedInToday(s)).length
  return { total, done, complete: done >= total }
})

// 考勤状态 → 图标 class（正常/迟到/缺勤/请假/早退/未记录）
const STATUS_CLASS = { 正常: 'normal', 迟到: 'late', 缺勤: 'absent', 请假: 'leave', 早退: 'early' }
function statusClass(status) {
  return STATUS_CLASS[status] || 'empty'
}

// 打卡：当前选中学生的学科课时（供学科下拉）
const attSubjects = computed(() => {
  const s = myStudents.value.find((x) => x.id === attStudentId.value)
  return s?.subject_sessions || []
})

function openDashboardAttendance() {
  attStudentId.value = null
  attForm.subject_id = null
  attForm.date = todayStr()
  attForm.status = '正常'
  attForm.remark = ''
  attVisible.value = true
}

function onAttStudentChange() {
  attForm.subject_id = null
}

async function saveAttendance() {
  if (!attStudentId.value) {
    ElMessage.warning('请选择学生')
    return
  }
  if (!attForm.subject_id) {
    ElMessage.warning('请选择打卡学科')
    return
  }
  attSaving.value = true
  try {
    await request.post('/learning/attendance', {
      student_id: attStudentId.value,
      subject_id: attForm.subject_id,
      date: attForm.date,
      status: attForm.status,
      remark: attForm.remark || null,
    })
    ElMessage.success('打卡成功')
    attVisible.value = false
    // 刷新日历，与学生管理数据保持一致
    attendanceSummary.value = await request.get('/dashboard/attendance-summary')
  } finally {
    attSaving.value = false
  }
}

function renderIncomeChart(data) {
  if (!chart) chart = echarts.init(incomeChartRef.value)
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#e5e7eb',
      textStyle: { color: '#111827', fontSize: 13 },
      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
    },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.date.slice(5)),
      axisLabel: { fontSize: 11, color: '#9ca3af' },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f6' } },
      axisLabel: { fontSize: 11, color: '#9ca3af' },
    },
    series: [{
      name: '收入',
      type: 'line',
      smooth: true,
      data: data.map((d) => d.amount),
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(16,185,129,0.2)' },
          { offset: 1, color: 'rgba(16,185,129,0)' },
        ]),
      },
      lineStyle: { color: '#10b981', width: 2.5 },
      itemStyle: { color: '#10b981' },
      symbol: 'circle',
      symbolSize: 6,
    }],
  })
}

function renderSubjectCharts() {
  const rows = subjectStats.value.subject_counts || []
  const distData = rows.filter((r) => r.count > 0).map((r) => ({ name: r.name, value: r.count }))
  if (distData.length && !subjectChart) subjectChart = echarts.init(subjectChartRef.value)
  if (subjectChart) {
    subjectChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)', backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#111827' } },
      color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899'],
      series: [{
        type: 'pie',
        radius: ['0', '60%'],
        center: ['50%', '50%'],
        label: { formatter: '{b}\n{c} 人', fontSize: 12 },
        emphasis: { scaleSize: 8 },
        data: distData,
      }],
    })
  }
  const cats = subjectStats.value.category_counts || {}
  const catData = Object.entries(cats).map(([name, value]) => ({ name, value }))
  if (catData.length && !catChart) catChart = echarts.init(catChartRef.value)
  if (catChart) {
    catChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)', backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#111827' } },
      color: ['#3b82f6', '#f59e0b'],
      series: [{
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['50%', '50%'],
        label: { formatter: '{b}\n{c} 人', fontSize: 12 },
        emphasis: { scaleSize: 8 },
        data: catData,
      }],
    })
  }
}

function handleResize() {
  chart && chart.resize()
  subjectChart && subjectChart.resize()
  catChart && catChart.resize()
}

onMounted(async () => {
  await loadData()
  nextTick(() => window.addEventListener('resize', handleResize))
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart && chart.dispose()
  subjectChart && subjectChart.dispose()
  catChart && catChart.dispose()
})
</script>

<style scoped>
.expire-alert {
  margin-bottom: 16px;
}
.fee-remind-card {
  border-color: #fde68a;
}
.remind-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #f59e0b;
  font-weight: 600;
}
/* 新学员交费提醒（醒目横幅） */
.nsb-wrap {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #fecaca;
  background: #fff;
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.12);
}
.nsb-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
  flex-wrap: wrap;
}
.nsb-icon {
  font-size: 26px;
  line-height: 1;
}
.nsb-text {
  flex: 1;
  min-width: 200px;
}
.nsb-title {
  font-size: 15px;
  font-weight: 700;
}
.nsb-desc {
  font-size: 12px;
  opacity: 0.92;
  margin-top: 3px;
}
.nsb-table {
  background: #fff;
}
.nsb-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
.chart-box {
  height: 320px;
}
.stat-prefix {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-right: 2px;
}
.stat-text {
  min-width: 0;
}
.stat-card {
  animation: cardSlideUp 0.5s ease-out both;
}
@keyframes cardSlideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.quick-links {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.quick-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 12px;
  border-radius: 12px;
  background: var(--bg);
  cursor: pointer;
  transition: all 0.25s;
  border: 1px solid var(--border-light);
}
.quick-link:hover {
  background: var(--primary-lighter);
  border-color: var(--primary-light);
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.1);
}
.quick-link-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.25s;
}
.quick-link:hover .quick-link-icon {
  transform: scale(1.1);
}
.quick-link span {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}
.clock-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.clock-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.clock-time {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}
.clock-out {
  font-size: 13px;
  color: var(--text-secondary);
}
.clock-btns {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}
.clock-schedule {
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-muted);
}
.ws {
  color: var(--text-muted);
  font-size: 12px;
  margin-left: 4px;
}
:deep(.el-card__header) .card-title {
  margin-bottom: 0;
}
.att-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}
.att-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.cal-legend {
  display: flex;
  gap: 14px;
  margin-bottom: 10px;
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
.cal-table { border-collapse: collapse; width: 100%; min-width: 640px; }
.cal-table th, .cal-table td { border: 1px solid #f0f0f0; text-align: center; }
.cal-table th.cal-name-th, .cal-table td.cal-name {
  text-align: left;
  padding: 6px 10px;
  white-space: nowrap;
  font-size: 13px;
  min-width: 90px;
  font-weight: 500;
}
.cal-day { font-size: 12px; color: #909399; padding: 4px 2px; min-width: 22px; font-weight: 500; }
.cal-day.is-today { background: #ecfdf5; color: #059669; font-weight: 700; }
.cal-cell { padding: 4px 2px; }
.cal-cell .cal-dot { display: block; margin: 0 auto; }
.att-pager { display: flex; justify-content: flex-end; margin-top: 12px; }
/* 移动端：打卡操作区改为纵向堆叠 */
@media (max-width: 767px) {
  .clock-bar {
    flex-direction: column;
    align-items: flex-start;
  }
  .clock-btns {
    flex-wrap: wrap;
  }
  .chart-box {
    height: 240px;
  }
}
/* transitions */
.slide-down-enter-active { transition: all 0.4s ease-out; }
.slide-down-leave-active { transition: all 0.3s ease-in; }
.slide-down-enter-from { opacity: 0; transform: translateY(-20px); }
.slide-down-leave-to { opacity: 0; transform: translateY(-10px); }
</style>