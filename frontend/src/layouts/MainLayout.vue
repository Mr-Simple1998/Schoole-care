<template>
  <el-container class="layout">
    <!-- 侧边栏（桌面端） -->
    <el-aside v-if="!isMobile" :width="isCollapse ? '68px' : '230px'" class="aside">
      <div class="logo">
        <div class="logo-icon">
          <el-icon :size="22"><Reading /></el-icon>
        </div>
        <span v-show="!isCollapse" class="logo-text">清禾家塾管理系统</span>
      </div>
      <SideMenu :collapse="isCollapse" />
    </el-aside>

    <!-- 侧边菜单抽屉（移动端） -->
    <el-drawer
      v-if="isMobile"
      v-model="mobileMenuVisible"
      direction="ltr"
      size="230px"
      :with-header="false"
      class="mobile-menu-drawer"
    >
      <div class="logo">
        <div class="logo-icon">
          <el-icon :size="22"><Reading /></el-icon>
        </div>
        <span class="logo-text">清禾家塾管理系统</span>
      </div>
      <SideMenu />
    </el-drawer>

    <el-container class="right">
      <!-- 顶栏 -->
      <el-header class="header">
        <div class="header-left">
          <div class="collapse-btn" @click="toggleMenu">
            <el-icon :size="18"><Menu v-if="isMobile" /><Expand v-else-if="isCollapse" /><Fold v-else /></el-icon>
          </div>
          <span class="page-title">{{ route.meta.title || '' }}</span>
        </div>
        <div class="header-right">
          <div class="header-actions">
            <el-badge :value="feeReminderCount" :hidden="!feeReminderCount" class="notice-bell" @click="openReminders">
              <el-icon :size="20"><Bell /></el-icon>
            </el-badge>
          </div>
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" class="avatar" :src="avatarUrl">
                {{ userStore.user?.name?.[0] }}
              </el-avatar>
              <span class="username">{{ userStore.user?.name }}</span>
              <el-tag size="small" effect="plain" :type="roleTagType" class="role-tag">
                {{ roleText }}
              </el-tag>
              <el-icon class="chevron"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><UserFilled /></el-icon>个人资料
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <!-- 个人资料弹窗 -->
    <ProfileDialog v-model="profileVisible" />

    <!-- 消息提醒弹窗 -->
    <el-dialog v-model="reminderVisible" title="消息提醒" width="520px" class="reminder-dialog">
      <div v-if="reminders.length" class="reminder-list">
        <div v-for="(r, i) in reminders" :key="i" class="reminder-item">
          <div class="reminder-head">
            <el-tag size="small" :type="r.remind_type === 'fee' ? 'warning' : 'primary'" effect="light">
              {{ r.remind_type === 'fee' ? '收费到期' : '学科到期' }}
            </el-tag>
            <span class="reminder-title">{{ r.student_name }} · {{ r.fee_type }}</span>
          </div>
          <div class="reminder-meta">
            <span>到期日：{{ r.expire_date }}</span>
            <span v-if="r.amount > 0">金额：¥{{ r.amount }}</span>
            <span :class="r.days_left < 0 ? 'expired' : r.days_left <= 2 ? 'urgent' : ''">
              {{ r.days_left < 0 ? `已到期 ${-r.days_left} 天` : `剩余 ${r.days_left} 天` }}
            </span>
          </div>
          <div v-if="r.teacher_name" class="reminder-teacher">负责教师：{{ r.teacher_name }}</div>
        </div>
      </div>
      <el-empty v-else description="暂无提醒" :image-size="80" />
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import ProfileDialog from '@/components/ProfileDialog.vue'
import SideMenu from '@/components/SideMenu.vue'
import { Bell, Menu } from '@element-plus/icons-vue'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)
const isMobile = ref(false)
const mobileMenuVisible = ref(false)
const profileVisible = ref(false)
const feeReminderCount = ref(0)
const reminderVisible = ref(false)
const reminders = ref([])

const avatarUrl = computed(() => userStore.user?.avatar || '')

