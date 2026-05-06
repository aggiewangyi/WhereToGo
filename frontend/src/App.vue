<template>
  <div class="app-root relative min-h-screen flex flex-col text-slate-100 antialiased">
    <div class="pointer-events-none fixed inset-0 bg-grid-tech bg-[length:48px_48px] opacity-[0.65]" aria-hidden="true" />
    <div
      class="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(45,212,191,0.12),transparent_55%)]"
      aria-hidden="true"
    />

    <header
      class="relative z-10 shrink-0 border-b border-teal-950/80 bg-slate-950/75 px-4 py-3 backdrop-blur-md"
    >
      <div class="mx-auto flex max-w-6xl items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="font-display truncate text-sm font-semibold tracking-tight text-white">
            去哪玩
            <span class="ml-1.5 font-normal text-teal-400/90">旅行助手</span>
          </h1>
          <p class="truncate text-xs text-slate-500">懂你的行程、攻略与灵感</p>
        </div>
        <div v-if="user" class="flex shrink-0 items-center gap-2">
          <span class="hidden max-w-[10rem] truncate text-xs text-slate-400 sm:inline">{{ user.nickname }}</span>
          <el-button class="header-logout" size="small" @click="onLogout">退出</el-button>
        </div>
      </div>
    </header>
    <main class="relative z-10 min-h-0 flex-1">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { RouterView, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const { user } = storeToRefs(userStore)
const router = useRouter()

function onLogout() {
  userStore.logout()
  void router.push('/login')
}
</script>

<style scoped>
.app-root {
  background-color: #030712;
}
.header-logout {
  background: rgba(15, 23, 42, 0.7) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  color: rgba(226, 232, 240, 0.95) !important;
  border-radius: 10px !important;
}
</style>
