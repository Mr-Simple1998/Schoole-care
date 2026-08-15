<template>
  <div class="page-container">
    <el-card shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input v-model="keyword" placeholder="搜索姓名/电话" clearable style="width: 220px" @input="handleSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>
        <el-button :icon="Refresh" @click="loadList">刷新</el-button>
      </div>

      <el-table :data="filteredList" stripe>
        <el-table-column prop="student_no" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="130" />
        <el-table-column prop="school" label="学校" width="160">
          <template #default="{ row }">
            <span>{{ row.school || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="guardian_name" label="监护人" width="130">
          <template #default="{ row }">
            <span>{{ row.guardian_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="guardian_phone" label="联系电话" width="160">
          <template #default="{ row }">
            <span>{{ row.guardian_phone || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="grade" label="年级" width="120">
          <template #default="{ row }">
            <span>{{ row.grade || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default>
            <el-tag type="info" size="small">已删除</el-tag>
          </template>
        </el-table-column>
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
</style>