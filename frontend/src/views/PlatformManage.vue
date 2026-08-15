<template>
  <div class="page-container">
    <el-card shadow="always">
      <template #header>
        <div class="card-header">
          <span>机构开户管理</span>
          <el-button type="primary" size="small" :icon="Plus" @click="openCreate">新校长开户</el-button>
        </div>
      </template>

      <!-- 统计概览 -->
      <el-row :gutter="16" class="stat-row stat-card-animated">
        <el-col :span="6">
          <el-card shadow="always" class="stat-card">
            <div class="stat-num">{{ organizations.length }}</div>
            <div class="stat-label">机构总数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="always" class="stat-card">
            <div class="stat-num">{{ totalPaid }}</div>
            <div class="stat-label">累计交费(元)</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="always" class="stat-card">
            <div class="stat-num highlight-warn">{{ expiringCount }}</div>
            <div class="stat-label">即将到期</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="always" class="stat-card">
            <div class="stat-num highlight-danger">{{ expiredCount }}</div>
            <div class="stat-label">已到期</div>
          </el-card>
        </el-col>
      </el-row>

      <el-table :data="organizations" stripe>
        <el-table-column prop="name" label="机构名称" min-width="130" />
        <el-table-column prop="code" label="机构编码" width="100" />
        <el-table-column label="校长账号" min-width="150">
          <template #default="{ row }">
            <template v-if="row.principal">
              <div>{{ row.principal.username }}</div>
              <div class="sub-text">{{ row.principal.name }}</div>
            </template>
            <span v-else class="sub-text">未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="计费方式" width="90">
          <template #default="{ row }">{{ row.plan_type_text || '-' }}</template>
        </el-table-column>
        <el-table-column label="交费时间段" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.payment_period" size="small" type="success">{{ row.payment_period }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="交费金额(元)" width="110">
          <template #default="{ row }">{{ row.fee_amount }}</template>
        </el-table-column>
        <el-table-column label="累计交费(元)" width="110">
          <template #default="{ row }">{{ row.total_paid }}</template>
        </el-table-column>
        <el-table-column label="到期状态" width="150">
          <template #default="{ row }">
            <div>
              <el-tag size="small" :type="statusTagType(row.expire_status)">{{ statusText(row) }}</el-tag>
            </div>
            <div v-if="row.expire_date" class="sub-text">{{ row.expire_date }}</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status ? 'success' : 'info'">{{ row.status ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" link type="success" @click="openRenew(row)">交费/续费</el-button>
            <el-button size="small" link @click="openPayments(row)">流水</el-button>
            <el-button size="small" link type="warning" @click="openResetPwd(row)">重置密码</el-button>
            <el-button size="small" link :type="row.status ? 'danger' : 'success'" @click="toggleStatus(row)">
              {{ row.status ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 开户流水统计 -->
    <el-card shadow="always" class="mt-16">
      <template #header>
        <div class="card-header"><span>开户流水统计</span></div>
      </template>
      <el-tabs v-model="statTab">
        <el-tab-pane label="总交费金额" name="total">
          <el-row :gutter="16" class="stat-card-animated">
            <el-col :span="8">
              <el-card shadow="always" class="stat-card">
                <div class="stat-num">{{ stat.total_amount }}</div>
                <div class="stat-label">全部机构累计交费(元)</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="always" class="stat-card">
                <div class="stat-num">{{ stat.org_count }}</div>
                <div class="stat-label">开户机构数</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="always" class="stat-card">
                <div class="stat-num highlight-danger">{{ stat.due_list?.length ?? 0 }}</div>
                <div class="stat-label">待收款/已到期机构</div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
        <el-tab-pane label="按机构汇总" name="by_org">
          <el-table :data="stat.by_org || []" stripe size="small" max-height="400">
            <el-table-column prop="name" label="机构名称" />
            <el-table-column prop="total_paid" label="累计交费(元)" width="130" />
            <el-table-column label="交费时间段" width="90">
              <template #default="{ row }">{{ row.payment_period || '-' }}</template>
            </el-table-column>
            <el-table-column label="到期状态" width="150">
              <template #default="{ row }">
                <div>
                  <el-tag size="small" :type="statusTagType(row.expire_status)">{{ orgStatusText(row.expire_status, row.expire_date) }}</el-tag>
                </div>
                <div v-if="row.expire_date" class="sub-text">{{ row.expire_date }}</div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="按月趋势" name="by_month">
          <div ref="monthChartRef" class="chart-box"></div>
        </el-tab-pane>
        <el-tab-pane label="待收款/已到期列表" name="due">
          <el-table :data="stat.due_list || []" stripe size="small" max-height="400">
            <el-table-column prop="name" label="机构名称" />
            <el-table-column label="交费时间段" width="90">
              <template #default="{ row }">{{ row.payment_period || '-' }}</template>
            </el-table-column>
            <el-table-column label="到期状态" width="120">
              <template #default="{ row }">
                <div>
                  <el-tag size="small" :type="row.expire_status === 'expired' ? 'danger' : 'warning'">
                    {{ row.expire_status === 'expired' ? '已到期' : '即将到期' }}
                  </el-tag>
                </div>
                <div v-if="row.days_left !== null && row.days_left !== undefined" class="sub-text">
                  {{ row.days_left < 0 ? '已到期' : `剩 ${row.days_left} 天` }}
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="expire_date" label="到期日期" width="120">
              <template #default="{ row }">{{ row.expire_date || '-' }}</template>
            </el-table-column>
            <el-table-column prop="total_paid" label="累计交费(元)" width="130" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" link type="success" @click="openRenewById(row.org_id)">去续费</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新校长开户对话框 -->
    <el-dialog v-model="createVisible" title="新校长开户" width="560px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="机构名称" prop="org_name">
          <el-input v-model="createForm.org_name" placeholder="如：阳光教育培训学校" />
        </el-form-item>
        <el-form-item label="校长姓名" prop="contact">
          <el-input v-model="createForm.contact" placeholder="校长姓名" />
        </el-form-item>
        <el-form-item label="登录账号" prop="username">
          <el-input v-model="createForm.username" placeholder="校长登录账号（唯一）" />
        </el-form-item>
        <el-form-item label="登录密码" prop="password">
          <el-input v-model="createForm.password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="createForm.phone" placeholder="选填" />
        </el-form-item>
        <el-divider content-position="left">开户交费</el-divider>
        <el-form-item label="计费方式">
          <el-select v-model="createForm.plan_type" placeholder="选择计费方式（选填）" style="width: 100%">
            <el-option label="按年" value="annual" />
            <el-option label="按次/阶段" value="stage" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="交费金额(元)">
          <el-input-number v-model="createForm.fee_amount" :min="0" :precision="2" style="width: 100%" placeholder="选填" />
        </el-form-item>
        <el-form-item label="交费时间段">
          <el-select v-model="createForm.payment_period" clearable placeholder="选择交费时间段（自动推算到期日）" style="width: 100%">
            <el-option label="半年" value="半年" />
            <el-option label="一年" value="一年" />
          </el-select>
          <div v-if="createForm.payment_period" class="tip-text">到期日期：{{ calcExpire(createForm.payment_period) }}</div>
        </el-form-item>
      </el-form>
      <div class="tip-text">开户后，该校长登录系统数据为空白，需自行录入学生、学科等信息。</div>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">确认开户</el-button>
      </template>
    </el-dialog>

    <!-- 编辑机构对话框 -->
    <el-dialog v-model="editVisible" title="编辑机构" width="480px">
      <el-form :model="editForm" label-width="90px">
        <el-form-item label="机构名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="editForm.contact" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="editForm.phone" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEditSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 交费/续费对话框 -->
    <el-dialog v-model="renewVisible" title="机构交费 / 续费" width="480px">
      <div style="margin-bottom: 12px">机构：<b>{{ renewTarget?.name }}</b></div>
      <el-form :model="renewForm" label-width="90px">
        <el-form-item label="计费方式">
          <el-select v-model="renewForm.plan_type" placeholder="选择计费方式" style="width: 100%">
            <el-option label="按年" value="annual" />
            <el-option label="按次/阶段" value="stage" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="交费金额(元)">
          <el-input-number v-model="renewForm.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="交费时间段">
          <el-select v-model="renewForm.payment_period" clearable placeholder="选择交费时间段（自动顺延到期日）" style="width: 100%">
            <el-option label="半年" value="半年" />
            <el-option label="一年" value="一年" />
          </el-select>
          <div v-if="renewForm.payment_period" class="tip-text">续费后到期日期：{{ calcExpire(renewForm.payment_period, renewTarget?.expire_date) }}</div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="renewForm.remark" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renewVisible = false">取消</el-button>
        <el-button type="success" :loading="saving" @click="handleRenew">确认交费</el-button>
      </template>
    </el-dialog>

    <!-- 流水明细对话框 -->
    <el-dialog v-model="paymentsVisible" title="开户流水明细" width="560px">
      <div style="margin-bottom: 12px">机构：<b>{{ paymentsTarget?.name }}</b></div>
      <el-table :data="paymentRows" stripe size="small" max-height="380">
        <el-table-column prop="created_at" label="交费时间" width="170" />
        <el-table-column prop="amount" label="金额(元)" width="100" />
        <el-table-column label="计费方式" width="100">
          <template #default="{ row }">{{ row.plan_type_text || '-' }}</template>
        </el-table-column>
        <el-table-column prop="expire_date" label="到期日期" width="110" />
        <el-table-column prop="remark" label="备注" />
      </el-table>
      <template #footer>
        <el-button @click="paymentsVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 重置校长密码对话框 -->
    <el-dialog v-model="pwdVisible" title="重置校长密码" width="460px">
      <div style="margin-bottom: 12px">机构：<b>{{ pwdTarget?.name }}</b></div>
      <el-input v-model="pwdForm.password" type="password" show-password placeholder="输入新密码（至少 6 位）" />
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="warning" @click="handleResetPwd">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import request from '@/utils/request'

const organizations = ref([])
const stat = ref({})
const saving = ref(false)
const statTab = ref('total')
const createVisible = ref(false)
const editVisible = ref(false)
const renewVisible = ref(false)
const paymentsVisible = ref(false)
const pwdVisible = ref(false)
const editTarget = ref(null)
const renewTarget = ref(null)
const paymentsTarget = ref(null)
const pwdTarget = ref(null)
const createFormRef = ref()
const paymentRows = ref([])
const monthChartRef = ref()
let monthChart = null

const createForm = reactive({ org_name: '', contact: '', username: '', password: '', phone: '', plan_type: '', fee_amount: 0, payment_period: '' })
const createRules = {
  org_name: [{ required: true, message: '请输入机构名称', trigger: 'blur' }],
  contact: [{ required: true, message: '请输入校长姓名', trigger: 'blur' }],
  username: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入登录密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}
const editForm = reactive({ name: '', contact: '', phone: '' })
const renewForm = reactive({ plan_type: '', amount: 0, payment_period: '', remark: '' })
const pwdForm = reactive({ password: '' })

const PERIOD_DAYS = { '半年': 180, '一年': 365 }

function calcExpire(period, base) {
  const days = PERIOD_DAYS[period]
  if (!days) return ''
  const d = base ? new Date(base) : new Date()
  d.setDate(d.getDate() + days)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

const totalPaid = computed(() => organizations.value.reduce((s, o) => s + (o.total_paid || 0), 0))
const expiringCount = computed(() => organizations.value.filter((o) => o.expire_status === 'expiring').length)
const expiredCount = computed(() => organizations.value.filter((o) => o.expire_status === 'expired').length)

function statusTagType(st) {
  if (st === 'expired') return 'danger'
  if (st === 'expiring') return 'warning'
  if (st === 'normal') return 'success'
  return 'info'
}
function statusText(row) {
  if (row.expire_status === 'expired') return '已到期'
  if (row.expire_status === 'expiring') return `剩${row.days_left}天`
  if (row.expire_status === 'normal') return '正常'
  return '未设置'
}
function orgStatusText(st, date) {
  if (st === 'expired') return '已到期'
  if (st === 'expiring') return '即将到期'
  if (st === 'normal') return '正常'
  return '未设置'
}

async function loadData() {
  organizations.value = await request.get('/platform/organizations')
  stat.value = await request.get('/platform/payments/statistics')
  renderMonthChart()
}

function renderMonthChart() {
  const rows = stat.value.by_month || []
  if (!rows.length) return
  if (!monthChart) {
    monthChart = echarts.init(monthChartRef.value)
  }
  monthChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: rows.map((d) => d.month), axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed' } } },
    series: [{
      name: '交费金额',
      type: 'bar',
      data: rows.map((d) => d.amount),
      itemStyle: { color: '#10b981', borderRadius: [6, 6, 0, 0] },
      barMaxWidth: 40,
    }],
  })
}

function openCreate() {
  Object.assign(createForm, { org_name: '', contact: '', username: '', password: '', phone: '', plan_type: '', fee_amount: 0, payment_period: '' })
  createVisible.value = true
}

async function handleCreate() {
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      await request.post('/platform/organizations', createForm)
      ElMessage.success('开户成功，新校长账号已创建')
      createVisible.value = false
      loadData()
    } finally {
      saving.value = false
    }
  })
}

