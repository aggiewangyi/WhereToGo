<template>
  <div
    class="agent-console relative mx-auto flex h-[calc(100vh-3.25rem)] max-w-6xl flex-col gap-0 px-2 pb-3 pt-3 sm:px-3 lg:flex-row lg:gap-4 lg:px-4"
  >
    <!-- 移动端：历史抽屉开关 -->
    <button
      type="button"
      class="mb-2 flex items-center gap-2 rounded-xl border border-white/[0.08] bg-slate-900/70 px-3 py-2 font-mono text-[11px] text-teal-200/90 backdrop-blur-sm lg:hidden"
      @click="drawerOpen = true"
    >
      <span class="h-1.5 w-1.5 rounded-full bg-teal-400 shadow-glow-sm" />
      历史对话
    </button>

    <!-- 侧边栏：桌面 -->
    <aside
      class="hidden w-[260px] shrink-0 flex-col rounded-2xl border border-white/[0.08] bg-slate-950/60 shadow-panel backdrop-blur-sm lg:flex"
    >
      <div class="border-b border-white/[0.06] p-3">
        <el-button class="w-full new-chat-btn" size="small" @click="newConversation">新对话</el-button>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto p-2">
        <div v-if="sessionsLoading" class="space-y-2 px-1 py-2">
          <div v-for="n in 5" :key="n" class="h-11 animate-pulse rounded-xl bg-slate-800/80" />
        </div>
        <button
          v-for="s in sessions"
          v-else
          :key="s.id"
          type="button"
          class="session-row mb-1 w-full rounded-xl px-3 py-2.5 text-left transition-colors"
          :class="{ 'session-row--active': s.id === sessionId }"
          @click="openSessionById(s.id)"
        >
          <p class="truncate text-xs font-medium text-slate-200">{{ sessionTitle(s) }}</p>
          <p class="mt-0.5 font-mono text-[10px] text-slate-500">{{ formatTime(s.updated_at) }}</p>
        </button>
        <p v-if="!sessionsLoading && sessions.length === 0" class="px-2 py-6 text-center text-xs text-slate-500">
          暂无历史，开始一段新规划吧
        </p>
      </div>
    </aside>

    <!-- 移动端抽屉 -->
    <Teleport to="body">
      <div
        v-if="drawerOpen"
        class="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm lg:hidden"
        @click.self="drawerOpen = false"
      />
      <aside
        v-if="drawerOpen"
        class="fixed inset-y-0 left-0 z-[70] flex w-[min(88vw,300px)] flex-col border-r border-white/[0.08] bg-slate-950/95 shadow-2xl backdrop-blur-md lg:hidden"
      >
        <div class="flex items-center justify-between border-b border-white/[0.06] p-3">
          <span class="text-xs font-medium text-slate-300">历史对话</span>
          <el-button text size="small" class="!text-slate-400" @click="drawerOpen = false">关闭</el-button>
        </div>
        <div class="border-b border-white/[0.06] p-3">
          <el-button class="w-full new-chat-btn" size="small" @click="newConversation">新对话</el-button>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto p-2">
          <button
            v-for="s in sessions"
            :key="s.id"
            type="button"
            class="session-row mb-1 w-full rounded-xl px-3 py-2.5 text-left"
            :class="{ 'session-row--active': s.id === sessionId }"
            @click="openSessionById(s.id)"
          >
            <p class="truncate text-xs font-medium text-slate-200">{{ sessionTitle(s) }}</p>
            <p class="mt-0.5 font-mono text-[10px] text-slate-500">{{ formatTime(s.updated_at) }}</p>
          </button>
        </div>
      </aside>
    </Teleport>

    <!-- 主列 -->
    <div class="flex min-h-0 min-w-0 flex-1 flex-col">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-wrap items-center gap-3">
          <div
            class="inline-flex rounded-lg border border-teal-500/20 bg-slate-900/80 p-0.5 shadow-panel backdrop-blur-sm"
          >
            <el-radio-group v-model="interactionMode" size="small" class="agent-mode-toggle">
              <el-radio-button value="verbose">详细 · 我要深度参与你规划</el-radio-button>
              <el-radio-button value="quiet">简洁 · 我要你帮我搞定一切</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <el-button class="agent-btn-ghost" size="small" :disabled="loading" @click="onClear">清空当前对话</el-button>
      </div>

      <Transition name="mission-fade">
        <div
          v-if="loading && (liveMissionTitle || signalFeed.length)"
          class="mission-panel relative mb-3 overflow-hidden rounded-2xl border border-teal-500/25 bg-gradient-to-r from-slate-950/95 via-slate-900/90 to-slate-950/95 px-4 py-3 shadow-glow-sm backdrop-blur-md"
        >
          <div class="mission-grid-bg pointer-events-none absolute inset-0 opacity-30" aria-hidden="true" />
          <div class="relative flex flex-wrap items-start gap-4">
            <div class="mission-bars flex shrink-0 gap-0.5 pt-1" aria-hidden="true">
              <span v-for="b in 5" :key="b" class="mission-bar" :style="{ animationDelay: `${b * 0.12}s` }" />
            </div>
            <div class="min-w-0 flex-1">
              <p class="font-display text-[15px] font-semibold tracking-tight text-white">
                {{ liveMissionTitle || '正在 · 推理编排中' }}
              </p>
              <p
                v-if="lastAssistantForStatus"
                class="mt-1 font-mono text-[11px] leading-relaxed text-teal-100/85"
              >
                {{ assistantStatusLine(lastAssistantForStatus) }}
              </p>
            </div>
          </div>
          <div
            v-if="signalFeed.length"
            class="relative mt-3 flex max-h-16 flex-wrap gap-1.5 overflow-y-auto pr-1 font-mono text-[10px] leading-snug"
          >
            <span
              v-for="s in signalFeed"
              :key="s.id"
              class="signal-chip rounded-md border border-white/[0.06] bg-black/25 px-2 py-1 text-slate-400"
            >
              {{ s.text }}
            </span>
          </div>
        </div>
      </Transition>

      <div
        ref="scrollRef"
        class="agent-scroll relative min-h-0 flex-1 overflow-y-auto rounded-2xl border border-white/[0.08] bg-slate-950/50 p-4 shadow-panel backdrop-blur-sm sm:p-5"
      >
        <div
          v-if="messages.length === 0"
          class="flex flex-col items-center justify-center px-4 py-24 text-center"
        >
          <div class="agent-orbit mb-6 h-14 w-14 rounded-full border border-teal-500/30 shadow-glow-sm" />
          <p class="font-display text-base font-semibold text-white">从这里开始</p>
          <p class="mt-2 max-w-sm text-sm leading-relaxed text-slate-500">
            说说目的地、天数和预算；也可以从左侧选择<strong class="text-slate-400">历史对话</strong>继续上次未完的规划。
          </p>
        </div>

        <div v-else class="space-y-6">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'"
          >
            <div
              v-if="msg.role === 'user'"
              class="max-w-[min(100%,40rem)] rounded-2xl border border-teal-500/25 bg-gradient-to-br from-teal-950/80 to-slate-900/90 px-4 py-3 text-sm text-slate-100 shadow-glow-sm"
            >
              {{ msg.content }}
            </div>

            <div
              v-else
              class="agent-assistant-bubble w-full max-w-[min(100%,48rem)] overflow-hidden rounded-2xl border border-white/[0.07] bg-slate-900/70 shadow-panel"
              :class="{ 'agent-assistant-bubble--live': msg.loading }"
            >
              <div
                v-if="msg.loading && assistantStatusLine(msg)"
                class="relative border-b border-white/[0.06] bg-slate-950/80 px-4 py-3"
              >
                <div class="agent-scanline pointer-events-none absolute inset-0 opacity-40" aria-hidden="true" />
                <div class="neural-line pointer-events-none absolute bottom-0 left-0 h-0.5 w-full opacity-80" />
                <div class="relative flex items-center gap-3">
                  <div class="agent-pulse-ring shrink-0" />
                  <Transition name="status-line" mode="out-in">
                    <p
                      :key="assistantStatusLine(msg)"
                      class="min-w-0 flex-1 font-mono text-[12px] leading-snug tracking-wide text-teal-100/95"
                    >
                      {{ assistantStatusLine(msg) }}
                    </p>
                  </Transition>
                </div>
              </div>

              <div
                v-if="msg.content.trim().length > 0 || !msg.loading"
                class="agent-answer px-4 py-4 sm:px-5 sm:py-5"
                :class="{ 'agent-answer--streaming': msg.loading && msg.content.trim().length > 0 }"
              >
                <div
                  class="prose prose-invert prose-sm max-w-none prose-headings:font-display prose-p:text-slate-300 prose-a:text-teal-400 prose-strong:text-white"
                  v-html="assistantBubbleHtml(msg, idx)"
                />
                <span
                  v-if="msg.loading && msg.content.trim().length > 0"
                  class="agent-caret ml-0.5 inline-block h-3.5 w-0.5 translate-y-0.5 bg-teal-400 shadow-glow-sm"
                  aria-hidden="true"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="composer-dock mt-4 shrink-0">
        <div
          class="composer-inner flex gap-2 rounded-2xl border border-white/[0.08] bg-slate-950/85 p-2 shadow-panel backdrop-blur-md"
        >
          <el-input
            v-model="input"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 6 }"
            placeholder="描述你的旅行想法 — Enter 发送 · Shift+Enter 换行"
            class="agent-input flex-1"
            @keydown.enter.exact.prevent="onSend"
          />
          <el-button class="agent-send shrink-0 self-end" :loading="loading" @click="onSend">发送</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import { marked } from 'marked'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  agentChatStream,
  listAgentSessions,
  getAgentSessionMessages,
  type AgentSessionRow,
} from '@/services/agent'

