<template>
  <div class="page-container">
    <el-row :gutter="16">
      <!-- 排行榜 -->
      <el-col :span="9">
        <el-card shadow="never">
          <template #header><span>积分排行榜</span></template>
          <div v-if="leaderboard.length === 0" class="empty-hint">暂无学生数据</div>
          <div v-else class="rank-list">
            <div v-for="(item, idx) in leaderboard" :key="item.id" class="rank-row">
              <span class="rank-badge" :class="idx === 0 ? 'is-top1' : idx === 1 ? 'is-top2' : idx === 2 ? 'is-top3' : ''">{{ idx + 1 }}</span>
              <div class="rank-main">
                <span class="rank-name">{{ item.name }}</span>
                <div class="mini-progress">
                  <div class="mp-track">
                    <div class="mp-bar" :class="pointsBarClass(item.points)" :style="{ width: pointsPct(item.points) + '%' }"></div>
                  </div>
                  <span class="mp-text">{{ item.points }} 分</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 积分操作与奖品 -->
      <el-col :span="15">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><span>积分加扣</span></template>
          <!-- 学生积分概览（纯展示，基于 students 计算） -->
          <div class="mini-stats points-stats">
            <div class="mini-stat">
              <div class="ms-label">学生总数</div>
              <div class="ms-value">{{ studentStats.total }}</div>
              <div class="ms-sub">当前可选学生</div>
            </div>
            <div class="mini-stat">
              <div class="ms-label">平均积分</div>
              <div class="ms-value">{{ studentStats.avg }}</div>
              <div class="ms-sub">全体学生均值</div>
            </div>
            <div class="mini-stat">
              <div class="ms-label">最高积分</div>
              <div class="ms-value is-max">{{ studentStats.max }}</div>
              <div class="ms-sub">榜首：{{ studentStats.top }}</div>
            </div>
          </div>
          <el-form inline>
            <el-form-item label="学生">
              <el-select v-model="changeForm.student_id" filterable placeholder="选择学生" style="width:170px">
                <el-option v-for="s in students" :key="s.id" :label="`${s.name}(${s.points}分)`" :value="s.id">
                  <div class="student-opt">
                    <span>{{ s.name }}</span>
                    <span class="opt-points">{{ s.points }} 分</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="积分变动">
              <el-input-number v-model="changeForm.change" :step="5" />
            </el-form-item>
            <el-form-item label="类别">
              <el-select v-model="changeForm.category" style="width:120px">
                <el-option label="表现" value="表现" />
                <el-option label="作业" value="作业" />
                <el-option label="成绩" value="成绩" />
                <el-option label="纪律" value="纪律" />
              </el-select>
            </el-form-item>
            <el-form-item label="原因">
              <el-input v-model="changeForm.reason" placeholder="如：作业优秀" style="width:160px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveChange">确认</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>积分记录</span>
              <el-button size="small" type="primary" :icon="Plus" @click="prizeVisible = true">管理奖品</el-button>
            </div>
          </template>
          <el-table :data="records" size="small" stripe max-height="360">
            <el-table-column prop="student_name" label="学生" width="90" />
            <el-table-column prop="change" label="变动" width="80">
              <template #default="{ row }">
                <span class="amount" :class="{ 'is-income': row.change > 0 }">
                  {{ row.change > 0 ? '+' : '' }}{{ row.change }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="类别" width="86">
              <template #default="{ row }">
                <el-tag size="small" effect="plain" :type="categoryType(row.category)">{{ row.category }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="原因" show-overflow-tooltip />
            <el-table-column prop="created_at" label="时间" width="160">
              <template #default="{ row }">{{ (row.created_at || '').slice(0, 16) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 奖品管理对话框 -->
    <el-dialog v-model="prizeVisible" title="奖品管理" width="700px">
      <div class="prize-add">
        <el-input v-model="prizeForm.name" placeholder="奖品名称" style="width:130px" />
        <el-input-number v-model="prizeForm.cost_points" :min="1" placeholder="所需积分" />
        <el-input-number v-model="prizeForm.stock" :min="-1" placeholder="库存(-1不限)" />
        <el-button type="primary" @click="addPrize">添加奖品</el-button>
      </div>
      <el-table :data="prizes" size="small" stripe>
        <el-table-column prop="name" label="奖品" />
        <el-table-column prop="cost_points" label="所需积分" width="100">
          <template #default="{ row }">
            <span class="num-strong">{{ row.cost_points }} <span class="cost-unit">分</span></span>
          </template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.stock === -1" size="small" type="info" effect="plain">不限</el-tag>
            <span v-else class="num-strong" :class="{ 'stock-low': row.stock <= 0 }">{{ row.stock }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="id" label="兑换" width="140">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="redeemFor(row)">为学生兑换</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 为学生兑换奖品对话框（下拉选择） -->
    <el-dialog v-model="redeemVisible" title="为学生兑换奖品" width="420px">
      <el-form label-width="70px">
        <el-form-item label="奖品">
          <el-tag type="warning">{{ redeemTarget?.name }}</el-tag>
          <span style="margin-left:8px;color:#909399">需 {{ redeemTarget?.cost_points }} 分</span>
        </el-form-item>
        <el-form-item label="学生" required>
          <el-select v-model="redeemStudentId" filterable placeholder="搜索或选择学生" style="width:100%">
            <el-option v-for="s in students" :key="s.id" :label="`${s.name}（${s.points}分）`" :value="s.id">
              <div class="student-opt">
                <span>{{ s.name }}</span>
                <span class="opt-points">{{ s.points }} 分</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="redeemVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRedeem">确认兑换</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'

const leaderboard = ref([])
const students = ref([])
const records = ref([])
const prizes = ref([])
const prizeVisible = ref(false)
const redeemVisible = ref(false)
const redeemTarget = ref(null)
const redeemStudentId = ref(null)

const changeForm = reactive({ student_id: null, change: 5, category: '表现', reason: '' })
const prizeForm = reactive({ name: '', cost_points: 10, stock: -1 })

// ===== 纯展示统计/格式化（不参与任何业务逻辑，仅用于界面展示） =====
const studentStats = computed(() => {
  const list = students.value
  if (!list.length) return { total: 0, avg: 0, max: 0, top: '-' }
  const points = list.map((s) => Number(s.points) || 0)
  const max = Math.max(...points)
  const top = (list.find((s) => Number(s.points) === max) || {}).name || '-'
  const avg = Math.round(points.reduce((a, b) => a + b, 0) / points.length)
  return { total: list.length, avg, max, top }
})

const maxPoints = computed(() => leaderboard.value.reduce((m, i) => Math.max(m, Number(i.points) || 0), 0))

function pointsPct(p) {
  if (!maxPoints.value) return 0
  return Math.max(2, Math.round(((Number(p) || 0) / maxPoints.value) * 100))
}

function pointsBarClass(p) {
  const v = Number(p) || 0
  const ratio = maxPoints.value ? v / maxPoints.value : 0
  if (ratio < 0.4) return 'is-danger'
  if (ratio < 0.7) return 'is-warn'
  return ''
}

function categoryType(cat) {
  return { 表现: 'success', 作业: 'primary', 成绩: 'warning', 纪律: 'danger' }[cat] || 'info'
}

async function loadAll() {
  leaderboard.value = await request.get('/points/leaderboard')
  students.value = await request.get('/students')
  records.value = await request.get('/points/records')
  prizes.value = await request.get('/points/prizes')
}

async function saveChange() {
  if (!changeForm.student_id) return ElMessage.warning('请选择学生')
  await request.post('/points/change', changeForm)
  ElMessage.success('积分已更新')
  Object.assign(changeForm, { student_id: null, change: 5, category: '表现', reason: '' })
  loadAll()
}

async function addPrize() {
  if (!prizeForm.name) return ElMessage.warning('请输入奖品名称')
  await request.post('/points/prizes', prizeForm)
  ElMessage.success('奖品已添加')
  Object.assign(prizeForm, { name: '', cost_points: 10, stock: -1 })
  loadAll()
}

function redeemFor(prize) {
  redeemTarget.value = prize
  redeemStudentId.value = null
  redeemVisible.value = true
}

async function confirmRedeem() {
  if (!redeemStudentId.value) return ElMessage.warning('请选择学生')
  await request.post('/points/redeem', { student_id: redeemStudentId.value, prize_id: redeemTarget.value.id })
  ElMessage.success('兑换成功')
  redeemVisible.value = false
  loadAll()
}

onMounted(loadAll)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.rank-list {
  display: flex;
  flex-direction: column;
}
.rank-main {
  flex: 1;
  min-width: 0;
}
.rank-main .rank-name {
  display: block;
  margin-bottom: 4px;
}

/* 学生积分概览 */
.points-stats {
  margin-bottom: 16px;
}
.points-stats .ms-value.is-max {
  color: var(--warning);
}

/* 学生下拉选项：姓名 + 积分高亮 */
.student-opt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
.student-opt .opt-points {
  color: var(--warning);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
}

/* 奖品表格数字辅助 */
.cost-unit {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 400;
}
.stock-low {
  color: var(--danger);
}

/* 积分加扣表单间距优化 */
:deep(.el-form--inline .el-form-item) {
  margin-right: 14px;
}
:deep(.el-form--inline .el-form-item:last-child) {
  margin-right: 0;
}

/* 奖品管理区域优化 */
.prize-add {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.prize-add .el-input,
.prize-add .el-input-number {
  flex-shrink: 0;
}
</style>