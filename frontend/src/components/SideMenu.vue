<template>
  <el-menu
    :default-active="activeMenu"
    :collapse="collapse"
    router
    class="menu"
    :collapse-transition="false"
  >
    <template v-if="userStore.isPlatform">
      <el-menu-item index="/platform">
        <el-icon><OfficeBuilding /></el-icon>
        <span>机构开户管理</span>
      </el-menu-item>
    </template>
    <template v-else>
      <el-menu-item index="/dashboard">
        <el-icon><Odometer /></el-icon>
        <span>工作台</span>
      </el-menu-item>
      <el-menu-item index="/students">
        <el-icon><User /></el-icon>
        <span>学生管理</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.isPrincipal || userStore.isSubPrincipal" index="/income">
        <el-icon><Money /></el-icon>
        <span>收费管理</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.isPrincipal || userStore.isSubPrincipal" index="/teachers">
        <el-icon><Avatar /></el-icon>
        <span>教师管理</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.isPrincipal || userStore.isSubPrincipal" index="/subjects">
        <el-icon><Grid /></el-icon>
        <span>学科管理</span>
      </el-menu-item>
      <el-menu-item index="/points">
        <el-icon><Trophy /></el-icon>
        <span>积分奖励</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.isPrincipal || userStore.isSubPrincipal" index="/campuses">
        <el-icon><School /></el-icon>
        <span>校区管理</span>
      </el-menu-item>
    </template>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  OfficeBuilding,
  Odometer,
  User,
  Money,
  Avatar,
  Grid,
  Trophy,
  School,
} from '@element-plus/icons-vue'

defineProps({
  collapse: { type: Boolean, default: false },
})

const route = useRoute()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.menu {
  border-right: none !important;
  flex: 1;
  padding: 8px;
}
.menu :deep(.el-menu-item) {
  border-radius: 10px;
  margin: 2px 0;
  height: 44px;
  line-height: 44px;
  color: var(--text-secondary);
  transition: all 0.2s;
  font-weight: 500;
  font-size: 14px;
}
.menu :deep(.el-menu-item:hover) {
  background: var(--primary-lighter);
  color: var(--primary);
}
.menu :deep(.el-menu-item.is-active) {
  background: var(--primary-lighter);
  color: var(--primary);
  font-weight: 600;
}
.menu :deep(.el-menu-item .el-icon) {
  font-size: 18px;
}
</style>