const SESSION_STORAGE_KEY = 'wheretogo_chat_session_id'

type ToolStep = { name: string; status: 'running' | 'done' | 'error' }

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
  loading?: boolean
  tool_steps?: ToolStep[]
  planningPhase?: string | null
}

const TOOL_WORKING: Record<string, string> = {
  web_search_tool: '正在联网查询相关信息…',
  news_search_tool: '正在检索新闻与动态…',
  search_travel_notes: '正在查阅社区笔记与攻略…',
  check_weather: '正在获取天气预报…',
  check_current_weather: '正在获取实时天气…',
  translate: '正在执行翻译…',
  get_location: '正在解析地理位置…',
  plan_route: '正在规划路线…',
  search_nearby: '正在检索周边地点…',
  search_flight_tickets: '正在查询航班信息…',
  search_train_tickets: '正在查询铁路票务…',
  search_hotel_options: '正在检索酒店选项…',
  search_destinations_catalog: '正在查询目的地库…',
}

const MAX_HISTORY_TURNS = 24

const messages = ref<ChatMessage[]>([])
const sessionId = ref<string | null>(null)
const loading = ref(false)
const input = ref('')
const scrollRef = ref<HTMLElement | null>(null)
const interactionMode = ref<'verbose' | 'quiet'>('verbose')
const sessions = ref<AgentSessionRow[]>([])
const sessionsLoading = ref(false)
const drawerOpen = ref(false)