const roleTagType = computed(() => {
  if (userStore.isPlatform) return 'danger'
  if (userStore.isPrincipal) return 'warning'
  if (userStore.isSubPrincipal) return 'success'
  return 'primary'
})
const roleText = computed(() => {
  if (userStore.isPlatform) return '平台管理员'
  if (userStore.isPrincipal) return '校长'
  if (userStore.isSubPrincipal) return '校区负责人'
  return '教师'
})

function handleCommand(command) {
  if (command === 'profile') {
    profileVisible.value = true
  } else if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}

let mql = null
function syncViewport(e) {
  isMobile.value = e.matches
  if (!e.matches) mobileMenuVisible.value = false
}
function toggleMenu() {
  if (isMobile.value) {
    mobileMenuVisible.value = true
  } else {
    isCollapse.value = !isCollapse.value
  }
}

// 路由变化时自动关闭移动端菜单抽屉
watch(
  () => route.path,
  () => {
    mobileMenuVisible.value = false
  }
)

async function loadReminders() {
  try {
    const data = await request.get('/dashboard/overview')
    reminders.value = data.fee_expire_reminders || []
    feeReminderCount.value = reminders.value.length
  } catch {}
}

function openReminders() {
  reminderVisible.value = true
}

onMounted(() => {
  mql = window.matchMedia('(max-width: 767px)')
  syncViewport(mql)
  if (mql.addEventListener) {
    mql.addEventListener('change', syncViewport)
  } else {
    mql.addListener(syncViewport)
  }
  loadReminders()
})

onBeforeUnmount(() => {
  if (mql) {
    if (mql.removeEventListener) {
      mql.removeEventListener('change', syncViewport)
    } else {
      mql.removeListener(syncViewport)
    }
  }
})
</script>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: #fff;
  border-right: 1px solid var(--border);
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}
.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.logo-text {
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  letter-spacing: -0.3px;
}
.right {
  display: flex;
  flex-direction: column;
}
.header {
  background: #fff;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.collapse-btn {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}
.collapse-btn:hover {
  background: var(--bg);
  color: var(--text);
}
.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-actions {
  display: flex;
  align-items: center;
}
.notice-bell {
  cursor: pointer;
  color: var(--text-secondary);
  padding: 6px;
  border-radius: 8px;
  transition: all 0.2s;
}
.notice-bell:hover {
  background: var(--bg);
  color: var(--text);
}

/* ========== 消息提醒弹窗 ========== */
.reminder-list {
  max-height: 420px;
  overflow-y: auto;
}
.reminder-item {
  padding: 12px 14px;
  margin-bottom: 10px;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  background: var(--bg);
}
.reminder-item:last-child {
  margin-bottom: 0;
}
.reminder-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.reminder-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}
.reminder-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 13px;
  color: var(--text-secondary);
}
.reminder-meta .expired {
  color: #f56c6c;
  font-weight: 600;
}
.reminder-meta .urgent {
  color: #e6a23c;
  font-weight: 600;
}
.reminder-teacher {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-muted);
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 10px;
  transition: all 0.2s;
}
.user-info:hover {
  background: var(--bg);
}
.avatar {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  font-weight: 600;
}
.username {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}
.role-tag {
  font-size: 11px;
}
.chevron {
  color: var(--text-muted);
  font-size: 12px;
  transition: transform 0.2s;
}
.main {
  padding: 0;
  overflow-y: auto;
  background: var(--bg-page);
}

/* ========== Page Transition ========== */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* ========== 移动端适配（≤767px） ========== */
@media (max-width: 767px) {
  .header {
    padding: 0 12px;
    height: 52px;
  }
  .username,
  .role-tag,
  .chevron {
    display: none;
  }
  .header-right {
    gap: 8px;
  }
  .logo {
    height: 56px;
    padding: 0 16px;
  }
  .mobile-menu-drawer :deep(.el-drawer__body) {
    padding: 0;
    display: flex;
    flex-direction: column;
  }
  .mobile-menu-drawer .logo {
    flex-shrink: 0;
  }
}
</style>