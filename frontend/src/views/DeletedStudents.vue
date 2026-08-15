<template>
  <div class="page-container">
    <el-card shadow="never">
      <!-- 顶部说明横幅（纯展示） -->
      <div v-if="totalDeleted > 0" class="banner is-danger">
        <span class="banner-emoji">🗑️</span>
        <div>
          <div class="banner-title">已删除学生档案</div>
          <div class="banner-desc">以下学生已移出在读名单，档案将保留用于收费记录与历史核对，仅校长可见。</div>
        </div>
      </div>

      <!-- 数据概览（纯展示，基于现有数据计算） -->
      <div v-if="totalDeleted > 0" class="mini-stats mb-16">
        <div class="mini-stat">
          <div class="ms-label">🗑️ 已删除总数</div>
          <div class="ms-value" style="color: var(--danger)">{{ totalDeleted }}</div>
          <div class="ms-sub">软删除归档学生</div>
        </div>
        <div class="mini-stat">
          <div class="ms-label">🏫 覆盖学校</div>
          <div class="ms-value" style="color: var(--info)">{{ schoolCount }}</div>
          <div class="ms-sub">来自 {{ schoolCount }} 所学校</div>
        </div>
        <div class="mini-stat">
          <div class="ms-label">📞 留有联系方式</div>
          <div class="ms-value" style="color: var(--success)">{{ contactCount }}</div>
          <div class="ms-sub">联系覆盖率 {{ contactRate }}%</div>
        </div>
        <div class="mini-stat">
          <div class="ms-label">⭐ 积分合计</div>
          <div class="ms-value" style="color: var(--warning)">{{ totalPoints }}</div>
          <div class="ms-sub">历史累计积分</div>
        </div>
      </div>

      <div class="toolbar">
        <div class="toolbar-left">
          <el-input v-model="keyword" placeholder="搜索姓名/电话" clearable style="width: 220px" @input="handleSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <span class="result-count">
            共 <b>{{ filteredList.length }}</b> 条记录<template v-if="isSearching">（已删除总数 {{ totalDeleted }}）</template>
          </span>
        </div>
        <el-button :icon="Refresh" @click="loadList">刷新</el-button>
      </div>

      <el-table :data="filteredList" stripe>
        <el-table-column prop="student_no" label="学号" width="110">
          <template #default="{ row }">
            <span class="student-no">{{ row.student_no || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="姓名" width="110">
          <template #default="{ row }">
            <span class="student-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="年级 / 班级" width="140">
          <template #default="{ row }">
            <div class="grade-cell">
              <span class="grade-chip">{{ row.grade || '—' }}</span>
              <span v-if="row.class_name" class="class-sub">{{ row.class_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="school" label="学校" width="150">
          <template #default="{ row }">
            <span v-if="row.school" class="school-cell">{{ row.school }}</span>
            <span v-else class="empty-inline">未设置</span>
          </template>
        </el-table-column>
        <el-table-column label="监护人" width="160">
          <template #default="{ row }">
            <div v-if="row.guardian_name || row.guardian_phone" class="guardian-cell">
              <span class="guardian-name">{{ row.guardian_name || '—' }}</span>
              <span v-if="row.guardian_phone" class="guardian-phone">{{ row.guardian_phone }}</span>
            </div>
            <span v-else class="empty-inline">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="enrollment_date" label="入学日期" width="130">
          <template #default="{ row }">
            <span v-if="row.enrollment_date" class="date-chip">{{ row.enrollment_date }}</span>
            <span v-else class="empty-inline">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="points" label="积分" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.points > 0" class="points-num">★ {{ row.points }}</span>
            <span v-else class="empty-inline">0</span>
          </template>
        </el-table-column>
        <el-table-column label="负责教师" width="110">
          <template #default="{ row }">
            <span v-if="row.teacher_name" class="teacher-cell">
              <span class="teacher-avatar">{{ row.teacher_name[0] }}</span>{{ row.teacher_name }}
            </span>
            <span v-else class="empty-inline">未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <div class="status-cell">
              <span class="status-dot" :class="statusDotClass(row.status)">{{ row.status || '未知' }}</span>
              <el-tag type="danger" size="small" effect="dark">已删除</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="notes" label="备注" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.notes" class="notes-cell">{{ row.notes }}</span>
            <span v-else class="empty-inline">—</span>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :description="isSearching ? '未找到匹配的已删除学生' : '暂无已删除学生记录'" :image-size="90">
            <p v-if="!isSearching" class="empty-hint">学生被删除后会自动归档于此，用于历史查询与收费记录核对</p>
          </el-empty>
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import request from '@/utils/request'

const list = ref([])
const keyword = ref('')

const filteredList = computed(() => {
  const kw = keyword.value.trim()
  if (!kw) return list.value
  return list.value.filter(
    (s) => (s.name && s.name.includes(kw)) || (s.guardian_phone && s.guardian_phone.includes(kw))
  )
})

// ===== 纯展示：数据概览（不改变任何业务逻辑，仅格式化展示） =====
const totalDeleted = computed(() => list.value.length)
const schoolCount = computed(() => new Set(list.value.map((s) => s.school).filter(Boolean)).size)
const contactCount = computed(() => list.value.filter((s) => s.guardian_phone).length)
const totalPoints = computed(() => list.value.reduce((sum, s) => sum + (Number(s.points) || 0), 0))
const contactRate = computed(() => (totalDeleted.value ? Math.round((contactCount.value / totalDeleted.value) * 100) : 0))
const isSearching = computed(() => keyword.value.trim() !== '')

// 状态 → 语义色圆点（在读=绿，休学=橙，退学=红，其余=蓝）
function statusDotClass(status) {
  if (status === '在读') return 'is-success'
  if (status === '休学') return 'is-warning'
  if (status === '退学') return 'is-danger'
  return 'is-info'
}

async function loadList() {
  try {
    const data = await request.get('/students/deleted')
    list.value = data || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  }
}

function handleSearch() {}

onMounted(loadList)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.toolbar-left {
  display: flex;
  gap: 12px;
}

/* ===== 数据直观化（仅展示层） ===== */
.banner-emoji {
  font-size: 18px;
  flex-shrink: 0;
}
.result-count {
  font-size: 13px;
  color: var(--text-secondary);
  margin-left: 4px;
}
.result-count b {
  color: var(--primary);
  font-size: 15px;
}
.student-no {
  font-weight: 600;
  color: var(--primary-dark);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.3px;
}
.student-name {
  font-weight: 600;
  color: var(--text);
}
.grade-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}
.grade-chip {
  background: var(--primary-lighter);
  color: var(--primary-dark);
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  white-space: nowrap;
}
.class-sub {
  font-size: 12px;
  color: var(--text-muted);
}
.school-cell {
  color: var(--text);
}
.guardian-cell {
  display: flex;
  flex-direction: column;
  line-height: 1.5;
}
.guardian-name {
  color: var(--text);
  font-size: 13px;
}
.guardian-phone {
  color: var(--text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.date-chip {
  color: var(--primary-dark);
  background: var(--primary-lighter);
  font-weight: 600;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  padding: 2px 8px;
  border-radius: 6px;
  white-space: nowrap;
}
.points-num {
  color: var(--warning);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.teacher-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.notes-cell {
  color: var(--text-secondary);
  font-size: 13px;
}
.empty-inline {
  color: #c0c4cc;
  font-size: 12px;
}
:deep(.el-table__body tr) {
  transition: background-color 0.3s ease;
}
</style>