function openEdit(row) {
  editTarget.value = row
  Object.assign(editForm, { name: row.name, contact: row.contact || '', phone: row.phone || '' })
  editVisible.value = true
}

async function handleEditSave() {
  await request.put(`/platform/organizations/${editTarget.value.id}`, editForm)
  ElMessage.success('机构信息已更新')
  editVisible.value = false
  loadData()
}

async function toggleStatus(row) {
  const action = row.status ? '停用' : '启用'
  await ElMessageBox.confirm(`确定${action}机构「${row.name}」吗？`, '提示', { type: 'warning' })
  await request.put(`/platform/organizations/${row.id}`, { status: !row.status })
  ElMessage.success(`已${action}`)
  loadData()
}

function openRenew(row) {
  renewTarget.value = row
  Object.assign(renewForm, { plan_type: row.plan_type || 'annual', amount: 0, payment_period: row.payment_period || '', remark: '' })
  renewVisible.value = true
}
function openRenewById(orgId) {
  const row = organizations.value.find((o) => o.id === orgId)
  if (row) openRenew(row)
}

async function handleRenew() {
  if (renewForm.amount <= 0 && !renewForm.payment_period) {
    ElMessage.warning('请填写交费金额或选择交费时间段')
    return
  }
  saving.value = true
  try {
    await request.post(`/platform/organizations/${renewTarget.value.id}/payments`, renewForm)
    ElMessage.success('交费成功，流水已记录')
    renewVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

async function openPayments(row) {
  paymentsTarget.value = row
  paymentRows.value = await request.get(`/platform/organizations/${row.id}/payments`)
  paymentsVisible.value = true
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
  const principal = pwdTarget.value?.principal
  if (!principal) {
    ElMessage.warning('该机构暂无校长账号可重置')
    return
  }
  await request.put(`/platform/principals/${principal.id}/reset-password`, { password: pwdForm.password })
  ElMessage.success('校长密码已重置')
  pwdVisible.value = false
}

function handleResize() {
  monthChart && monthChart.resize()
}

onMounted(async () => {
  await loadData()
  nextTick(() => window.addEventListener('resize', handleResize))
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  monthChart && monthChart.dispose()
})
</script>

<style scoped>
/* ===== 全局 el-card 圆角 + 阴影 ===== */
.el-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.06);
}
:deep(.el-card__body) {
  border-radius: 12px;
}