/** 顶部任务条：阶段移交 + 信号流 */
const liveMissionTitle = ref('')
const signalFeed = ref<{ id: number; text: string }[]>([])
let signalSeq = 0
const streamingHtmlCache = ref('')

const lastAssistantForStatus = computed(() => {
  const m = messages.value
  if (m.length === 0) return null
  const last = m[m.length - 1]
  return last.role === 'assistant' ? last : null
})

watch(sessionId, (v) => {
  if (v) localStorage.setItem(SESSION_STORAGE_KEY, v)
  else localStorage.removeItem(SESSION_STORAGE_KEY)
})

marked.setOptions({ breaks: true, gfm: true })

function toolLabel(name: string) {
  return (
    {
      web_search_tool: '联网搜索',
      news_search_tool: '新闻检索',
      search_travel_notes: '笔记攻略',
      check_weather: '天气预报',
      check_current_weather: '实时天气',
      translate: '翻译',
      get_location: '地理编码',
      plan_route: '路线规划',
      search_nearby: '周边搜索',
      search_flight_tickets: '机票',
      search_train_tickets: '火车票',
      search_hotel_options: '酒店',
      search_destinations_catalog: '目的地库',
    }[name] || name.replace(/_/g, ' ')
  )
}

function toolWorkingLine(name: string) {
  return TOOL_WORKING[name] || `正在调用「${toolLabel(name)}」…`
}

