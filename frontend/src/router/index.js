import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/views/Login.vue') },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: () => {
      const store = useUserStore()
      return store.isPlatform ? '/platform' : '/dashboard'
    },
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '工作台' } },
      // 学生管理
      { path: 'students', name: 'students', component: () => import('@/views/StudentList.vue'), meta: { title: '学生管理' } },
      // 已删除学生（校长）
      { path: 'deleted-students', name: 'deleted-students', component: () => import('@/views/DeletedStudents.vue'), meta: { title: '已删除学生', roles: ['principal'] } },
      // 收费管理（校长）
      { path: 'income', name: 'income', component: () => import('@/views/IncomeManage.vue'), meta: { title: '收费管理', roles: ['principal'] } },
      // 教师账号管理（校长）
      { path: 'teachers', name: 'teachers', component: () => import('@/views/TeacherManage.vue'), meta: { title: '教师管理', roles: ['principal'] } },
      // 学科管理（校长）
      { path: 'subjects', name: 'subjects', component: () => import('@/views/SubjectManage.vue'), meta: { title: '学科管理', roles: ['principal'] } },
      // 积分系统
      { path: 'points', name: 'points', component: () => import('@/views/PointsSystem.vue'), meta: { title: '积分奖励' } },
      // 平台管理（平台管理员）
      { path: 'platform', name: 'platform', component: () => import('@/views/PlatformManage.vue'), meta: { title: '机构开户管理', roles: ['platform'] } },
      // 学生学习档案（教师）
      { path: 'student/:id', name: 'student-detail', component: () => import('@/views/StudentDetail.vue'), meta: { title: '学生学习档案' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫：检查登录与角色权限
router.beforeEach((to) => {
  const userStore = useUserStore()
  if (to.name === 'login') {
    return true
  }
  if (!userStore.isLoggedIn) {
    return { name: 'login' }
  }
  const roles = to.meta?.roles
  if (roles && !roles.includes(userStore.user?.role)) {
    return { name: 'dashboard' }
  }
  return true
})

export default router