/* ===== 卡片头部 ===== */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* ===== 统计行 ===== */
.stat-row {
  margin-bottom: 16px;
}

/* ===== 统计卡片 ===== */
.stat-card {
  text-align: center;
  padding: 20px;
  border-radius: 12px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px 0 rgba(0, 0, 0, 0.12);
}

/* ===== staggered 入场动画（slide-up） ===== */
.stat-card-animated .el-col {
  animation: slideUp 0.5s ease-out both;
}
.stat-card-animated .el-col:nth-child(1) { animation-delay: 0.05s; }
.stat-card-animated .el-col:nth-child(2) { animation-delay: 0.15s; }
.stat-card-animated .el-col:nth-child(3) { animation-delay: 0.25s; }
.stat-card-animated .el-col:nth-child(4) { animation-delay: 0.35s; }

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== 统计数字（计数动画） ===== */
.stat-num {
  font-size: 26px;
  font-weight: 700;
  color: #409eff;
  animation: countIn 0.6s ease-out;
}
@keyframes countIn {
  from {
    opacity: 0;
    transform: scale(0.4);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
.stat-num.highlight-warn {
  color: #e6a23c;
}
.stat-num.highlight-danger {
  color: #f56c6c;
}

/* ===== 标签 & 辅助文字 ===== */
.stat-label {
  color: #909399;
  font-size: 13px;
  margin-top: 4px;
}
.sub-text {
  color: #909399;
  font-size: 12px;
}
.tip-text {
  color: #909399;
  font-size: 12px;
  margin-bottom: 8px;
}
.mt-16 {
  margin-top: 16px;
}
.warn-text {
  color: #e6a23c;
}
.danger-text {
  color: #f56c6c;
}

/* ===== 图表区 ===== */
.chart-box {
  height: 380px;
}
</style>