/** 脱敏：移除疑似内部 TravelProfile JSON 块（用户画像不向用户展示） */
function skipJsonObject(s: string, start: number): number {
  let depth = 0
  let inStr = false
  let esc = false
  for (let i = start; i < s.length; i++) {
    const c = s[i]
    if (inStr) {
      if (esc) {
        esc = false
        continue
      }
      if (c === '\\') {
        esc = true
        continue
      }
      if (c === '"') inStr = false
      continue
    }
    if (c === '"') {
      inStr = true
      continue
    }
    if (c === '{') depth++
    else if (c === '}') {
      depth--
      if (depth === 0) return i + 1
    }
  }
  return start
}

function sanitizeReplyText(s: string): string {
  if (!s || !s.includes('traveler_type')) return s
  let i = 0
  let out = ''
  while (i < s.length) {
    const j = s.indexOf('{', i)
    if (j === -1) return out + s.slice(i)
    const probe = s.slice(j, Math.min(j + 6000, s.length))
    const fp =
      probe.includes('"traveler_type"') &&
      probe.includes('"destination"') &&
      (probe.includes('"preferences"') || probe.includes('"budget_level"') || probe.includes('"notes"'))
    if (!fp) {
      out += s.slice(i, j + 1)
      i = j + 1
      continue
    }
    out += s.slice(i, j)
    const end = skipJsonObject(s, j)
    i = end > j ? end : j + 1
  }
  return out
}

function pushSignal(text: string) {
  const t = text.trim()
  if (!t) return
  signalSeq += 1
  signalFeed.value = [...signalFeed.value.slice(-20), { id: signalSeq, text: t }]
}

function renderMarkdown(text: string) {
  return marked.parse(sanitizeReplyText(text || '')) as string
}

function assistantBubbleHtml(msg: ChatMessage, idx: number): string {
  if (msg.role !== 'assistant') return ''
  const isLast = idx === messages.value.length - 1
  const raw = sanitizeReplyText(msg.content)
  if (isLast && msg.loading) {
    return streamingHtmlCache.value || (marked.parse(raw || ' ') as string)
  }
  return marked.parse(raw || '') as string
}

function assistantStatusLine(msg: ChatMessage): string {
  const running = msg.tool_steps?.filter((s) => s.status === 'running') || []
  if (running.length) {
    return toolWorkingLine(running[running.length - 1].name)
  }
  if (msg.planningPhase?.trim()) {
    const p = msg.planningPhase.trim()
    if (p.startsWith('正在')) return `${p}…`
    return `子任务：${p}…`
  }
  const hasText = msg.content.trim().length > 0
  if (hasText) return '流式输出模型回复中…'
  return '语义解析与上下文对齐中…'
}

function sessionTitle(s: AgentSessionRow) {
  if (s.title?.trim()) return s.title.trim()
  return `对话 · ${formatTime(s.updated_at)}`
}

