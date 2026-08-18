<template>
  <div class="page-container">
    <!-- 数据概览 -->
    <div class="mini-stats mb-16">
      <div class="mini-stat">
        <div class="ms-label">💰 本月收入</div>
        <div class="ms-value" style="color: var(--success)">¥{{ summary.monthIncome }}</div>
      </div>
      <div class="mini-stat">
        <div class="ms-label">🧾 收费总流水</div>
        <div class="ms-value">¥{{ summary.totalFees }}</div>
      </div>
      <div class="mini-stat">
        <div class="ms-label">⚠️ 待缴欠费</div>
        <div class="ms-value" style="color: var(--danger)">¥{{ summary.totalOverdue }}</div>
        <div class="ms-sub">{{ summary.overdueCount }} 笔未结清</div>
      </div>
      <div class="mini-stat">
        <div class="ms-label">↩️ 退费 / 减免</div>
        <div class="ms-value" style="color: var(--warning)">¥{{ summary.totalRefund }}</div>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 左边：收费管理 -->
      <el-col :span="15">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>收费管理</span>
              <div class="header-actions">
                <el-radio-group v-model="studentFilter" size="small">
                  <el-radio-button value="all">全部</el-radio-button>
                  <el-radio-button value="active">在读</el-radio-button>
                </el-radio-group>
                <el-button type="primary" size="small" :icon="Plus" @click="openFeeDialog">记一笔收费</el-button>
              </div>
            </div>
          </template>

          <el-tabs v-model="activeTab">
            <!-- 收费流水 -->
            <el-tab-pane label="收费流水" name="fees">
              <el-table :data="filtered(fees)" size="small" stripe>
                <el-table-column label="学生" width="110">
                  <template #default="{ row }">
                    <span>{{ row.student_name }}</span>
                    <el-tag v-if="row.student_deleted" size="small" type="danger" style="margin-left:4px">已删除</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="fee_type" label="类型" width="80" />
                <el-table-column prop="amount" label="金额" width="90">
          <template #default="{ row }"><span style="color:#10b981;font-weight:600">¥{{ row.amount }}</span></template>
        </el-table-column>
                <el-table-column prop="pay_date" label="日期" width="110" />
                <el-table-column prop="payment_period" label="时间段" width="90">
                  <template #default="{ row }">{{ row.payment_period || '-' }}</template>
                </el-table-column>
                <el-table-column label="到期日" width="130">
                  <template #default="{ row }">
                    <template v-if="row.expire_date">
                      <span :class="isExpiring(row) ? 'expire-warn-text' : ''">{{ row.expire_date }}</span>
                      <el-tag v-if="expireStatus(row)" size="small" :type="expireStatus(row).type" style="margin-left:4px">{{ expireStatus(row).text }}</el-tag>
                    </template>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="payment_method" label="方式" width="90" />
                <el-table-column label="次数" width="150" align="center">
                  <template #default="{ row }">
                    <div v-if="row.total_sessions" class="mini-progress" style="max-width:130px">
                      <div class="mp-track">
                        <div class="mp-bar" :class="sessionClass(row)" :style="{ width: sessionWidth(row) + '%' }"></div>
                      </div>
                      <span class="mp-text">{{ row.remaining_sessions ?? row.total_sessions }}/{{ row.total_sessions }}</span>
                    </div>
                    <span v-else style="color:#c0c4cc">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="remark" label="备注" show-overflow-tooltip />
              </el-table>
            </el-tab-pane>

            <!-- 账单 -->
            <el-tab-pane label="账单管理" name="invoices">
              <el-button size="small" :icon="Plus" style="margin-bottom:10px" @click="openInvoiceDialog">生成账单</el-button>
              <el-table :data="filtered(invoices)" size="small" stripe>
                <el-table-column label="学生" width="110">
                  <template #default="{ row }">
                    <span>{{ row.student_name }}</span>
                    <el-tag v-if="row.student_deleted" size="small" type="danger" style="margin-left:4px">已删除</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="item" label="项目" width="120" />
                <el-table-column prop="amount" label="应收" width="90">
                  <template #default="{ row }"><span style="color:#f59e0b;font-weight:600">¥{{ row.amount }}</span></template>
                </el-table-column>
                <el-table-column prop="paid_amount" label="已缴" width="90">
                  <template #default="{ row }"><span style="color:#10b981;font-weight:600">¥{{ row.paid_amount }}</span></template>
                </el-table-column>
                <el-table-column prop="due_date" label="应缴日期" width="110" />
                <el-table-column label="状态" width="90">
                  <template #default="{ row }">
                    <el-tag size="small" :type="statusType(row.status)">{{ row.status }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>

            <!-- 欠费提醒 -->
            <el-tab-pane label="欠费提醒" name="overdue">
              <el-table :data="filtered(overdue)" size="small" stripe>
                <el-table-column label="学生" width="120">
                  <template #default="{ row }">
                    <span>{{ row.student_name }}</span>
                    <el-tag v-if="row.student_deleted" size="small" type="danger" style="margin-left:4px">已删除</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="item" label="项目" width="120" />
                <el-table-column prop="amount" label="应收" width="90" />
                <el-table-column prop="unpaid" label="欠费">
                  <template #default="{ row }"><span style="color:#f56c6c;font-weight:600">¥{{ row.unpaid }}</span></template>
                </el-table-column>
                <el-table-column prop="due_date" label="应缴日期" width="110" />
                <el-table-column label="操作">
                  <template #default="{ row }">
                    <el-button size="small" type="primary" link @click="openRefundDialog(row)">减免/退费</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>

            <!-- 学费分期 -->
            <el-tab-pane label="学费分期" name="installments">
              <el-button size="small" :icon="Plus" style="margin-bottom:10px" @click="openInstallment">创建分期</el-button>
              <el-table :data="filtered(installments)" size="small" stripe>
                <el-table-column label="学生" width="110">
                  <template #default="{ row }">
                    <span>{{ row.student_name }}</span>
                    <el-tag v-if="row.student_deleted" size="small" type="danger" style="margin-left:4px">已删除</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="title" label="分期名称" width="130" />
                <el-table-column prop="total_amount" label="总额" width="90">
                  <template #default="{ row }"><span style="color:#e6a23c;font-weight:600">¥{{ row.total_amount }}</span></template>
                </el-table-column>
                <el-table-column label="进度" width="150">
                  <template #default="{ row }">
                    <div class="mini-progress">
                      <div class="mp-track">
                        <div class="mp-bar" :class="row.status === '已完成' ? '' : 'is-warn'" :style="{ width: instProgress(row) + '%' }"></div>
                      </div>
                      <span class="mp-text">{{ row.paid_periods }}/{{ row.periods }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="90">
                  <template #default="{ row }"><el-tag size="small" :type="row.status === '已完成' ? 'success' : 'warning'">{{ row.status }}</el-tag></template>
                </el-table-column>
                <el-table-column label="操作" width="160">
                  <template #default="{ row }">
                    <el-button size="small" type="primary" link @click="viewInstallment(row)">详情</el-button>
                    <el-button size="small" type="success" link :disabled="row.status === '已完成'" @click="payInstallment(row)">缴下一期</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>

      <!-- 右边：退费减免记录 -->
      <el-col :span="9">
        <el-card shadow="never">
          <template #header><span>退费/减免记录</span></template>
          <el-table :data="filtered(refunds)" size="small" stripe>
            <el-table-column label="学生" width="110">
              <template #default="{ row }">
                <span>{{ row.student_name || '-' }}</span>
                <el-tag v-if="row.student_deleted" size="small" type="danger" style="margin-left:4px">已删除</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="kind" label="类型" width="70">
              <template #default="{ row }">
                <el-tag size="small" :type="row.kind === '退费' ? 'danger' : 'warning'">{{ row.kind }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" width="80" />
            <el-table-column prop="reason" label="原因" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 收费对话框 -->
    <el-dialog v-model="feeVisible" title="记一笔收费" width="500px">
      <el-form :model="feeForm" label-width="90px">
        <el-form-item label="学生" required>
          <el-select v-model="feeForm.student_id" filterable placeholder="选择学生" style="width:100%">
            <el-option v-for="s in students" :key="s.id" :label="`${s.name}(${s.student_no})`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="收费类型">
          <el-select v-model="feeForm.fee_type" style="width:100%">
            <el-option label="学费" value="学费" />
            <el-option label="餐费" value="餐费" />
            <el-option label="杂费" value="杂费" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input-number v-model="feeForm.amount" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="缴费日期">
          <el-date-picker v-model="feeForm.pay_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="缴费时间段">
          <el-select v-model="feeForm.payment_period" clearable placeholder="选择时间段（自动推算到期日）" style="width:100%">
            <el-option label="一月" value="一月" />
            <el-option label="半学期" value="半学期" />
            <el-option label="一年" value="一年" />
          </el-select>
          <div v-if="feeExpirePreview" class="period-tip">到期日：{{ feeExpirePreview }}</div>
        </el-form-item>
        <el-form-item label="课程总次数">
          <el-input-number v-model="feeForm.total_sessions" :min="0" :step="1" placeholder="按次核销时填写" style="width:100%" />
          <div class="period-tip">填写后，每次打卡自动核销1次</div>
        </el-form-item>
        <el-form-item label="支付方式">
          <el-select v-model="feeForm.payment_method" style="width:100%">
            <el-option label="现金" value="现金" />
            <el-option label="微信" value="微信" />
            <el-option label="支付宝" value="支付宝" />
            <el-option label="银行转账" value="转账" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="feeForm.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feeVisible = false">取消</el-button>
        <el-button type="primary" @click="saveFee">保存</el-button>
      </template>
    </el-dialog>

    <!-- 账单对话框 -->
    <el-dialog v-model="invoiceVisible" title="生成账单" width="500px">
      <el-form :model="invoiceForm" label-width="90px">
        <el-form-item label="学生" required>
          <el-select v-model="invoiceForm.student_id" filterable placeholder="选择学生" style="width:100%">
            <el-option v-for="s in students" :key="s.id" :label="`${s.name}(${s.student_no})`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" required>
          <el-input v-model="invoiceForm.item" placeholder="如：暑期托管费" />
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input-number v-model="invoiceForm.amount" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="应缴日期">
          <el-date-picker v-model="invoiceForm.due_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="invoiceVisible = false">取消</el-button>
        <el-button type="primary" @click="saveInvoice">保存</el-button>
      </template>
    </el-dialog>

    <!-- 减免/退费对话框 -->
    <el-dialog v-model="refundVisible" title="减免/退费" width="500px">
      <el-form :model="refundForm" label-width="90px">
        <el-form-item label="类型">
          <el-radio-group v-model="refundForm.kind">
            <el-radio value="减免">减免</el-radio>
            <el-radio value="退费">退费</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input-number v-model="refundForm.amount" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="refundForm.reason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="refundVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRefund">确认</el-button>
      </template>
    </el-dialog>

    <!-- 创建分期对话框 -->
    <el-dialog v-model="instVisible" title="创建学费分期" width="500px">
      <el-form :model="instForm" label-width="90px">
        <el-form-item label="学生" required>
          <el-select v-model="instForm.student_id" filterable placeholder="选择学生" style="width:100%">
            <el-option v-for="s in students" :key="s.id" :label="`${s.name}(${s.student_no})`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="分期名称" required>
          <el-input v-model="instForm.title" placeholder="如：暑期学费分期" />
        </el-form-item>
        <el-form-item label="总金额" required>
          <el-input-number v-model="instForm.total_amount" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="期数" required>
          <el-input-number v-model="instForm.periods" :min="1" :max="24" style="width:100%" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="instForm.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="instForm.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="instVisible = false">取消</el-button>
        <el-button type="primary" @click="saveInstallment">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分期详情对话框 -->
    <el-dialog v-model="instDetailVisible" title="分期详情" width="560px">
      <el-descriptions :column="2" border size="small" style="margin-bottom:14px">
        <el-descriptions-item label="学生">{{ instDetail.student_name }}</el-descriptions-item>
        <el-descriptions-item label="分期名称">{{ instDetail.title }}</el-descriptions-item>
        <el-descriptions-item label="总金额">¥{{ instDetail.total_amount }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ instDetail.status }}</el-descriptions-item>
      </el-descriptions>
      <el-table :data="instDetail.records" size="small" stripe>
        <el-table-column prop="period_no" label="期数" width="70">
          <template #default="{ row }">第{{ row.period_no }}期</template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="90" />
        <el-table-column prop="due_date" label="应缴日期" width="110" />
        <el-table-column prop="paid_date" label="实缴日期" width="110" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }"><el-tag size="small" :type="row.status === '已缴' ? 'success' : 'info'">{{ row.status }}</el-tag></template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'

const PERIOD_DAYS = { '一月': 30, '半学期': 60, '一年': 365 }

const route = useRoute()

const activeTab = ref('fees')
const studentFilter = ref('all')
const students = ref([])
const fees = ref([])
const invoices = ref([])
const overdue = ref([])
const refunds = ref([])
const installments = ref([])

const feeVisible = ref(false)
const invoiceVisible = ref(false)
const refundVisible = ref(false)
const instVisible = ref(false)
const instDetailVisible = ref(false)

const feeForm = reactive({ student_id: null, fee_type: '学费', amount: 0, pay_date: '', payment_method: '现金', payment_period: '', total_sessions: null, remark: '' })

const feeExpirePreview = computed(() => {
  const days = PERIOD_DAYS[feeForm.payment_period]
  if (!days || !feeForm.pay_date) return ''
  const d = new Date(feeForm.pay_date)
  d.setDate(d.getDate() + days)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
})

function isExpiring(row) {
  if (!row.expire_date) return false
  const days = (new Date(row.expire_date) - new Date()) / 86400000
  return days <= 5
}

// ===== 纯展示：数据概览与进度（不改变任何业务逻辑） =====
const summary = computed(() => {
  const now = new Date()
  const ym = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  const monthIncome = fees.value.filter((f) => (f.pay_date || '').startsWith(ym)).reduce((a, b) => a + (b.amount || 0), 0)
  const totalFees = fees.value.reduce((a, b) => a + (b.amount || 0), 0)
  const totalOverdue = overdue.value.reduce((a, b) => a + (b.unpaid || 0), 0)
  const totalRefund = refunds.value.reduce((a, b) => a + (b.amount || 0), 0)
  return { monthIncome, totalFees, totalOverdue, totalRefund, overdueCount: overdue.value.length }
})

function expireStatus(row) {
  if (!row.expire_date) return null
  const days = Math.ceil((new Date(row.expire_date) - new Date()) / 86400000)
  if (days < 0) return { type: 'danger', text: `已到期 ${-days} 天` }
  if (days <= 5) return { type: 'warning', text: `${days} 天后到期` }
  return null
}

function sessionWidth(row) {
  const t = row.total_sessions
  const r = row.remaining_sessions ?? t
  if (!t) return 0
  return Math.max(0, Math.min(100, Math.round((r / t) * 100)))
}
function sessionClass(row) {
  const w = sessionWidth(row)
  return w < 20 ? 'is-danger' : w < 50 ? 'is-warn' : ''
}

function instProgress(row) {
  if (!row.periods) return 0
  return Math.max(0, Math.min(100, Math.round(((row.paid_periods || 0) / row.periods) * 100)))
}
const invoiceForm = reactive({ student_id: null, item: '', amount: 0, due_date: '' })
const refundForm = reactive({ student_id: null, invoice_id: null, kind: '减免', amount: 0, reason: '' })
const instForm = reactive({ student_id: null, title: '', total_amount: 0, periods: 1, start_date: '', remark: '' })
const instDetail = ref({ records: [] })

function statusType(status) {
  return { '已缴清': 'success', '待缴': 'warning', '部分缴纳': 'danger', '已减免': 'info' }[status] || 'info'
}

function filtered(list) {
  if (studentFilter.value === 'all') return list
  const wantDeleted = studentFilter.value === 'deleted'
  return list.filter(r => Boolean(r.student_deleted) === wantDeleted)
}

async function loadAll() {
  students.value = await request.get('/students')
  fees.value = await request.get('/income/fees')
  invoices.value = await request.get('/income/invoices')
  overdue.value = await request.get('/income/overdue')
  refunds.value = await request.get('/income/refunds')
  installments.value = await request.get('/income/installments')
}

function openFeeDialog(studentId = null) {
  Object.assign(feeForm, { student_id: studentId, fee_type: '学费', amount: 0, pay_date: todayStr(), payment_method: '现金', payment_period: '', total_sessions: null, remark: '' })
  feeVisible.value = true
}

function todayStr() {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${dd}`
}
function openInvoiceDialog() {
  Object.assign(invoiceForm, { student_id: null, item: '', amount: 0, due_date: '' })
  invoiceVisible.value = true
}
function openRefundDialog(row) {
  Object.assign(refundForm, { student_id: row.student_id, invoice_id: row.invoice_id, kind: '减免', amount: row.unpaid, reason: '' })
  refundVisible.value = true
}

async function saveFee() {
  if (!feeForm.student_id) return ElMessage.warning('请选择学生')
  await request.post('/income/fees', feeForm)
  ElMessage.success('收费记录已保存')
  feeVisible.value = false
  loadAll()
}
async function saveInvoice() {
  if (!invoiceForm.student_id) return ElMessage.warning('请选择学生')
  await request.post('/income/invoices', invoiceForm)
  ElMessage.success('账单已生成')
  invoiceVisible.value = false
  loadAll()
}
async function saveRefund() {
  await request.post('/income/refunds', refundForm)
  ElMessage.success('已处理')
  refundVisible.value = false
  loadAll()
}

function openInstallment() {
  Object.assign(instForm, { student_id: null, title: '', total_amount: 0, periods: 1, start_date: '', remark: '' })
  instVisible.value = true
}
async function saveInstallment() {
  if (!instForm.student_id) return ElMessage.warning('请选择学生')
  if (!instForm.title) return ElMessage.warning('请输入分期名称')
  await request.post('/income/installments', instForm)
  ElMessage.success('分期已创建')
  instVisible.value = false
  loadAll()
}
async function viewInstallment(row) {
  instDetail.value = await request.get(`/income/installments/${row.id}`)
  instDetailVisible.value = true
}
async function payInstallment(row) {
  const res = await request.post(`/income/installments/${row.id}/pay`)
  ElMessage.success(res.detail || '已缴纳')
  loadAll()
}

onMounted(async () => {
  await loadAll()
  // 从工作台「新学员交费提醒」跳转而来：自动打开收费弹窗并预选学生，记录收费后提醒自动消失
  const sid = Number(route.query.fee_student)
  if (sid) {
    const st = students.value.find((s) => s.id === sid)
    openFeeDialog(sid)
    ElMessage.info(st ? `请为「${st.name}」记录收费，保存后工作台提醒将自动消失` : '请为所选学生记录收费')
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.period-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #e6a23c;
}
.expire-warn-text {
  color: #f59e0b;
  font-weight: 600;
}

/* 表格行 hover 过渡 */
.el-table tbody tr {
  transition: background-color 0.25s ease;
}

/* 标签页样式优化 */
:deep(.el-tabs__header) {
  margin-bottom: 12px;
}
:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}
:deep(.el-tabs__item) {
  font-weight: 500;
  transition: color 0.2s;
}
</style>