<template>
  <div class="page-container">
    <!-- 汇总统计卡 -->
    <div class="mini-stats mb-16">
      <div class="mini-stat">
        <div class="ms-label">💰 本月总收入</div>
        <div class="ms-value" style="color: var(--success)">¥{{ fmt(summary?.month_income) }}</div>
        <div class="ms-sub">学费自动归属 + 手工登记</div>
      </div>
      <div class="mini-stat">
        <div class="ms-label">📤 本月总支出</div>
        <div class="ms-value" style="color: var(--danger)">¥{{ fmt(summary?.month_expense) }}</div>
        <div class="ms-sub">房租/工资/水电等</div>
      </div>
      <div class="mini-stat">
        <div class="ms-label">⚖️ 本月结余</div>
        <div class="ms-value" :style="{ color: balanceColor }">¥{{ fmt(summary?.month_balance) }}</div>
        <div class="ms-sub">收入 - 支出</div>
      </div>
      <div class="mini-stat">
        <div class="ms-label">🏫 在读学生</div>
        <div class="ms-value" style="color: var(--info)">{{ summary?.student_count ?? '-' }}</div>
        <div class="ms-sub">全部校区合计 · 今日打卡 {{ summary?.today_attendance ?? 0 }}</div>
      </div>
    </div>

    <!-- 工具条 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="section-title" style="margin: 0">校区概况</span>
        <span class="result-count">共 <b>{{ items.length }}</b> 个校区</span>
      </div>
      <div class="toolbar-right">
        <el-button :icon="Money" @click="openTxn(null)">登记收支</el-button>
        <el-button v-if="canManage" type="primary" :icon="Plus" class="btn-add" @click="openCampus()">新增校区</el-button>
      </div>
    </div>

    <!-- 校区卡片网格 -->
    <div class="card-grid">
      <div v-for="c in items" :key="c.id ?? 'none'" class="campus-card" :class="{ 'is-disabled': c.status === false }">
        <div class="cc-head">
          <div class="cc-title">
            <span class="cc-icon"><el-icon :size="16"><School /></el-icon></span>
            <span class="cc-name">{{ c.name }}</span>
            <el-tag v-if="c.status === false" size="small" type="info" effect="plain">已停用</el-tag>
          </div>
          <div class="cc-head-right">
            <el-tag v-if="c.head" size="small" type="success" effect="light">负责人：{{ c.head.name }}</el-tag>
            <el-tag v-else-if="canManage" size="small" type="info" effect="plain">未设负责人</el-tag>
          </div>
        </div>
        <div class="cc-meta">
          <span v-if="c.address"><el-icon><Location /></el-icon>{{ c.address }}</span>
          <span v-if="c.phone"><el-icon><Phone /></el-icon>{{ c.phone }}</span>
        </div>

        <div class="cc-stats">
          <div class="cc-stat">
            <div class="cs-label">本月收入</div>
            <div class="cs-value amount is-income">¥{{ fmt(c.month_income) }}</div>
          </div>
          <div class="cc-stat">
            <div class="cs-label">本月支出</div>
            <div class="cs-value amount is-expense">¥{{ fmt(c.month_expense) }}</div>
          </div>
          <div class="cc-stat">
            <div class="cs-label">结余</div>
            <div class="cs-value" :style="{ color: c.month_balance >= 0 ? 'var(--success)' : 'var(--danger)' }">
              ¥{{ fmt(c.month_balance) }}
            </div>
          </div>
        </div>

        <div class="cc-info">
          <span v-if="canManage" class="linkable" @click="goStudents(c)">学生 <b>{{ c.student_count }}</b> ›</span>
          <span v-else>学生 <b>{{ c.student_count }}</b></span>
          <span v-if="canManage" class="linkable" @click="goTeachers(c)">教师 <b>{{ c.teacher_count }}</b> ›</span>
          <span v-else>教师 <b>{{ c.teacher_count }}</b></span>
          <span>今日打卡 <b>{{ c.today_attendance }}</b></span>
          <span :class="c.unpaid > 0 ? 'unpaid-warn' : ''">待缴 ¥{{ fmt(c.unpaid) }}</span>
        </div>

        <div class="cc-actions">
          <el-button size="small" :icon="Money" @click="openTxn(c)">登记收支</el-button>
          <el-button size="small" link type="primary" @click="showDetail(c)">明细</el-button>
          <template v-if="canManage">
            <el-button size="small" link @click="openHead(c)">负责人</el-button>
            <el-button size="small" link @click="openCampus(c)">编辑</el-button>
            <el-button size="small" link type="danger" @click="handleDeleteCampus(c)">删除</el-button>
          </template>
        </div>
      </div>

      <!-- 未分校区（校长可见） -->
      <div v-if="uncategorized" class="campus-card is-uncat">
        <div class="cc-head">
          <div class="cc-title">
            <span class="cc-icon"><el-icon :size="16"><QuestionFilled /></el-icon></span>
            <span class="cc-name">未分校区</span>
            <el-tag size="small" type="info" effect="plain">未归属数据</el-tag>
          </div>
        </div>
        <div class="cc-meta"><span>尚未分配校区的学生/数据</span></div>
        <div class="cc-stats">
          <div class="cc-stat">
            <div class="cs-label">本月学费收入</div>
            <div class="cs-value amount is-income">¥{{ fmt(uncategorized.month_income) }}</div>
          </div>
          <div class="cc-stat">
            <div class="cs-label">在读学生</div>
            <div class="cs-value" style="color: var(--info)">{{ uncategorized.student_count }}</div>
          </div>
          <div class="cc-stat">
            <div class="cs-label">今日打卡</div>
            <div class="cs-value" style="color: var(--warning)">{{ uncategorized.today_attendance }}</div>
          </div>
        </div>
        <div class="cc-info">
          <span v-if="canManage" class="linkable" @click="goStudents(null)">学生 <b>{{ uncategorized.student_count }}</b> ›</span>
          <span>待缴 ¥{{ fmt(uncategorized.unpaid) }}</span>
        </div>
        <div class="cc-actions">
          <el-button size="small" link type="primary" @click="showDetail(null)">明细</el-button>
        </div>
      </div>
    </div>

    <!-- 收支明细 -->
    <el-card shadow="never" class="mt-16">
      <div class="txn-head">
        <span class="section-title" style="margin: 0">收支明细</span>
        <div class="txn-filters">
          <el-select v-model="filterCampus" placeholder="全部校区" clearable style="width: 150px" @change="loadTxns">
            <el-option v-for="c in items" :key="c.id ?? 'none'" :label="c.name" :value="c.id" />
          </el-select>
          <el-select v-model="filterKind" placeholder="全部类型" clearable style="width: 120px" @change="loadTxns">
            <el-option label="收入" value="income" />
            <el-option label="支出" value="expense" />
          </el-select>
        </div>
      </div>
      <el-table :data="txns" stripe size="default">
        <el-table-column prop="record_date" label="日期" width="110" />
        <el-table-column prop="campus_name" label="校区" width="120" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.kind === 'income' ? 'success' : 'danger'" effect="light">
              {{ row.kind === 'income' ? '收入' : '支出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="90" />
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            <span :class="row.kind === 'income' ? 'amount is-income' : 'amount is-expense'">
              {{ row.kind === 'income' ? '+' : '-' }}¥{{ fmt(row.amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="160">
          <template #default="{ row }"><span v-if="row.remark">{{ row.remark }}</span><span v-else class="empty-inline">-</span></template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="登记人" width="100" />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="danger" @click="handleDeleteTxn(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty><el-empty description="暂无收支记录" :image-size="80" /></template>
      </el-table>
    </el-card>

    <!-- 校区新增/编辑对话框 -->
    <el-dialog v-model="campusVisible" :title="campusForm.id ? '编辑校区' : '新增校区'" width="480px">
      <el-form :model="campusForm" label-width="80px">
        <el-form-item label="校区名称" required>
          <el-input v-model="campusForm.name" placeholder="如：总校 / 一分校" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="campusForm.address" placeholder="校区地址" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="campusForm.phone" placeholder="联系电话" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="campusForm.remark" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
        <el-form-item v-if="campusForm.id" label="状态">
          <el-switch v-model="campusForm.status" :active-value="true" :inactive-value="false" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="campusVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveCampus">保存</el-button>
      </template>
    </el-dialog>

    <!-- 负责人设置对话框 -->
    <el-dialog v-model="headVisible" :title="`设置「${headCampus?.name || ''}」负责人（校长管理号）`" width="500px">
      <el-form label-width="90px">
        <el-form-item label="当前负责人">
          <template v-if="headCampus?.head">
            <span class="head-current">{{ headCampus.head.name }}（{{ headCampus.head.username }}）</span>
            <el-button size="small" link type="danger" @click="headUserId = null; headMode = 'select'">取消负责人</el-button>
          </template>
          <span v-else class="empty-inline">未设置</span>
        </el-form-item>
        <el-form-item label="设置方式">
          <el-radio-group v-model="headMode">
            <el-radio value="select">从现有教师选择</el-radio>
            <el-radio value="create">手动新建账号</el-radio>
          </el-radio-group>
        </el-form-item>
        <template v-if="headMode === 'select'">
          <el-form-item label="选择教师">
            <el-select v-model="headUserId" placeholder="从本机构教师中选择" clearable filterable style="width: 100%">
              <el-option v-for="t in teachers" :key="t.id" :label="`${t.name}（${t.username}）${t.campus_id ? '· 归属:' + campusName(t.campus_id) : ''}`" :value="t.id" />
            </el-select>
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="负责人姓名" required>
            <el-input v-model="headNew.name" placeholder="如：王小明" />
          </el-form-item>
          <el-form-item label="登录账号" required>
            <el-input v-model="headNew.username" placeholder="用于负责人登录（如：wangxiaoming）" />
          </el-form-item>
          <el-form-item label="登录密码" required>
            <el-input v-model="headNew.password" type="password" show-password placeholder="至少 6 位" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="headNew.phone" placeholder="负责人电话（可选）" />
          </el-form-item>
        </template>
      </el-form>
      <div class="head-tip">校长管理号只能查看/操作自己校区的数据（学生、教师、收支等）；原负责人会自动降为教师。新建的负责人账号可直接在小程序/PC 登录使用。</div>
      <template #footer>
        <el-button @click="headVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveHead">保存</el-button>
      </template>
    </el-dialog>

    <!-- 收支登记对话框 -->
    <el-dialog v-model="txnVisible" title="登记收支" width="480px">
      <el-form :model="txnForm" label-width="80px">
        <el-form-item label="校区" required>
          <el-select v-model="txnForm.campus_id" placeholder="选择校区" style="width: 100%" :disabled="!canManage && txnForm.campus_id">
            <el-option v-for="c in items" :key="c.id ?? 'none'" :label="c.name" :value="c.id" :disabled="c.id === null" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型" required>
          <el-radio-group v-model="txnForm.kind" @change="onKindChange">
            <el-radio-button value="income">收入</el-radio-button>
            <el-radio-button value="expense">支出</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="txnForm.category" placeholder="选择分类" style="width: 100%">
            <el-option v-for="cat in categoryOptions" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input-number v-model="txnForm.amount" :min="0.01" :precision="2" :step="100" style="width: 100%" />
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker v-model="txnForm.record_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="txnForm.remark" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="txnVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveTxn">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Money, School, Location, Phone, QuestionFilled } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const overview = ref(null)
const items = ref([])
const uncategorized = ref(null)
const txns = ref([])
const teachers = ref([])
const filterCampus = ref(null)
const filterKind = ref(null)

const campusVisible = ref(false)
const headVisible = ref(false)
const txnVisible = ref(false)
const saving = ref(false)
const headCampus = ref(null)
const headMode = ref('select')
const headUserId = ref(null)
const headNew = reactive({ name: '', username: '', password: '', phone: '' })

const canManage = computed(() => overview.value?.can_manage ?? userStore.isPrincipal)
const summary = computed(() => overview.value?.summary)

const emptyCampus = () => ({ id: null, name: '', address: '', phone: '', remark: '', status: true })
const campusForm = reactive(emptyCampus())
const txnForm = reactive({ campus_id: null, kind: 'income', category: '', amount: null, record_date: '', remark: '' })

const INCOME_CATS = ['餐费', '杂费', '其他']
const EXPENSE_CATS = ['房租', '工资', '水电', '其他']
const categoryOptions = computed(() => (txnForm.kind === 'income' ? INCOME_CATS : EXPENSE_CATS))

const balanceColor = computed(() => {
  const b = summary.value?.month_balance ?? 0
  return b >= 0 ? 'var(--success)' : 'var(--danger)'
})

function fmt(n) {
  return (n ?? 0).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function campusName(id) {
  const c = items.value.find((x) => x.id === id)
  return c ? c.name : ''
}

async function loadAll() {
  overview.value = await request.get('/campuses')
  items.value = overview.value.items || []
  uncategorized.value = overview.value.uncategorized || null
  if (userStore.isPrincipal) {
    teachers.value = await request.get('/auth/teachers')
  }
}

async function loadTxns() {
  const params = {}
  if (filterCampus.value != null) params.campus_id = filterCampus.value
  if (filterKind.value) params.kind = filterKind.value
  txns.value = await request.get('/campuses/transactions', { params })
}

// ===== 校区设置 =====
function openCampus(c) {
  Object.assign(campusForm, emptyCampus(), c ? { id: c.id, name: c.name, address: c.address || '', phone: c.phone || '', remark: c.remark || '', status: c.status } : {})
  campusVisible.value = true
}

async function handleSaveCampus() {
  if (!campusForm.name.trim()) {
    ElMessage.warning('请输入校区名称')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: campusForm.name.trim(),
      address: campusForm.address || null,
      phone: campusForm.phone || null,
      remark: campusForm.remark || null,
    }
    if (campusForm.id) {
      payload.status = campusForm.status
      await request.put(`/campuses/${campusForm.id}`, payload)
      ElMessage.success('校区已更新')
    } else {
      await request.post('/campuses', payload)
      ElMessage.success('校区已创建')
    }
    campusVisible.value = false
    loadAll()
  } finally {
    saving.value = false
  }
}

async function handleDeleteCampus(c) {
  await ElMessageBox.confirm(`确定删除校区「${c.name}」吗？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/campuses/${c.id}`)
    ElMessage.success('已删除')
    loadAll()
  } catch (e) {
    // 后端返回的禁止原因直接展示
  }
}

// ===== 负责人 =====
function openHead(c) {
  headCampus.value = c
  headMode.value = 'select'
  headUserId.value = c.head?.id ?? null
  Object.assign(headNew, { name: '', username: '', password: '', phone: '' })
  headVisible.value = true
}

async function handleSaveHead() {
  if (headMode.value === 'create') {
    if (!headNew.name.trim()) {
      ElMessage.warning('请输入负责人姓名')
      return
    }
    if (!headNew.username.trim()) {
      ElMessage.warning('请输入登录账号')
      return
    }
    if (!headNew.password || headNew.password.length < 6) {
      ElMessage.warning('密码至少 6 位')
      return
    }
  }
  saving.value = true
  try {
    const payload =
      headMode.value === 'create'
        ? {
            username: headNew.username.trim(),
            password: headNew.password,
            name: headNew.name.trim(),
            phone: headNew.phone || null,
          }
        : { user_id: headUserId.value }
    await request.post(`/campuses/${headCampus.value.id}/head`, payload)
    ElMessage.success('负责人已设置')
    headVisible.value = false
    loadAll()
  } finally {
    saving.value = false
  }
}

// ===== 收支 =====
function openTxn(c) {
  txnForm.campus_id = c?.id ?? null
  txnForm.kind = 'income'
  txnForm.category = ''
  txnForm.amount = null
  txnForm.record_date = ''
  txnForm.remark = ''
  txnVisible.value = true
}

function onKindChange() {
  txnForm.category = ''
}

async function handleSaveTxn() {
  if (!txnForm.campus_id) {
    ElMessage.warning('请选择校区')
    return
  }
  if (!txnForm.category) {
    ElMessage.warning('请选择分类')
    return
  }
  if (!txnForm.amount || txnForm.amount <= 0) {
    ElMessage.warning('请输入有效金额')
    return
  }
  if (!txnForm.record_date) {
    ElMessage.warning('请选择日期')
    return
  }
  saving.value = true
  try {
    await request.post('/campuses/transactions', {
      campus_id: txnForm.campus_id,
      kind: txnForm.kind,
      category: txnForm.category,
      amount: txnForm.amount,
      record_date: txnForm.record_date,
      remark: txnForm.remark || null,
    })
    ElMessage.success('登记成功')
    txnVisible.value = false
    loadAll()
    loadTxns()
  } finally {
    saving.value = false
  }
}

async function handleDeleteTxn(row) {
  await ElMessageBox.confirm(`确定删除这笔${row.kind === 'income' ? '收入' : '支出'}（¥${fmt(row.amount)}）吗？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/campuses/transactions/${row.id}`)
    ElMessage.success('已删除')
    loadAll()
    loadTxns()
  } catch (e) {}
}

function showDetail(c) {
  filterCampus.value = c?.id ?? null
  loadTxns()
  document.querySelector('.txn-head')?.scrollIntoView({ behavior: 'smooth' })
}

// 校长：查看某校区（或未分校区）的学生/教师列表
function goStudents(c) {
  router.push({ path: '/students', query: { campus: c?.id ?? 0 } })
}
function goTeachers(c) {
  router.push({ path: '/teachers', query: { campus: c.id } })
}

onMounted(() => {
  loadAll()
  loadTxns()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  gap: 12px;
}
.toolbar-right {
  display: flex;
  gap: 10px;
}
.result-count {
  font-size: 13px;
  color: var(--text-secondary);
  margin-left: 10px;
}
.result-count b {
  color: var(--primary);
  font-size: 15px;
}
.btn-add {
  --el-button-bg-color: #10b981;
  --el-button-border-color: #10b981;
  --el-button-hover-bg-color: #059669;
  --el-button-hover-border-color: #059669;
  --el-button-active-bg-color: #047857;
  --el-button-active-border-color: #047857;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}
.campus-card {
  background: #fff;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.25s;
}
.campus-card:hover {
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.08);
  border-color: var(--primary-light);
  transform: translateY(-2px);
}
.campus-card.is-disabled {
  opacity: 0.7;
}
.campus-card.is-uncat {
  border-style: dashed;
  background: #fafafa;
}
.cc-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.cc-title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.cc-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: var(--primary-lighter);
  color: var(--primary-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.cc-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cc-head-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.cc-meta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 12px;
}
.cc-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.cc-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}
.cc-stat {
  flex: 1;
  background: var(--bg);
  border-radius: 10px;
  padding: 10px 12px;
}
.cs-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.cs-value {
  font-size: 16px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--text);
}
.amount.is-expense {
  color: var(--danger);
}
.cc-info {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}
.cc-info b {
  color: var(--text);
  font-size: 13px;
}
.cc-info .linkable {
  cursor: pointer;
  color: var(--primary);
  font-weight: 500;
  transition: opacity 0.2s;
}
.cc-info .linkable:hover {
  opacity: 0.75;
  text-decoration: underline;
}
.unpaid-warn {
  color: var(--danger);
  font-weight: 600;
}
.cc-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  border-top: 1px dashed var(--border-light);
  padding-top: 10px;
}
.mt-16 {
  margin-top: 16px;
}
.txn-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  gap: 12px;
  flex-wrap: wrap;
}
.txn-filters {
  display: flex;
  gap: 10px;
}
.head-current {
  font-weight: 600;
  color: var(--success);
}
.head-tip {
  font-size: 12px;
  color: var(--text-muted);
  background: var(--bg);
  border-radius: 8px;
  padding: 8px 12px;
}
.empty-inline {
  color: #c0c4cc;
  font-size: 12px;
}
</style>
