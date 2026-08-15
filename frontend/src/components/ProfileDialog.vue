<template>
  <el-dialog v-model="visible" title="个人资料" width="560px" :close-on-click-modal="false">
    <el-tabs v-model="activeTab">
      <!-- 基本资料 -->
      <el-tab-pane label="基本资料" name="info">
        <div class="avatar-row">
          <el-avatar :size="72" class="avatar-big" :src="avatarUrl">
            {{ (form.name || userStore.user?.name || '?')[0] }}
          </el-avatar>
          <div class="avatar-actions">
            <el-upload
              :show-file-list="false"
              :http-request="handleAvatarUpload"
              accept="image/*"
            >
              <el-button size="small" :icon="Upload">上传头像</el-button>
            </el-upload>
            <div class="avatar-tip">支持 png/jpg/jpeg/gif/webp，≤5MB</div>
          </div>
        </div>

        <el-form :model="form" label-width="80px" style="margin-top: 16px">
          <el-form-item label="账号">
            <el-input :model-value="profile.username" disabled />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="form.name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="电话">
            <el-input v-model="form.phone" placeholder="请输入联系电话" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="角色">
            <el-tag :type="roleType">{{ roleText }}</el-tag>
          </el-form-item>
        </el-form>
        <div class="dialog-footer">
          <el-button @click="visible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSaveInfo">保存资料</el-button>
        </div>
      </el-tab-pane>

      <!-- 修改密码 -->
      <el-tab-pane label="修改密码" name="password">
        <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px" style="margin-top: 8px">
          <el-form-item label="原密码" prop="old_password">
            <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入原密码" />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少 6 位" />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirm">
            <el-input v-model="pwdForm.confirm" type="password" show-password placeholder="再次输入新密码" />
          </el-form-item>
        </el-form>
        <div class="dialog-footer">
          <el-button @click="visible = false">取消</el-button>
          <el-button type="primary" :loading="savingPwd" @click="handleSavePwd">确认修改</el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const visible = defineModel({ type: Boolean, default: false })

const activeTab = ref('info')
const saving = ref(false)
const savingPwd = ref(false)
const pwdFormRef = ref()

const profile = ref({})
const form = reactive({ name: '', phone: '', email: '' })
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })

const avatarUrl = computed(() => profile.value.avatar || userStore.user?.avatar || '')

const roleType = computed(() => {
  const r = userStore.user?.role
  if (r === 'platform') return 'danger'
  if (r === 'principal') return 'danger'
  if (r === 'sub_principal' || r === 'campus_head') return 'success'
  return 'primary'
})
const roleText = computed(() => {
  const r = userStore.user?.role
  if (r === 'platform') return '平台管理员'
  if (r === 'principal') return '总校长'
  if (r === 'sub_principal' || r === 'campus_head') return '校长管理号'
  return '教师'
})

const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, cb) => {
        if (value !== pwdForm.new_password) cb(new Error('两次输入的密码不一致'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
}

async function loadProfile() {
  const data = await request.get('/profile')
  profile.value = data
  form.name = data.name || ''
  form.phone = data.phone || ''
  form.email = data.email || ''
}

async function handleAvatarUpload({ file }) {
  const fd = new FormData()
  fd.append('file', file)
  const data = await request.post('/profile/avatar', fd)
  profile.value.avatar = data.url
  form.avatar = data.url
  ElMessage.success('头像上传成功')
}

async function handleSaveInfo() {
  saving.value = true
  try {
    const data = await request.put('/profile', {
      name: form.name,
      phone: form.phone,
      email: form.email,
      avatar: form.avatar,
    })
    profile.value = data
    // 同步到本地用户信息
    userStore.user = { ...userStore.user, ...data }
    localStorage.setItem('user', JSON.stringify(userStore.user))
    ElMessage.success('资料已保存')
    visible.value = false
  } finally {
    saving.value = false
  }
}

async function handleSavePwd() {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  savingPwd.value = true
  try {
    await request.put('/profile/password', {
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm = ''
    userStore.logout()
    window.location.href = '/login'
  } finally {
    savingPwd.value = false
  }
}

watch(visible, (v) => {
  if (v) {
    activeTab.value = 'info'
    loadProfile()
  }
})
</script>

<style scoped>
.avatar-row {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 8px 0;
}
.avatar-big {
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff;
  font-size: 28px;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
}
.avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.avatar-tip {
  font-size: 12px;
  color: #909399;
}
.dialog-footer {
  text-align: right;
  margin-top: 8px;
}
</style>