<template>
  <div class="page-container">
    <el-row :gutter="16">
      <!-- 排行榜 -->
      <el-col :span="9">
        <el-card shadow="never">
          <template #header><span>积分排行榜</span></template>
          <div v-if="leaderboard.length === 0" class="empty">暂无学生数据</div>
          <div v-else class="rank-list">
            <div
              v-for="(item, idx) in leaderboard"
              :key="item.id"
              class="rank-item"
              :class="idx === 0 ? 'rank-gold' : idx === 1 ? 'rank-silver' : idx === 2 ? 'rank-bronze' : ''"
            >
              <span class="rank-no" :class="`rank-${idx + 1}`">{{ idx + 1 }}</span>
              <span class="rank-name">{{ item.name }}</span>
              <span class="rank-points">{{ item.points }} 分</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 积分操作与奖品 -->
      <el-col :span="15">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><span>积分加扣</span></template>
          <el-form inline>
            <el-form-item label="学生">
              <el-select v-model="changeForm.student_id" filterable placeholder="选择学生" style="width:170px">
                <el-option v-for="s in students" :key="s.id" :label="`${s.name}(${s.points}分)`" :value="s.id" />
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
                <span :style="{ color: row.change > 0 ? '#67c23a' : '#f56c6c', fontWeight: 600 }">
                  {{ row.change > 0 ? '+' : '' }}{{ row.change }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="类别" width="80" />
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
        <el-table-column prop="cost_points" label="所需积分" width="100" />
        <el-table-column prop="stock" label="库存" width="80">
          <template #default="{ row }">{{ row.stock === -1 ? '不限' : row.stock }}</template>
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
            <el-option v-for="s in students" :key="s.id" :label="`${s.name}（${s.points}分）`" :value="s.id" />
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
import { ref, reactive, onMounted } from 'vue'
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
  gap: 8px;
}
.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 6px;
  background: #f5f7fa;
}
.rank-gold {
  background: linear-gradient(135deg, #fef3c7, #fde68a, #fef3c7);
  border: 1px solid #f59e0b;
}
.rank-silver {
  background: linear-gradient(135deg, #f1f5f9, #cbd5e1, #f1f5f9);
  border: 1px solid #94a3b8;
}
.rank-bronze {
  background: linear-gradient(135deg, #fef2f2, #fecaca, #fef2f2);
  border: 1px solid #d97706;
}
.rank-no {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  background: #c0c4cc;
  color: #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}
.rank-1 { background: #f59e0b; }
.rank-2 { background: #94a3b8; }
.rank-3 { background: #d97706; }
.rank-name {
  flex: 1;
  font-weight: 500;
}
.rank-points {
  color: #e6a23c;
  font-weight: 600;
}
.empty {
  text-align: center;
  color: #909399;
  padding: 30px 0;
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