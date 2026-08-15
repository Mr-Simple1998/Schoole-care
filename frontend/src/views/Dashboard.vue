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
      <el-col :span="(userStore.isPrincipal || userStore.isSubPrincipal) ? 6 : 12" v-for="card in statCards" :key="card.label">
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

    <!-- 图表区（收入趋势仅总校长/校区负责人可见本校区收入） -->
    <el-row v-if="userStore.isPrincipal || userStore.isSubPrincipal" :gutter="16" class="mt-16">
      <el-col :span="16">
        <el-card shadow="never">
          <div class="card-title">近14天收入趋势</div>
          <div ref="incomeChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="card-title">学科 / 非学科人数</div>
          <div ref="catChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 学科分布 / 快捷入口 -->
    <el-row :gutter="16" class="mt-16">
      <el-col :span="16">
        <el-card shadow="never">
          <div class="card-title">学科学生分布</div>
          <div ref="subjectChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
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
      <el-col :span="12">
        <el-card shadow="never">
          <div class="card-title">学科 / 非学科人数</div>
          <div ref="catChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'
import { AlarmClock } from '@element-plus/icons-vue'

const userStore = useUserStore()
const incomeChartRef = ref()
const subjectChartRef = ref()
const catChartRef = ref()
let chart = null
let subjectChart = null
let catChart = null

const overview = ref({})
const subjectStats = ref({ subject_counts: [], category_counts: {}, total_students: 0 })
const animatedValues = reactive({})

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
/* transitions */
.slide-down-enter-active { transition: all 0.4s ease-out; }
.slide-down-leave-active { transition: all 0.3s ease-in; }
.slide-down-enter-from { opacity: 0; transform: translateY(-20px); }
.slide-down-leave-to { opacity: 0; transform: translateY(-10px); }
</style>