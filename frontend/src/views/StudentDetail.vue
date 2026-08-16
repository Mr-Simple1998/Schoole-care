<template>
  <div class="page-container" v-loading="loading">
    <!-- 学生信息头 -->
    <el-card shadow="never" style="margin-bottom:16px">
      <div class="student-header">
        <div class="student-avatar">{{ student.name?.[0] }}</div>
        <div class="student-info">
          <div class="student-name">{{ student.name }} <el-tag size="small" effect="plain">{{ student.student_no }}</el-tag></div>
          <div class="student-meta">
            <span v-if="student.school">{{ student.school }}</span>
            <span>{{ student.grade || '未填年级' }}</span>
            <span v-if="student.enrollment_date">入学：{{ student.enrollment_date }}</span>
            <span>积分：<b style="color:#e6a23c">{{ student.points }} 分</b></span>
            <span>状态：<el-tag size="small" :type="student.status === '在读' ? 'success' : 'info'">{{ student.status }}</el-tag></span>
          </div>
          <div class="student-subjects" v-if="student.subjects && student.subjects.length">
            学科：
            <el-tag
              v-for="s in student.subjects"
              :key="s.id"
              size="small"
              :type="s.category === '学科' ? 'primary' : 'warning'"
              style="margin-right: 4px"
            >{{ s.name }}</el-tag>
          </div>
        </div>
        <el-button @click="$router.push('/students')" style="margin-left:auto">返回</el-button>
      </div>
    </el-card>

    <!-- 数据概览 -->
    <div class="mini-stats mb-16">
      <div class="mini-stat">
        <div class="ms-label">⭐ 积分</div>
        <div class="ms-value" style="color: var(--warning)">{{ student.points ?? 0 }}</div>
      </div>
      <div class="mini-stat">
        <div class="ms-label">📋 出勤率</div>
        <div class="ms-value" style="color: var(--success)">{{ attStats.attendance_rate }}%</div>
        <div class="ms-sub">{{ attStats.total }} 条考勤记录</div>
      </div>
      <div class="mini-stat">
        <div class="ms-label">📝 成绩记录</div>
        <div class="ms-value" style="color: var(--info)">{{ scores.length }}</div>
      </div>
      <div class="mini-stat">
        <div class="ms-label">📖 作业 / 🎓 表现</div>
        <div class="ms-value">{{ homework.length }} / {{ performances.length }}</div>
      </div>
      <div class="mini-stat">
        <div class="ms-label">⏳ 剩余课时</div>
        <div class="ms-value" :style="{ color: totalRemaining > 0 ? 'var(--success)' : 'var(--danger)' }">{{ totalRemaining }}</div>
        <div class="ms-sub">{{ subjectSessionCount }} 门计次学科</div>
      </div>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 成绩 -->
      <el-tab-pane label="学习成绩" name="scores">
        <div class="tab-toolbar">
          <el-button type="primary" size="small" :icon="Plus" @click="openScore">记录成绩</el-button>
          <el-button size="small" :icon="Download" @click="exportTranscript">导出成绩单(CSV)</el-button>
        </div>
        <el-table :data="scores" size="small" stripe>
          <el-table-column prop="subject" label="科目" width="90" />
          <el-table-column prop="exam_type" label="考试类型" width="100" />
          <el-table-column prop="score" label="得分" width="90">
            <template #default="{ row }">
              <b :style="{ color: scoreColor(row.score, row.full_score) }">{{ row.score }}</b> / {{ row.full_score }}
            </template>
          </el-table-column>
          <el-table-column prop="exam_date" label="日期" width="110" />
          <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        </el-table>
        <div v-if="Object.keys(trend).length" class="trend-box">
          <div class="card-title" style="margin-top:16px">成绩趋势</div>
          <div ref="trendChartRef" class="trend-chart"></div>
        </div>
      </el-tab-pane>

      <!-- 考勤 -->
      <el-tab-pane label="考勤打卡" name="attendance">
        <div class="tab-toolbar">
          <!-- 学生分开管理：各角色只能给自己负责的学生打卡 -->
          <el-button v-if="canCheckIn" type="primary" size="small" :icon="Plus" @click="openAttendance">打卡</el-button>
        </div>
        <!-- 学科课时概览 -->
        <div v-if="student.subject_sessions && student.subject_sessions.length" class="session-overview">
          <div class="card-title">课时核销情况</div>
          <div class="session-grid">
            <div v-for="ss in student.subject_sessions" :key="ss.subject_id" class="session-card">
              <div class="session-subject-name">{{ ss.subject_name }}</div>
              <div v-if="ss.total_sessions !== null" class="session-progress">
                <el-progress
                  :percentage="ss.total_sessions > 0 ? Math.round(ss.used_sessions / ss.total_sessions * 100) : 0"
                  :color="ss.remaining > 0 ? '#10b981' : '#f56c6c'"
                  :stroke-width="14"
                >
                  <span class="progress-text">
                    已核 <b>{{ ss.used_sessions }}</b> / <b>{{ ss.total_sessions }}</b> 次
                    <span v-if="ss.remaining > 0" style="color:#10b981">（剩 {{ ss.remaining }} 次）</span>
                    <span v-else style="color:#f56c6c">（已用完）</span>
                  </span>
                </el-progress>
              </div>
              <div v-else class="session-unlimited">
                <span v-if="ss.expire_date" style="color:#606266">
                  <span v-if="ss.duration_value && ss.duration_unit">{{ ss.duration_value }}{{ ss.duration_unit }}到期：</span>
                  <b :style="{ color: getExpireColor(ss.expire_date) }">{{ ss.expire_date }}</b>
                  <el-tag v-if="getExpireTag(ss.expire_date)" size="small" :type="getExpireTag(ss.expire_date).type" style="margin-left:6px">
                    {{ getExpireTag(ss.expire_date).text }}
                  </el-tag>
                </span>
                <span v-if="!ss.expire_date && ss.duration_value && ss.duration_unit" style="color:#10b981">
                  时长 {{ ss.duration_value }}{{ ss.duration_unit }}（首次打卡后开始计时）
                </span>
                <span v-if="!ss.expire_date && !(ss.duration_value && ss.duration_unit)" style="color:#909399">按到期时间计算（未设置时长）</span>
              </div>
            </div>
          </div>
        </div>
        <!-- 考勤统计报表 -->
        <el-row :gutter="16" v-if="attStats.total" style="margin-bottom:16px">
          <el-col :span="8">
            <el-card shadow="never">
              <div class="stat-title">出勤率</div>
              <div class="stat-big">{{ attStats.attendance_rate }}%</div>
              <div class="stat-sub">共 {{ attStats.total }} 条考勤记录</div>
            </el-card>
          </el-col>
          <el-col :span="16">
            <el-card shadow="never">
              <div class="stat-title">考勤构成</div>
              <div ref="attChartRef" class="att-chart"></div>
            </el-card>
          </el-col>
        </el-row>
        <el-table :data="attendances" size="small" stripe>
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="subject_name" label="学科" width="80">
            <template #default="{ row }">
              <span v-if="row.subject_name">{{ row.subject_name }}</span>
              <span v-else style="color:#c0c4cc">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="attType(row.status)">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" />
        </el-table>
      </el-tab-pane>

      <!-- 作业 -->
      <el-tab-pane label="作业管理" name="homework">
        <div class="tab-toolbar">
          <el-button type="primary" size="small" :icon="Plus" @click="openHomework">布置作业</el-button>
        </div>
        <el-table :data="homework" size="small" stripe>
          <el-table-column prop="subject" label="科目" width="90" />
          <el-table-column prop="content" label="作业内容" show-overflow-tooltip />
          <el-table-column prop="assign_date" label="日期" width="110" />
          <el-table-column prop="complete_status" label="完成情况" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="hwType(row.complete_status)">{{ row.complete_status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="score" label="评分" width="70" />
        </el-table>
      </el-tab-pane>

      <!-- 课堂表现 -->
      <el-tab-pane label="课堂表现" name="performance">
        <div class="tab-toolbar">
          <el-button type="primary" size="small" :icon="Plus" @click="openPerf">记录表现</el-button>
        </div>
        <el-table :data="performances" size="small" stripe>
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="performance_type" label="类型" width="100" />
          <el-table-column prop="rating" label="评分" width="180">
            <template #default="{ row }">
              <el-rate :model-value="row.rating" disabled size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="comment" label="评价" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 各对话框 -->
    <el-dialog v-model="scoreVisible" title="记录成绩" width="480px">
      <el-form :model="scoreForm" label-width="80px">
        <el-form-item label="科目"><el-input v-model="scoreForm.subject" placeholder="语文/数学/英语" /></el-form-item>
        <el-form-item label="考试类型">
          <el-select v-model="scoreForm.exam_type" style="width:100%">
            <el-option label="平时考" value="平时考" /><el-option label="期中" value="期中" /><el-option label="期末" value="期末" />
          </el-select>
        </el-form-item>
        <el-form-item label="得分"><el-input-number v-model="scoreForm.score" :min="0" :max="100" style="width:100%" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="scoreForm.remark" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scoreVisible = false">取消</el-button>
        <el-button type="primary" @click="saveScore">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="attVisible" title="考勤打卡" width="480px">
      <el-form :model="attForm" label-width="80px">
        <el-form-item label="学科">
          <el-select v-model="attForm.subject_id" placeholder="请选择打卡学科" style="width:100%" filterable clearable>
            <el-option
              v-for="ss in student.subject_sessions"
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
        <el-button type="primary" @click="saveAttendance">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="hwVisible" title="布置作业" width="480px">
      <el-form :model="hwForm" label-width="80px">
        <el-form-item label="科目"><el-input v-model="hwForm.subject" placeholder="语文/数学/英语" /></el-form-item>
        <el-form-item label="作业内容"><el-input v-model="hwForm.content" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="完成情况">
          <el-select v-model="hwForm.complete_status" style="width:100%">
            <el-option label="未完成" value="未完成" /><el-option label="已完成" value="已完成" /><el-option label="优秀" value="优秀" />
          </el-select>
        </el-form-item>
        <el-form-item label="评分"><el-input-number v-model="hwForm.score" :min="0" :max="100" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="hwVisible = false">取消</el-button>
        <el-button type="primary" @click="saveHomework">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="perfVisible" title="记录课堂表现" width="480px">
      <el-form :model="perfForm" label-width="80px">
        <el-form-item label="类型">
          <el-select v-model="perfForm.performance_type" style="width:100%">
            <el-option label="纪律" value="纪律" /><el-option label="参与度" value="参与度" />
            <el-option label="积极性" value="积极性" /><el-option label="态度" value="态度" />
          </el-select>
        </el-form-item>
        <el-form-item label="评分"><el-rate v-model="perfForm.rating" /></el-form-item>
        <el-form-item label="评价"><el-input v-model="perfForm.comment" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="perfVisible = false">取消</el-button>
        <el-button type="primary" @click="savePerf">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const studentId = route.params.id
const loading = ref(false)
const activeTab = ref('scores')

const student = ref({})
const scores = ref([])
const trend = ref({})
const attendances = ref([])
const homework = ref([])
const performances = ref([])
const attStats = ref({ total: 0, attendance_rate: 0, status_counts: {} })
const sessions = ref(null)

const scoreVisible = ref(false)
const attVisible = ref(false)
const hwVisible = ref(false)
const perfVisible = ref(false)

const scoreForm = reactive({ subject: '', exam_type: '平时考', score: 0, exam_date: '', remark: '' })
const attForm = reactive({ date: '', subject_id: null, status: '正常', time_in: '', time_out: '', remark: '' })
const hwForm = reactive({ subject: '', content: '', assign_date: '', complete_status: '未完成', score: null })
const perfForm = reactive({ performance_type: '纪律', rating: 3, comment: '', date: '' })

const trendChartRef = ref()
const attChartRef = ref()
let trendChart = null
let attChart = null

function attType(s) {
  return { '正常': 'success', '迟到': 'warning', '早退': 'warning', '请假': 'info', '缺勤': 'danger' }[s] || 'info'
}
function hwType(s) {
  return { '优秀': 'success', '已完成': 'primary', '未完成': 'danger' }[s] || 'info'
}

// ===== 纯展示：概览统计与成绩配色（不改变任何业务逻辑） =====
// 是否可给该学生打卡：总校长/校区负责人/教师的学生分开，只能给自己负责的学生打卡
const canCheckIn = computed(() => student.value.teacher_id === userStore.user?.id)
const totalRemaining = computed(() =>
  (student.value.subject_sessions || []).reduce((a, s) => a + (s.remaining ?? 0), 0)
)
const subjectSessionCount = computed(() =>
  (student.value.subject_sessions || []).filter((s) => s.remaining !== null && s.remaining !== undefined).length
)
function scoreColor(score, full) {
  const p = full ? score / full : score / 100
  if (p >= 0.9) return '#10b981'
  if (p >= 0.6) return '#f59e0b'
  return '#ef4444'
}

// 到期时间颜色和标签
function getExpireColor(expireDate) {
  if (!expireDate) return '#606266'
  const days = Math.ceil((new Date(expireDate) - new Date()) / (1000 * 60 * 60 * 24))
  if (days < 0) return '#f56c6c'
  if (days <= 5) return '#f59e0b'
  return '#10b981'
}
function getExpireTag(expireDate) {
  if (!expireDate) return null
  const days = Math.ceil((new Date(expireDate) - new Date()) / (1000 * 60 * 60 * 24))
  if (days < 0) return { type: 'danger', text: '已到期' }
  if (days <= 5) return { type: 'warning', text: days + '天后到期' }
  if (days <= 30) return { type: 'info', text: days + '天后到期' }
  return null
}

// 根据电脑本地时间生成当日日期（YYYY-MM-DD）
function todayStr() {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${dd}`
}

async function loadAll() {
  loading.value = true
  try {
    const [st, sc, at, hw, pf] = await Promise.all([
      request.get(`/students/${studentId}`),
      request.get(`/learning/scores?student_id=${studentId}`),
      request.get(`/learning/attendance?student_id=${studentId}`),
      request.get(`/learning/homework?student_id=${studentId}`),
      request.get(`/learning/performances?student_id=${studentId}`),
    ])
    student.value = st
    scores.value = sc
    attendances.value = at
    homework.value = hw
    performances.value = pf
    trend.value = await request.get(`/learning/scores/trend/${studentId}`)
    attStats.value = await request.get(`/learning/attendance/stats?student_id=${studentId}`)
    try { sessions.value = await request.get(`/income/students/${studentId}/sessions`) } catch { sessions.value = null }
  } finally {
    loading.value = false
  }
}

async function exportTranscript() {
  try {
    const blob = await request.get(`/learning/transcript/${studentId}/export`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${student.value.name || '学生'}_成绩单.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('成绩单已导出')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

function openScore() { Object.assign(scoreForm, { subject: '', exam_type: '平时考', score: 0, exam_date: '', remark: '' }); scoreVisible.value = true }
function openAttendance() {
  const today = todayStr()
  attForm.date = today
  attForm.subject_id = null
  attForm.status = '正常'
  attForm.remark = ''
  attVisible.value = true
}
function openHomework() { Object.assign(hwForm, { subject: '', content: '', assign_date: '', complete_status: '未完成', score: null }); hwVisible.value = true }
function openPerf() { Object.assign(perfForm, { performance_type: '纪律', rating: 3, comment: '', date: '' }); perfVisible.value = true }

async function saveScore() {
  await request.post('/learning/scores', { ...scoreForm, exam_date: todayStr(), student_id: +studentId })
  ElMessage.success('成绩已保存'); scoreVisible.value = false; loadAll()
}
async function saveAttendance() {
  await request.post('/learning/attendance', {
    student_id: +studentId,
    subject_id: attForm.subject_id || null,
    date: attForm.date,
    status: attForm.status,
    remark: attForm.remark,
  })
  ElMessage.success('打卡成功'); attVisible.value = false
  await loadAll()
  // 提示核销信息
  if (student.value.subject_sessions) {
    const ss = student.value.subject_sessions.find(s => s.subject_id === attForm.subject_id)
    if (ss && ss.remaining !== null) {
      ElMessage.info(`「${ss.subject_name}」剩余课时：${ss.remaining} 次`)
    }
  }
}
async function saveHomework() {
  await request.post('/learning/homework', { ...hwForm, assign_date: todayStr(), student_id: +studentId })
  ElMessage.success('作业已保存'); hwVisible.value = false; loadAll()
}
async function savePerf() {
  await request.post('/learning/performances', { ...perfForm, date: todayStr(), student_id: +studentId })
  ElMessage.success('表现已记录'); perfVisible.value = false; loadAll()
}

function renderTrend() {
  const subjects = Object.keys(trend.value)
  if (!subjects.length) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: subjects },
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category' },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: subjects.map((sub) => ({
      name: sub,
      type: 'line',
      smooth: true,
      data: trend.value[sub].map((t) => t.score),
    })),
  })
}

function renderAttChart() {
  const counts = attStats.value.status_counts || {}
  const data = Object.entries(counts).map(([name, value]) => ({ name, value }))
  if (!data.length) return
  const colorMap = { 正常: '#67c23a', 迟到: '#e6a23c', 早退: '#e6a23c', 请假: '#909399', 缺勤: '#f56c6c' }
  if (!attChart) attChart = echarts.init(attChartRef.value)
  attChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 次 ({d}%)' },
    legend: { bottom: 0 },
    color: data.map((d) => colorMap[d.name] || '#409eff'),
    series: [{
      type: 'pie',
      radius: ['35%', '62%'],
      center: ['50%', '45%'],
      label: { formatter: '{b}\n{c} 次' },
      data,
    }],
  })
}

function handleResize() { trendChart && trendChart.resize(); attChart && attChart.resize() }

// 切换 tab 时，隐藏状态初始化的图表尺寸为 0，需重新渲染
watch(activeTab, (tab) => {
  nextTick(() => {
    if (tab === 'scores') {
      renderTrend()
      if (trendChart) trendChart.resize()
    } else if (tab === 'attendance') {
      renderAttChart()
      if (attChart) attChart.resize()
    }
  })
})

onMounted(async () => {
  await loadAll()
  nextTick(() => {
    renderTrend()
    window.addEventListener('resize', handleResize)
  })
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart && trendChart.dispose()
  attChart && attChart.dispose()
})
</script>

<style scoped>
.student-header {
  display: flex;
  align-items: center;
  gap: 20px;
}
.student-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.student-name {
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}
.student-meta {
  display: flex;
  gap: 16px;
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}
.student-subjects {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #606266;
  font-size: 13px;
  margin-top: 8px;
}
.tab-toolbar {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.session-badge {
  font-size: 13px;
  color: #10b981;
  background: #ecfdf5;
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid #a7f3d0;
}
.session-badge strong {
  font-size: 16px;
}
.trend-chart {
  height: 260px;
}
.att-chart {
  height: 200px;
}
.stat-title {
  color: #909399;
  font-size: 13px;
}
.stat-big {
  font-size: 32px;
  font-weight: 700;
  color: #10b981;
  margin: 8px 0 4px;
}
.stat-sub {
  color: #909399;
  font-size: 12px;
}
:deep(.el-rate__icon.is-active) {
  color: #f59e0b;
}
.session-overview {
  margin-bottom: 16px;
}
.session-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  margin-top: 8px;
}
.session-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
}
.session-subject-name {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}
.session-progress {
  font-size: 12px;
}
.progress-text {
  font-size: 12px;
  color: #606266;
}
.session-unlimited {
  font-size: 12px;
  padding: 4px 0;
}
</style>