function formatTime(iso: string) {
  try {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

async function loadSessions() {
  sessionsLoading.value = true
  try {
    sessions.value = await listAgentSessions()
  } catch {
    sessions.value = []
  } finally {
    sessionsLoading.value = false
  }
}

async function openSessionById(id: string) {
  if (loading.value) return
  try {
    const data = await getAgentSessionMessages(id)
    sessionId.value = data.session_id
    messages.value = data.messages.map((m) => ({
      role: (m.role === 'user' ? 'user' : 'assistant') as 'user' | 'assistant',
      content: sanitizeReplyText(m.content),
    }))
    drawerOpen.value = false
  } catch {
    ElMessage.error('无法加载该对话')
    sessionId.value = null
    messages.value = []
    localStorage.removeItem(SESSION_STORAGE_KEY)
  }
}

function newConversation() {
  messages.value = []
  sessionId.value = null
  drawerOpen.value = false
}

async function scrollToBottom() {
  await nextTick()
  const el = scrollRef.value
  if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
}

watch(
  () => [
    messages.value.length,
    messages.value[messages.value.length - 1]?.role,
    messages.value[messages.value.length - 1]?.content?.length ?? 0,
    loading.value,
  ],
  () => scrollToBottom()
)

watch(loading, () => scrollToBottom())

async function onSend() {
  const text = input.value.trim()
  if (!text || loading.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  messages.value.push({
    role: 'assistant',
    content: '',
    loading: true,
    tool_steps: [],
    planningPhase: null,
  })
  loading.value = true

  liveMissionTitle.value = '正在 · 连接推理引擎…'
  signalFeed.value = []
  streamingHtmlCache.value = ''
  pushSignal(liveMissionTitle.value)

  const prior = messages.value
    .slice(0, -2)
    .slice(-MAX_HISTORY_TURNS)
    .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))

  const assistantMsg = messages.value[messages.value.length - 1]

  let pendingText = ''
  let streamRaf = 0
  let scrollRaf = 0
  let lastMdAt = 0
  let lastMdLen = 0

  function bumpMarkdown(force: boolean) {
    const raw = assistantMsg.content
    const now = Date.now()
    if (!force && now - lastMdAt < 80 && raw.length - lastMdLen < 80) return
    lastMdAt = now
    lastMdLen = raw.length
    streamingHtmlCache.value = marked.parse(sanitizeReplyText(raw)) as string
  }

  function flushStream() {
    streamRaf = 0
    if (!pendingText) return
    assistantMsg.content += pendingText
    pendingText = ''
    bumpMarkdown(false)
    if (!scrollRaf) {
      scrollRaf = requestAnimationFrame(() => {
        scrollRaf = 0
        void scrollToBottom()
      })
    }
  }

  function scheduleStreamChunk(chunk: string) {
    pendingText += chunk
    if (streamRaf) return
    streamRaf = requestAnimationFrame(flushStream)
  }

  try {
    const res = await agentChatStream(text, {
      session_id: sessionId.value,
      history: sessionId.value ? undefined : prior.length ? prior : undefined,
      interaction_mode: interactionMode.value,
    })
    const reader = res.body?.getReader()
    const decoder = new TextDecoder()

    if (reader) {
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          try {
            const json = JSON.parse(line.slice(5).trim()) as {
              type: string
              data?: Record<string, unknown>
            }
            if (json.type === 'session' && json.data?.session_id) {
              sessionId.value = String(json.data.session_id)
            } else if (json.type === 'text' && json.data) {
              scheduleStreamChunk(String(json.data))
            } else if (json.type === 'phase' && json.data) {
              const label = typeof json.data.label === 'string' ? json.data.label : ''
              const name = typeof json.data.name === 'string' ? json.data.name : ''
              assistantMsg.planningPhase = label || name
              const fallback: Record<string, string> = {
                intent: '正在 · 意图识别与推荐',
                planner: '正在 · 行程规划编排',
                prep: '正在 · 行前建议与打包清单',
                handoff_profile: '正在 · 整合需求并移交行程专家',
                handoff_prep: '正在 · 汇总行程并移交行前顾问',
              }
              const lineTitle = label || fallback[name] || '正在 · 多智能体编排中'
              liveMissionTitle.value = lineTitle.startsWith('正在') ? lineTitle : `正在 · ${lineTitle}`
              pushSignal(liveMissionTitle.value)
            } else if (json.type === 'tool_start' && json.data?.name) {
              const nm = String(json.data.name)
              assistantMsg.tool_steps = [
                ...(assistantMsg.tool_steps || []),
                { name: nm, status: 'running' },
              ]
              pushSignal(toolWorkingLine(nm))
            } else if (json.type === 'tool_end' && json.data?.name) {
              const name = String(json.data.name)
              const output = String(json.data.output ?? '')
              const failed =
                /已跳过|无工具返回|本次超时（|工具输出无法预览/.test(output) ||
                /\bTimeout\b/i.test(output)
              const steps = [...(assistantMsg.tool_steps || [])]
              let idx = -1
              for (let i = steps.length - 1; i >= 0; i--) {
                if (steps[i].name === name && steps[i].status === 'running') {
                  idx = i
                  break
                }
              }
              if (idx >= 0) {
                steps[idx] = {
                  ...steps[idx],
                  status: failed ? 'error' : 'done',
                }
                assistantMsg.tool_steps = steps
              }
            } else if (json.type === 'error' && json.data?.message) {
              assistantMsg.content = String(json.data.message)
              bumpMarkdown(true)
            }
          } catch {
            /* ignore malformed sse */
          }
        }
      }
      if (streamRaf) {
        cancelAnimationFrame(streamRaf)
        streamRaf = 0
      }
      flushStream()
      const orphan = assistantMsg.tool_steps?.filter((s) => s.status === 'running')
      if (orphan?.length) {
        assistantMsg.tool_steps = (assistantMsg.tool_steps || []).map((s) =>
          s.status === 'running' ? { ...s, status: 'error' as const } : s
        )
      }
    } else {
      const data = (await res.json()) as { content?: string; session_id?: string }
      assistantMsg.content = sanitizeReplyText(data.content || '')
      if (data.session_id) sessionId.value = data.session_id
      bumpMarkdown(true)
    }
    assistantMsg.loading = false
    bumpMarkdown(true)
    window.setTimeout(() => {
      liveMissionTitle.value = ''
      signalFeed.value = []
    }, 700)
  } catch {
    assistantMsg.content = '发送失败，请检查网络或重新登录后再试。'
    assistantMsg.loading = false
    bumpMarkdown(true)
    liveMissionTitle.value = ''
    signalFeed.value = []
    ElMessage.error('发送失败')
  } finally {
    loading.value = false
    void loadSessions()
  }
}

