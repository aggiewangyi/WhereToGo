<template>
  <div class="mx-auto flex min-h-[calc(100vh-3.25rem)] max-w-md flex-col justify-center px-4 py-12">
    <div class="mb-8 text-center">
      <h2 class="font-display text-xl font-semibold text-white">欢迎回来</h2>
      <p class="mt-1 text-sm text-slate-500">登录后继续你的旅行对话</p>
    </div>
    <div class="rounded-2xl border border-white/[0.08] bg-slate-950/70 p-6 shadow-panel backdrop-blur-sm">
      <el-form label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="手机号">
          <el-input v-model="phone" maxlength="20" placeholder="11 位手机号" clearable />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" placeholder="密码" show-password @keyup.enter="onSubmit" />
        </el-form-item>
        <el-button class="w-full submit-btn" :loading="submitting" native-type="submit" @click="onSubmit">
          登录
        </el-button>
      </el-form>
      <p class="mt-4 text-center text-xs text-slate-500">
        还没有账号？
        <RouterLink to="/register" class="text-teal-400 hover:text-teal-300">注册</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const phone = ref('')
const password = ref('')
const submitting = ref(false)

async function onSubmit() {
  if (!phone.value.trim() || !password.value) {
    ElMessage.warning('请填写手机号和密码')
    return
  }
  submitting.value = true
  try {
    await userStore.login(phone.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect || '/')
  } catch {
    ElMessage.error('登录失败，请检查手机号与密码')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
:deep(.el-form-item__label) {
  color: rgba(148, 163, 184, 0.95) !important;
  font-size: 12px;
}
:deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.65) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08) inset !important;
}
.submit-btn {
  border-radius: 12px !important;
  border: 1px solid rgba(45, 212, 191, 0.45) !important;
  background: linear-gradient(165deg, rgba(45, 212, 191, 0.25), rgba(15, 118, 110, 0.4)) !important;
  color: rgb(204, 251, 241) !important;
  font-weight: 600;
}
</style>
