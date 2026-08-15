<template>
  <div class="login-container">
    <div class="login-bg-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>
    <div class="login-card">
      <div class="card-accent"></div>

      <div class="login-header">
        <div class="login-icon">
          <el-icon :size="36"><Reading /></el-icon>
        </div>
        <h2>托管学堂</h2>
        <p class="login-subtitle">教学机构后台管理系统</p>
        <span class="login-badge">ADMIN CONSOLE</span>
      </div>

      <div class="form-divider"><span>账号登录</span></div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入账号" :prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-tip">
        <el-icon class="tip-icon"><InfoFilled /></el-icon>
        <span>如需开通机构账号，请联系平台管理员</span>
      </div>

      <div class="login-footer">© {{ currentYear }} 托管学堂 · 教务管理系统</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)

// 纯展示：页脚年份
const currentYear = new Date().getFullYear()

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login(form.username, form.password)
      ElMessage.success('登录成功')
      router.push(userStore.isPlatform ? '/platform' : '/dashboard')
    } catch (e) {
      // 错误已由拦截器处理
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(1100px 560px at 88% -12%, rgba(16, 185, 129, 0.16), transparent 60%),
    radial-gradient(900px 520px at -8% 112%, rgba(139, 92, 246, 0.07), transparent 55%),
    linear-gradient(135deg, #ecfdf5 0%, #d1fae5 30%, #f0fdf4 60%, #f9fafb 100%);
  position: relative;
  overflow: hidden;
}
/* 淡网格底纹 */
.login-container::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(16, 185, 129, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 185, 129, 0.045) 1px, transparent 1px);
  background-size: 44px 44px;
  -webkit-mask-image: radial-gradient(ellipse at center, #000 0%, transparent 75%);
  mask-image: radial-gradient(ellipse at center, #000 0%, transparent 75%);
  pointer-events: none;
}
.login-bg-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
}
.shape-1 {
  width: 500px;
  height: 500px;
  background: var(--primary);
  top: -100px;
  right: -120px;
  animation: float 8s ease-in-out infinite;
}
.shape-2 {
  width: 300px;
  height: 300px;
  background: var(--primary-400);
  bottom: -60px;
  left: -80px;
  animation: float 6s ease-in-out infinite reverse;
}
.shape-3 {
  width: 200px;
  height: 200px;
  background: var(--primary-dark);
  top: 50%;
  left: 15%;
  animation: float 7s ease-in-out infinite 2s;
}
@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-20px) scale(1.05); }
}
.login-card {
  width: 420px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.85);
  border-radius: 20px;
  padding: 44px 40px 30px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.12), 0 4px 18px rgba(16, 185, 129, 0.08);
  position: relative;
  z-index: 1;
  animation: cardIn 0.5s ease-out;
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
/* 卡片顶部渐变装饰条 */
.card-accent {
  position: absolute;
  top: 0;
  left: 40px;
  right: 40px;
  height: 4px;
  border-radius: 0 0 4px 4px;
  background: linear-gradient(90deg, var(--primary), var(--primary-400), #8b5cf6);
}
.login-header {
  text-align: center;
  margin-bottom: 26px;
}
.login-icon {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin: 0 auto 16px;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
}
/* 图标外扩光圈 */
.login-icon::after {
  content: '';
  position: absolute;
  inset: -6px;
  border-radius: 20px;
  border: 2px solid rgba(16, 185, 129, 0.25);
  animation: iconPulse 2.6s ease-out infinite;
}
@keyframes iconPulse {
  0% { transform: scale(0.92); opacity: 0.9; }
  70%, 100% { transform: scale(1.28); opacity: 0; }
}
.login-header h2 {
  font-size: 25px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 6px;
  letter-spacing: 1px;
}
.login-subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}
.login-badge {
  display: inline-block;
  margin-top: 12px;
  padding: 3px 12px;
  border-radius: 999px;
  background: var(--primary-lighter);
  border: 1px solid var(--primary-light);
  color: var(--primary-dark);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1.5px;
}
/* 表单区标题分隔线 */
.form-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 26px;
  color: var(--text-muted);
  font-size: 12px;
  letter-spacing: 1px;
}
.form-divider::before,
.form-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border));
}
.form-divider::after {
  background: linear-gradient(90deg, var(--border), transparent);
}
/* 输入框圆角与聚焦光环 */
:deep(.el-input__wrapper) {
  padding: 4px 14px;
  border-radius: 10px !important;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--primary) inset, 0 4px 14px rgba(16, 185, 129, 0.12) !important;
}
:deep(.el-input__inner)::placeholder {
  color: var(--text-muted);
}
.login-btn {
  width: 100%;
  height: 46px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 4px;
  border-radius: 10px !important;
  border: none !important;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.28);
}
.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(16, 185, 129, 0.36);
}
.login-btn:active {
  transform: translateY(0);
}
.login-btn.is-loading {
  opacity: 0.85;
}
.login-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 22px;
  padding: 10px 16px;
  border-radius: 10px;
  background: var(--bg);
  border: 1px dashed var(--border);
  color: var(--text-secondary);
  font-size: 12.5px;
}
.tip-icon {
  color: var(--info);
  font-size: 14px;
  flex-shrink: 0;
}
.login-footer {
  margin-top: 20px;
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
  letter-spacing: 0.5px;
}
</style>