async function onClear() {
  try {
    await ElMessageBox.confirm('清空当前界面上的对话？（服务器上的历史仍可在左侧找回）', '提示', {
      confirmButtonText: '清空',
      cancelButtonText: '取消',
      type: 'warning',
    })
    messages.value = []
    sessionId.value = null
    ElMessage.success('已清空当前对话')
  } catch {
    /* cancelled */
  }
}

onMounted(async () => {
  await loadSessions()
  const saved = localStorage.getItem(SESSION_STORAGE_KEY)
  if (saved) {
    await openSessionById(saved)
  }
})
</script>

<style scoped>
.agent-scroll {
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: rgba(45, 212, 191, 0.35) transparent;
}

.session-row {
  color: inherit;
  background: transparent;
  border: 1px solid transparent;
}
.session-row:hover {
  background: rgba(15, 23, 42, 0.75);
  border-color: rgba(45, 212, 191, 0.12);
}
.session-row--active {
  background: rgba(45, 212, 191, 0.08) !important;
  border-color: rgba(45, 212, 191, 0.35) !important;
}

.new-chat-btn {
  border-radius: 10px !important;
  border: 1px solid rgba(45, 212, 191, 0.35) !important;
  background: rgba(45, 212, 191, 0.1) !important;
  color: rgb(204, 251, 241) !important;
  font-weight: 600;
}

.agent-orbit {
  animation: orbit-spin 12s linear infinite;
  box-shadow:
    inset 0 0 20px rgba(45, 212, 191, 0.15),
    0 0 24px -8px rgba(45, 212, 191, 0.35);
}

@keyframes orbit-spin {
  to {
    transform: rotate(360deg);
  }
}

.agent-scanline {
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(45, 212, 191, 0.03) 2px,
    rgba(45, 212, 191, 0.03) 4px
  );
  mask-image: linear-gradient(90deg, transparent, black 18%, black 82%, transparent);
}

.agent-pulse-ring {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: rgba(45, 212, 191, 0.95);
  box-shadow:
    0 0 0 0 rgba(45, 212, 191, 0.45),
    0 0 12px rgba(45, 212, 191, 0.55);
  animation: pulse-ring 1.6s ease-out infinite;
}

@keyframes pulse-ring {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  70% {
    transform: scale(1.35);
    opacity: 0.35;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.agent-answer--streaming :deep(.prose) {
  animation: answer-in 0.45s ease-out both;
}

@keyframes answer-in {
  from {
    opacity: 0.65;
    filter: blur(2px);
  }
  to {
    opacity: 1;
    filter: blur(0);
  }
}

.agent-caret {
  animation: caret-blink 1s step-end infinite;
}

@keyframes caret-blink {
  50% {
    opacity: 0;
  }
}

.status-line-enter-active,
.status-line-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
}
.status-line-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.status-line-leave-to {
  opacity: 0;
  transform: translateY(-3px);
}

.composer-dock {
  position: relative;
}
.composer-dock::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 1rem;
  padding: 1px;
  background: linear-gradient(
    120deg,
    rgba(45, 212, 191, 0.25),
    rgba(45, 212, 191, 0.05) 40%,
    rgba(148, 163, 184, 0.08) 70%,
    rgba(45, 212, 191, 0.2)
  );
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0.65;
}

