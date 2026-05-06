<template>
  <div class="mx-auto flex min-h-[calc(100vh-3.25rem)] max-w-md flex-col justify-center px-4 py-12">
    <div class="mb-8 text-center">
      <h2 class="font-display text-xl font-semibold text-white">创建账号</h2>
      <p class="mt-1 text-sm text-slate-500">保存对话历史，随时继续规划</p>
    </div>
    <div class="rounded-2xl border border-white/[0.08] bg-slate-950/70 p-6 shadow-panel backdrop-blur-sm">
      <el-form label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="手机号">
          <el-input v-model="phone" maxlength="20" placeholder="11 位手机号" clearable />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="nickname" maxlength="50" placeholder="怎么称呼你" clearable />
        </el-form-item>
        <el-form-item label="密码（至少 6 位）">
          <el-input v-model="password" type="password" placeholder="设置密码" show-password />
        </el-form-item>
        <el-button class="w-full submit-btn" :loading="submitting" native-type="submit" @click="onSubmit">
          注册并登录
        </el-button>
      </el-form>
      <p class="mt-4 text-center text-xs text-slate-500">
        已有账号？
        <RouterLink to="/login" class="text-teal-400 hover:text-teal-300">登录</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const phone = ref('')
const nickname = ref('')
const password = ref('')
const submitting = ref(false)

async function onSubmit() {
  if (!phone.value.trim() || !nickname.value.trim() || password.value.length < 6) {
    ElMessage.warning('请填写完整信息，密码至少 6 位')
    return
  }
  submitting.value = true
  try {
    await userStore.register({
      phone: phone.value.trim(),
      nickname: nickname.value.trim(),
      password: password.value,
    })
    await router.replace('/')
  } catch {
    ElMessage.error('注册失败，手机号可能已被使用')
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