:deep(.agent-mode-toggle .el-radio-button__inner) {
  background: transparent !important;
  border: none !important;
  color: rgba(148, 163, 184, 0.95) !important;
  font-family: Outfit, PingFang SC, sans-serif;
  font-size: 12px;
  font-weight: 500;
  box-shadow: none !important;
}
:deep(.agent-mode-toggle .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: rgba(45, 212, 191, 0.12) !important;
  color: rgb(153, 246, 228) !important;
  box-shadow: inset 0 0 0 1px rgba(45, 212, 191, 0.35) !important;
}

:deep(.agent-input .el-textarea__inner) {
  background: rgba(15, 23, 42, 0.55) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  border-radius: 12px !important;
  color: #e2e8f0 !important;
  font-family: Outfit, PingFang SC, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  box-shadow: none !important;
  resize: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}
:deep(.agent-input .el-textarea__inner:focus) {
  border-color: rgba(45, 212, 191, 0.45) !important;
  box-shadow: 0 0 0 1px rgba(45, 212, 191, 0.2), 0 0 28px -8px rgba(45, 212, 191, 0.25) !important;
}
:deep(.agent-input .el-textarea__inner::placeholder) {
  color: rgba(100, 116, 139, 0.9);
}

:deep(.agent-send.el-button) {
  border-radius: 12px !important;
  border: 1px solid rgba(45, 212, 191, 0.45) !important;
  background: linear-gradient(165deg, rgba(45, 212, 191, 0.22), rgba(15, 118, 110, 0.35)) !important;
  color: rgb(204, 251, 241) !important;
  font-family: Outfit, PingFang SC, sans-serif;
  font-weight: 600;
  padding: 10px 18px !important;
  box-shadow: 0 0 24px -10px rgba(45, 212, 191, 0.5);
  transition:
    transform 0.15s ease,
    box-shadow 0.2s ease;
}
:deep(.agent-send.el-button:hover:not(.is-loading)) {
  transform: translateY(-1px);
  box-shadow: 0 0 32px -8px rgba(45, 212, 191, 0.55);
}

:deep(.agent-btn-ghost.el-button) {
  background: rgba(15, 23, 42, 0.6) !important;
  border: 1px solid rgba(248, 113, 113, 0.25) !important;
  color: rgba(252, 165, 165, 0.95) !important;
  border-radius: 10px !important;
  font-size: 12px;
}

.mission-fade-enter-active,
.mission-fade-leave-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s ease;
}
.mission-fade-enter-from,
.mission-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.mission-grid-bg {
  background-image:
    linear-gradient(105deg, rgba(45, 212, 191, 0.07) 0%, transparent 45%),
    radial-gradient(circle at 80% 20%, rgba(56, 189, 248, 0.08), transparent 55%);
}

.mission-bars .mission-bar {
  display: block;
  width: 3px;
  height: 18px;
  border-radius: 9999px;
  background: linear-gradient(180deg, rgba(45, 212, 191, 0.15), rgba(45, 212, 191, 0.95));
  animation: bar-pulse 1.1s ease-in-out infinite alternate;
}
@keyframes bar-pulse {
  from {
    transform: scaleY(0.35);
    opacity: 0.45;
    filter: drop-shadow(0 0 4px rgba(45, 212, 191, 0.35));
  }
  to {
    transform: scaleY(1);
    opacity: 1;
    filter: drop-shadow(0 0 8px rgba(45, 212, 191, 0.55));
  }
}

.neural-line {
  background: linear-gradient(90deg, transparent, rgba(45, 212, 191, 0.85), transparent);
  animation: neural-sweep 2.2s linear infinite;
}
@keyframes neural-sweep {
  0% {
    transform: translateX(-40%);
    opacity: 0.2;
  }
  40% {
    opacity: 1;
  }
  100% {
    transform: translateX(140%);
    opacity: 0.2;
  }
}

.agent-assistant-bubble--live {
  box-shadow:
    0 0 0 1px rgba(45, 212, 191, 0.12),
    0 0 48px -20px rgba(45, 212, 191, 0.25);
}
</style>
