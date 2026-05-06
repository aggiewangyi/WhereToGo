import { ref, watch, nextTick, onMounted, computed } from 'vue';
import { marked } from 'marked';
import { ElMessage, ElMessageBox } from 'element-plus';
import { agentChatStream, listAgentSessions, getAgentSessionMessages, } from '@/services/agent';
const SESSION_STORAGE_KEY = 'wheretogo_chat_session_id';
const TOOL_WORKING = {
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
};
const MAX_HISTORY_TURNS = 24;
const messages = ref([]);
const sessionId = ref(null);
const loading = ref(false);
const input = ref('');
const scrollRef = ref(null);
const interactionMode = ref('verbose');
const sessions = ref([]);
const sessionsLoading = ref(false);
const drawerOpen = ref(false);
/** 顶部任务条：阶段移交 + 信号流 */
const liveMissionTitle = ref('');
const signalFeed = ref([]);
let signalSeq = 0;
const streamingHtmlCache = ref('');
const lastAssistantForStatus = computed(() => {
    const m = messages.value;
    if (m.length === 0)
        return null;
    const last = m[m.length - 1];
    return last.role === 'assistant' ? last : null;
});
watch(sessionId, (v) => {
    if (v)
        localStorage.setItem(SESSION_STORAGE_KEY, v);
    else
        localStorage.removeItem(SESSION_STORAGE_KEY);
});
marked.setOptions({ breaks: true, gfm: true });
function toolLabel(name) {
    return ({
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
    }[name] || name.replace(/_/g, ' '));
}
function toolWorkingLine(name) {
    return TOOL_WORKING[name] || `正在调用「${toolLabel(name)}」…`;
}
/** 脱敏：移除疑似内部 TravelProfile JSON 块（用户画像不向用户展示） */
function skipJsonObject(s, start) {
    let depth = 0;
    let inStr = false;
    let esc = false;
    for (let i = start; i < s.length; i++) {
        const c = s[i];
        if (inStr) {
            if (esc) {
                esc = false;
                continue;
            }
            if (c === '\\') {
                esc = true;
                continue;
            }
            if (c === '"')
                inStr = false;
            continue;
        }
        if (c === '"') {
            inStr = true;
            continue;
        }
        if (c === '{')
            depth++;
        else if (c === '}') {
            depth--;
            if (depth === 0)
                return i + 1;
        }
    }
    return start;
}
function sanitizeReplyText(s) {
    if (!s || !s.includes('traveler_type'))
        return s;
    let i = 0;
    let out = '';
    while (i < s.length) {
        const j = s.indexOf('{', i);
        if (j === -1)
            return out + s.slice(i);
        const probe = s.slice(j, Math.min(j + 6000, s.length));
        const fp = probe.includes('"traveler_type"') &&
            probe.includes('"destination"') &&
            (probe.includes('"preferences"') || probe.includes('"budget_level"') || probe.includes('"notes"'));
        if (!fp) {
            out += s.slice(i, j + 1);
            i = j + 1;
            continue;
        }
        out += s.slice(i, j);
        const end = skipJsonObject(s, j);
        i = end > j ? end : j + 1;
    }
    return out;
}
function pushSignal(text) {
    const t = text.trim();
    if (!t)
        return;
    signalSeq += 1;
    signalFeed.value = [...signalFeed.value.slice(-20), { id: signalSeq, text: t }];
}
function renderMarkdown(text) {
    return marked.parse(sanitizeReplyText(text || ''));
}
function assistantBubbleHtml(msg, idx) {
    if (msg.role !== 'assistant')
        return '';
    const isLast = idx === messages.value.length - 1;
    const raw = sanitizeReplyText(msg.content);
    if (isLast && msg.loading) {
        return streamingHtmlCache.value || marked.parse(raw || ' ');
    }
    return marked.parse(raw || '');
}
function assistantStatusLine(msg) {
    const running = msg.tool_steps?.filter((s) => s.status === 'running') || [];
    if (running.length) {
        return toolWorkingLine(running[running.length - 1].name);
    }
    if (msg.planningPhase?.trim()) {
        const p = msg.planningPhase.trim();
        if (p.startsWith('正在'))
            return `${p}…`;
        return `子任务：${p}…`;
    }
    const hasText = msg.content.trim().length > 0;
    if (hasText)
        return '流式输出模型回复中…';
    return '语义解析与上下文对齐中…';
}
function sessionTitle(s) {
    if (s.title?.trim())
        return s.title.trim();
    return `对话 · ${formatTime(s.updated_at)}`;
}
function formatTime(iso) {
    try {
        const d = new Date(iso);
        return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
    catch {
        return '';
    }
}
async function loadSessions() {
    sessionsLoading.value = true;
    try {
        sessions.value = await listAgentSessions();
    }
    catch {
        sessions.value = [];
    }
    finally {
        sessionsLoading.value = false;
    }
}
async function openSessionById(id) {
    if (loading.value)
        return;
    try {
        const data = await getAgentSessionMessages(id);
        sessionId.value = data.session_id;
        messages.value = data.messages.map((m) => ({
            role: (m.role === 'user' ? 'user' : 'assistant'),
            content: sanitizeReplyText(m.content),
        }));
        drawerOpen.value = false;
    }
    catch {
        ElMessage.error('无法加载该对话');
        sessionId.value = null;
        messages.value = [];
        localStorage.removeItem(SESSION_STORAGE_KEY);
    }
}
function newConversation() {
    messages.value = [];
    sessionId.value = null;
    drawerOpen.value = false;
}
async function scrollToBottom() {
    await nextTick();
    const el = scrollRef.value;
    if (el)
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
}
watch(() => [
    messages.value.length,
    messages.value[messages.value.length - 1]?.role,
    messages.value[messages.value.length - 1]?.content?.length ?? 0,
    loading.value,
], () => scrollToBottom());
watch(loading, () => scrollToBottom());
async function onSend() {
    const text = input.value.trim();
    if (!text || loading.value)
        return;
    input.value = '';
    messages.value.push({ role: 'user', content: text });
    messages.value.push({
        role: 'assistant',
        content: '',
        loading: true,
        tool_steps: [],
        planningPhase: null,
    });
    loading.value = true;
    liveMissionTitle.value = '正在 · 连接推理引擎…';
    signalFeed.value = [];
    streamingHtmlCache.value = '';
    pushSignal(liveMissionTitle.value);
    const prior = messages.value
        .slice(0, -2)
        .slice(-MAX_HISTORY_TURNS)
        .map((m) => ({ role: m.role, content: m.content }));
    const assistantMsg = messages.value[messages.value.length - 1];
    let pendingText = '';
    let streamRaf = 0;
    let scrollRaf = 0;
    let lastMdAt = 0;
    let lastMdLen = 0;
    function bumpMarkdown(force) {
        const raw = assistantMsg.content;
        const now = Date.now();
        if (!force && now - lastMdAt < 80 && raw.length - lastMdLen < 80)
            return;
        lastMdAt = now;
        lastMdLen = raw.length;
        streamingHtmlCache.value = marked.parse(sanitizeReplyText(raw));
    }
    function flushStream() {
        streamRaf = 0;
        if (!pendingText)
            return;
        assistantMsg.content += pendingText;
        pendingText = '';
        bumpMarkdown(false);
        if (!scrollRaf) {
            scrollRaf = requestAnimationFrame(() => {
                scrollRaf = 0;
                void scrollToBottom();
            });
        }
    }
    function scheduleStreamChunk(chunk) {
        pendingText += chunk;
        if (streamRaf)
            return;
        streamRaf = requestAnimationFrame(flushStream);
    }
    try {
        const res = await agentChatStream(text, {
            session_id: sessionId.value,
            history: sessionId.value ? undefined : prior.length ? prior : undefined,
            interaction_mode: interactionMode.value,
        });
        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        if (reader) {
            let buffer = '';
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                for (const line of lines) {
                    if (!line.startsWith('data:'))
                        continue;
                    try {
                        const json = JSON.parse(line.slice(5).trim());
                        if (json.type === 'session' && json.data?.session_id) {
                            sessionId.value = String(json.data.session_id);
                        }
                        else if (json.type === 'text' && json.data) {
                            scheduleStreamChunk(String(json.data));
                        }
                        else if (json.type === 'phase' && json.data) {
                            const label = typeof json.data.label === 'string' ? json.data.label : '';
                            const name = typeof json.data.name === 'string' ? json.data.name : '';
                            assistantMsg.planningPhase = label || name;
                            const fallback = {
                                intent: '正在 · 意图识别与推荐',
                                planner: '正在 · 行程规划编排',
                                prep: '正在 · 行前建议与打包清单',
                                handoff_profile: '正在 · 整合需求并移交行程专家',
                                handoff_prep: '正在 · 汇总行程并移交行前顾问',
                            };
                            const lineTitle = label || fallback[name] || '正在 · 多智能体编排中';
                            liveMissionTitle.value = lineTitle.startsWith('正在') ? lineTitle : `正在 · ${lineTitle}`;
                            pushSignal(liveMissionTitle.value);
                        }
                        else if (json.type === 'tool_start' && json.data?.name) {
                            const nm = String(json.data.name);
                            assistantMsg.tool_steps = [
                                ...(assistantMsg.tool_steps || []),
                                { name: nm, status: 'running' },
                            ];
                            pushSignal(toolWorkingLine(nm));
                        }
                        else if (json.type === 'tool_end' && json.data?.name) {
                            const name = String(json.data.name);
                            const output = String(json.data.output ?? '');
                            const failed = /已跳过|无工具返回|本次超时（|工具输出无法预览/.test(output) ||
                                /\bTimeout\b/i.test(output);
                            const steps = [...(assistantMsg.tool_steps || [])];
                            let idx = -1;
                            for (let i = steps.length - 1; i >= 0; i--) {
                                if (steps[i].name === name && steps[i].status === 'running') {
                                    idx = i;
                                    break;
                                }
                            }
                            if (idx >= 0) {
                                steps[idx] = {
                                    ...steps[idx],
                                    status: failed ? 'error' : 'done',
                                };
                                assistantMsg.tool_steps = steps;
                            }
                        }
                        else if (json.type === 'error' && json.data?.message) {
                            assistantMsg.content = String(json.data.message);
                            bumpMarkdown(true);
                        }
                    }
                    catch {
                        /* ignore malformed sse */
                    }
                }
            }
            if (streamRaf) {
                cancelAnimationFrame(streamRaf);
                streamRaf = 0;
            }
            flushStream();
            const orphan = assistantMsg.tool_steps?.filter((s) => s.status === 'running');
            if (orphan?.length) {
                assistantMsg.tool_steps = (assistantMsg.tool_steps || []).map((s) => s.status === 'running' ? { ...s, status: 'error' } : s);
            }
        }
        else {
            const data = (await res.json());
            assistantMsg.content = sanitizeReplyText(data.content || '');
            if (data.session_id)
                sessionId.value = data.session_id;
            bumpMarkdown(true);
        }
        assistantMsg.loading = false;
        bumpMarkdown(true);
        window.setTimeout(() => {
            liveMissionTitle.value = '';
            signalFeed.value = [];
        }, 700);
    }
    catch {
        assistantMsg.content = '发送失败，请检查网络或重新登录后再试。';
        assistantMsg.loading = false;
        bumpMarkdown(true);
        liveMissionTitle.value = '';
        signalFeed.value = [];
        ElMessage.error('发送失败');
    }
    finally {
        loading.value = false;
        void loadSessions();
    }
}
async function onClear() {
    try {
        await ElMessageBox.confirm('清空当前界面上的对话？（服务器上的历史仍可在左侧找回）', '提示', {
            confirmButtonText: '清空',
            cancelButtonText: '取消',
            type: 'warning',
        });
        messages.value = [];
        sessionId.value = null;
        ElMessage.success('已清空当前对话');
    }
    catch {
        /* cancelled */
    }
}
onMounted(async () => {
    await loadSessions();
    const saved = localStorage.getItem(SESSION_STORAGE_KEY);
    if (saved) {
        await openSessionById(saved);
    }
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['session-row']} */ ;
/** @type {__VLS_StyleScopedClasses['composer-dock']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-mode-toggle']} */ ;
/** @type {__VLS_StyleScopedClasses['el-radio-button__inner']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-input']} */ ;
/** @type {__VLS_StyleScopedClasses['el-textarea__inner']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-input']} */ ;
/** @type {__VLS_StyleScopedClasses['el-textarea__inner']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-send']} */ ;
/** @type {__VLS_StyleScopedClasses['el-button']} */ ;
/** @type {__VLS_StyleScopedClasses['el-button']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "agent-console relative mx-auto flex h-[calc(100vh-3.25rem)] max-w-6xl flex-col gap-0 px-2 pb-3 pt-3 sm:px-3 lg:flex-row lg:gap-4 lg:px-4" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.drawerOpen = true;
        } },
    type: "button",
    ...{ class: "mb-2 flex items-center gap-2 rounded-xl border border-white/[0.08] bg-slate-900/70 px-3 py-2 font-mono text-[11px] text-teal-200/90 backdrop-blur-sm lg:hidden" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span)({
    ...{ class: "h-1.5 w-1.5 rounded-full bg-teal-400 shadow-glow-sm" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.aside, __VLS_intrinsicElements.aside)({
    ...{ class: "hidden w-[260px] shrink-0 flex-col rounded-2xl border border-white/[0.08] bg-slate-950/60 shadow-panel backdrop-blur-sm lg:flex" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "border-b border-white/[0.06] p-3" },
});
const __VLS_0 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    ...{ 'onClick': {} },
    ...{ class: "w-full new-chat-btn" },
    size: "small",
}));
const __VLS_2 = __VLS_1({
    ...{ 'onClick': {} },
    ...{ class: "w-full new-chat-btn" },
    size: "small",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
let __VLS_4;
let __VLS_5;
let __VLS_6;
const __VLS_7 = {
    onClick: (__VLS_ctx.newConversation)
};
__VLS_3.slots.default;
var __VLS_3;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "min-h-0 flex-1 overflow-y-auto p-2" },
});
if (__VLS_ctx.sessionsLoading) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "space-y-2 px-1 py-2" },
    });
    for (const [n] of __VLS_getVForSourceType((5))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div)({
            key: (n),
            ...{ class: "h-11 animate-pulse rounded-xl bg-slate-800/80" },
        });
    }
}
else {
    for (const [s] of __VLS_getVForSourceType((__VLS_ctx.sessions))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!!(__VLS_ctx.sessionsLoading))
                        return;
                    __VLS_ctx.openSessionById(s.id);
                } },
            key: (s.id),
            type: "button",
            ...{ class: "session-row mb-1 w-full rounded-xl px-3 py-2.5 text-left transition-colors" },
            ...{ class: ({ 'session-row--active': s.id === __VLS_ctx.sessionId }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "truncate text-xs font-medium text-slate-200" },
        });
        (__VLS_ctx.sessionTitle(s));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "mt-0.5 font-mono text-[10px] text-slate-500" },
        });
        (__VLS_ctx.formatTime(s.updated_at));
    }
}
if (!__VLS_ctx.sessionsLoading && __VLS_ctx.sessions.length === 0) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "px-2 py-6 text-center text-xs text-slate-500" },
    });
}
const __VLS_8 = {}.Teleport;
/** @type {[typeof __VLS_components.Teleport, typeof __VLS_components.Teleport, ]} */ ;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
    to: "body",
}));
const __VLS_10 = __VLS_9({
    to: "body",
}, ...__VLS_functionalComponentArgsRest(__VLS_9));
__VLS_11.slots.default;
if (__VLS_ctx.drawerOpen) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.drawerOpen))
                    return;
                __VLS_ctx.drawerOpen = false;
            } },
        ...{ class: "fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm lg:hidden" },
    });
}
if (__VLS_ctx.drawerOpen) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.aside, __VLS_intrinsicElements.aside)({
        ...{ class: "fixed inset-y-0 left-0 z-[70] flex w-[min(88vw,300px)] flex-col border-r border-white/[0.08] bg-slate-950/95 shadow-2xl backdrop-blur-md lg:hidden" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "flex items-center justify-between border-b border-white/[0.06] p-3" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "text-xs font-medium text-slate-300" },
    });
    const __VLS_12 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    const __VLS_13 = __VLS_asFunctionalComponent(__VLS_12, new __VLS_12({
        ...{ 'onClick': {} },
        text: true,
        size: "small",
        ...{ class: "!text-slate-400" },
    }));
    const __VLS_14 = __VLS_13({
        ...{ 'onClick': {} },
        text: true,
        size: "small",
        ...{ class: "!text-slate-400" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_13));
    let __VLS_16;
    let __VLS_17;
    let __VLS_18;
    const __VLS_19 = {
        onClick: (...[$event]) => {
            if (!(__VLS_ctx.drawerOpen))
                return;
            __VLS_ctx.drawerOpen = false;
        }
    };
    __VLS_15.slots.default;
    var __VLS_15;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "border-b border-white/[0.06] p-3" },
    });
    const __VLS_20 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({
        ...{ 'onClick': {} },
        ...{ class: "w-full new-chat-btn" },
        size: "small",
    }));
    const __VLS_22 = __VLS_21({
        ...{ 'onClick': {} },
        ...{ class: "w-full new-chat-btn" },
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_21));
    let __VLS_24;
    let __VLS_25;
    let __VLS_26;
    const __VLS_27 = {
        onClick: (__VLS_ctx.newConversation)
    };
    __VLS_23.slots.default;
    var __VLS_23;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "min-h-0 flex-1 overflow-y-auto p-2" },
    });
    for (const [s] of __VLS_getVForSourceType((__VLS_ctx.sessions))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.drawerOpen))
                        return;
                    __VLS_ctx.openSessionById(s.id);
                } },
            key: (s.id),
            type: "button",
            ...{ class: "session-row mb-1 w-full rounded-xl px-3 py-2.5 text-left" },
            ...{ class: ({ 'session-row--active': s.id === __VLS_ctx.sessionId }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "truncate text-xs font-medium text-slate-200" },
        });
        (__VLS_ctx.sessionTitle(s));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "mt-0.5 font-mono text-[10px] text-slate-500" },
        });
        (__VLS_ctx.formatTime(s.updated_at));
    }
}
var __VLS_11;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "flex min-h-0 min-w-0 flex-1 flex-col" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "mb-3 flex flex-wrap items-center justify-between gap-3" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "flex flex-wrap items-center gap-3" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "inline-flex rounded-lg border border-teal-500/20 bg-slate-900/80 p-0.5 shadow-panel backdrop-blur-sm" },
});
const __VLS_28 = {}.ElRadioGroup;
/** @type {[typeof __VLS_components.ElRadioGroup, typeof __VLS_components.elRadioGroup, typeof __VLS_components.ElRadioGroup, typeof __VLS_components.elRadioGroup, ]} */ ;
// @ts-ignore
const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({
    modelValue: (__VLS_ctx.interactionMode),
    size: "small",
    ...{ class: "agent-mode-toggle" },
}));
const __VLS_30 = __VLS_29({
    modelValue: (__VLS_ctx.interactionMode),
    size: "small",
    ...{ class: "agent-mode-toggle" },
}, ...__VLS_functionalComponentArgsRest(__VLS_29));
__VLS_31.slots.default;
const __VLS_32 = {}.ElRadioButton;
/** @type {[typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, ]} */ ;
// @ts-ignore
const __VLS_33 = __VLS_asFunctionalComponent(__VLS_32, new __VLS_32({
    value: "verbose",
}));
const __VLS_34 = __VLS_33({
    value: "verbose",
}, ...__VLS_functionalComponentArgsRest(__VLS_33));
__VLS_35.slots.default;
var __VLS_35;
const __VLS_36 = {}.ElRadioButton;
/** @type {[typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, ]} */ ;
// @ts-ignore
const __VLS_37 = __VLS_asFunctionalComponent(__VLS_36, new __VLS_36({
    value: "quiet",
}));
const __VLS_38 = __VLS_37({
    value: "quiet",
}, ...__VLS_functionalComponentArgsRest(__VLS_37));
__VLS_39.slots.default;
var __VLS_39;
var __VLS_31;
const __VLS_40 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
const __VLS_41 = __VLS_asFunctionalComponent(__VLS_40, new __VLS_40({
    ...{ 'onClick': {} },
    ...{ class: "agent-btn-ghost" },
    size: "small",
    disabled: (__VLS_ctx.loading),
}));
const __VLS_42 = __VLS_41({
    ...{ 'onClick': {} },
    ...{ class: "agent-btn-ghost" },
    size: "small",
    disabled: (__VLS_ctx.loading),
}, ...__VLS_functionalComponentArgsRest(__VLS_41));
let __VLS_44;
let __VLS_45;
let __VLS_46;
const __VLS_47 = {
    onClick: (__VLS_ctx.onClear)
};
__VLS_43.slots.default;
var __VLS_43;
const __VLS_48 = {}.Transition;
/** @type {[typeof __VLS_components.Transition, typeof __VLS_components.Transition, ]} */ ;
// @ts-ignore
const __VLS_49 = __VLS_asFunctionalComponent(__VLS_48, new __VLS_48({
    name: "mission-fade",
}));
const __VLS_50 = __VLS_49({
    name: "mission-fade",
}, ...__VLS_functionalComponentArgsRest(__VLS_49));
__VLS_51.slots.default;
if (__VLS_ctx.loading && (__VLS_ctx.liveMissionTitle || __VLS_ctx.signalFeed.length)) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "mission-panel relative mb-3 overflow-hidden rounded-2xl border border-teal-500/25 bg-gradient-to-r from-slate-950/95 via-slate-900/90 to-slate-950/95 px-4 py-3 shadow-glow-sm backdrop-blur-md" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div)({
        ...{ class: "mission-grid-bg pointer-events-none absolute inset-0 opacity-30" },
        'aria-hidden': "true",
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "relative flex flex-wrap items-start gap-4" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "mission-bars flex shrink-0 gap-0.5 pt-1" },
        'aria-hidden': "true",
    });
    for (const [b] of __VLS_getVForSourceType((5))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span)({
            key: (b),
            ...{ class: "mission-bar" },
            ...{ style: ({ animationDelay: `${b * 0.12}s` }) },
        });
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "min-w-0 flex-1" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "font-display text-[15px] font-semibold tracking-tight text-white" },
    });
    (__VLS_ctx.liveMissionTitle || '正在 · 推理编排中');
    if (__VLS_ctx.lastAssistantForStatus) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "mt-1 font-mono text-[11px] leading-relaxed text-teal-100/85" },
        });
        (__VLS_ctx.assistantStatusLine(__VLS_ctx.lastAssistantForStatus));
    }
    if (__VLS_ctx.signalFeed.length) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "relative mt-3 flex max-h-16 flex-wrap gap-1.5 overflow-y-auto pr-1 font-mono text-[10px] leading-snug" },
        });
        for (const [s] of __VLS_getVForSourceType((__VLS_ctx.signalFeed))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                key: (s.id),
                ...{ class: "signal-chip rounded-md border border-white/[0.06] bg-black/25 px-2 py-1 text-slate-400" },
            });
            (s.text);
        }
    }
}
var __VLS_51;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ref: "scrollRef",
    ...{ class: "agent-scroll relative min-h-0 flex-1 overflow-y-auto rounded-2xl border border-white/[0.08] bg-slate-950/50 p-4 shadow-panel backdrop-blur-sm sm:p-5" },
});
/** @type {typeof __VLS_ctx.scrollRef} */ ;
if (__VLS_ctx.messages.length === 0) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "flex flex-col items-center justify-center px-4 py-24 text-center" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div)({
        ...{ class: "agent-orbit mb-6 h-14 w-14 rounded-full border border-teal-500/30 shadow-glow-sm" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "font-display text-base font-semibold text-white" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "mt-2 max-w-sm text-sm leading-relaxed text-slate-500" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({
        ...{ class: "text-slate-400" },
    });
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "space-y-6" },
    });
    for (const [msg, idx] of __VLS_getVForSourceType((__VLS_ctx.messages))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            key: (idx),
            ...{ class: (msg.role === 'user' ? 'flex justify-end' : 'flex justify-start') },
        });
        if (msg.role === 'user') {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "max-w-[min(100%,40rem)] rounded-2xl border border-teal-500/25 bg-gradient-to-br from-teal-950/80 to-slate-900/90 px-4 py-3 text-sm text-slate-100 shadow-glow-sm" },
            });
            (msg.content);
        }
        else {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "agent-assistant-bubble w-full max-w-[min(100%,48rem)] overflow-hidden rounded-2xl border border-white/[0.07] bg-slate-900/70 shadow-panel" },
                ...{ class: ({ 'agent-assistant-bubble--live': msg.loading }) },
            });
            if (msg.loading && __VLS_ctx.assistantStatusLine(msg)) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "relative border-b border-white/[0.06] bg-slate-950/80 px-4 py-3" },
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div)({
                    ...{ class: "agent-scanline pointer-events-none absolute inset-0 opacity-40" },
                    'aria-hidden': "true",
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div)({
                    ...{ class: "neural-line pointer-events-none absolute bottom-0 left-0 h-0.5 w-full opacity-80" },
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "relative flex items-center gap-3" },
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div)({
                    ...{ class: "agent-pulse-ring shrink-0" },
                });
                const __VLS_52 = {}.Transition;
                /** @type {[typeof __VLS_components.Transition, typeof __VLS_components.Transition, ]} */ ;
                // @ts-ignore
                const __VLS_53 = __VLS_asFunctionalComponent(__VLS_52, new __VLS_52({
                    name: "status-line",
                    mode: "out-in",
                }));
                const __VLS_54 = __VLS_53({
                    name: "status-line",
                    mode: "out-in",
                }, ...__VLS_functionalComponentArgsRest(__VLS_53));
                __VLS_55.slots.default;
                __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
                    key: (__VLS_ctx.assistantStatusLine(msg)),
                    ...{ class: "min-w-0 flex-1 font-mono text-[12px] leading-snug tracking-wide text-teal-100/95" },
                });
                (__VLS_ctx.assistantStatusLine(msg));
                var __VLS_55;
            }
            if (msg.content.trim().length > 0 || !msg.loading) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                    ...{ class: "agent-answer px-4 py-4 sm:px-5 sm:py-5" },
                    ...{ class: ({ 'agent-answer--streaming': msg.loading && msg.content.trim().length > 0 }) },
                });
                __VLS_asFunctionalElement(__VLS_intrinsicElements.div)({
                    ...{ class: "prose prose-invert prose-sm max-w-none prose-headings:font-display prose-p:text-slate-300 prose-a:text-teal-400 prose-strong:text-white" },
                });
                __VLS_asFunctionalDirective(__VLS_directives.vHtml)(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.assistantBubbleHtml(msg, idx)) }, null, null);
                if (msg.loading && msg.content.trim().length > 0) {
                    __VLS_asFunctionalElement(__VLS_intrinsicElements.span)({
                        ...{ class: "agent-caret ml-0.5 inline-block h-3.5 w-0.5 translate-y-0.5 bg-teal-400 shadow-glow-sm" },
                        'aria-hidden': "true",
                    });
                }
            }
        }
    }
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "composer-dock mt-4 shrink-0" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "composer-inner flex gap-2 rounded-2xl border border-white/[0.08] bg-slate-950/85 p-2 shadow-panel backdrop-blur-md" },
});
const __VLS_56 = {}.ElInput;
/** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
// @ts-ignore
const __VLS_57 = __VLS_asFunctionalComponent(__VLS_56, new __VLS_56({
    ...{ 'onKeydown': {} },
    modelValue: (__VLS_ctx.input),
    type: "textarea",
    autosize: ({ minRows: 1, maxRows: 6 }),
    placeholder: "描述你的旅行想法 — Enter 发送 · Shift+Enter 换行",
    ...{ class: "agent-input flex-1" },
}));
const __VLS_58 = __VLS_57({
    ...{ 'onKeydown': {} },
    modelValue: (__VLS_ctx.input),
    type: "textarea",
    autosize: ({ minRows: 1, maxRows: 6 }),
    placeholder: "描述你的旅行想法 — Enter 发送 · Shift+Enter 换行",
    ...{ class: "agent-input flex-1" },
}, ...__VLS_functionalComponentArgsRest(__VLS_57));
let __VLS_60;
let __VLS_61;
let __VLS_62;
const __VLS_63 = {
    onKeydown: (__VLS_ctx.onSend)
};
var __VLS_59;
const __VLS_64 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
const __VLS_65 = __VLS_asFunctionalComponent(__VLS_64, new __VLS_64({
    ...{ 'onClick': {} },
    ...{ class: "agent-send shrink-0 self-end" },
    loading: (__VLS_ctx.loading),
}));
const __VLS_66 = __VLS_65({
    ...{ 'onClick': {} },
    ...{ class: "agent-send shrink-0 self-end" },
    loading: (__VLS_ctx.loading),
}, ...__VLS_functionalComponentArgsRest(__VLS_65));
let __VLS_68;
let __VLS_69;
let __VLS_70;
const __VLS_71 = {
    onClick: (__VLS_ctx.onSend)
};
__VLS_67.slots.default;
var __VLS_67;
/** @type {__VLS_StyleScopedClasses['agent-console']} */ ;
/** @type {__VLS_StyleScopedClasses['relative']} */ ;
/** @type {__VLS_StyleScopedClasses['mx-auto']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['h-[calc(100vh-3.25rem)]']} */ ;
/** @type {__VLS_StyleScopedClasses['max-w-6xl']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-col']} */ ;
/** @type {__VLS_StyleScopedClasses['gap-0']} */ ;
/** @type {__VLS_StyleScopedClasses['px-2']} */ ;
/** @type {__VLS_StyleScopedClasses['pb-3']} */ ;
/** @type {__VLS_StyleScopedClasses['pt-3']} */ ;
/** @type {__VLS_StyleScopedClasses['sm:px-3']} */ ;
/** @type {__VLS_StyleScopedClasses['lg:flex-row']} */ ;
/** @type {__VLS_StyleScopedClasses['lg:gap-4']} */ ;
/** @type {__VLS_StyleScopedClasses['lg:px-4']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-2']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['items-center']} */ ;
/** @type {__VLS_StyleScopedClasses['gap-2']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-xl']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.08]']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-slate-900/70']} */ ;
/** @type {__VLS_StyleScopedClasses['px-3']} */ ;
/** @type {__VLS_StyleScopedClasses['py-2']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['text-[11px]']} */ ;
/** @type {__VLS_StyleScopedClasses['text-teal-200/90']} */ ;
/** @type {__VLS_StyleScopedClasses['backdrop-blur-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['lg:hidden']} */ ;
/** @type {__VLS_StyleScopedClasses['h-1.5']} */ ;
/** @type {__VLS_StyleScopedClasses['w-1.5']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-full']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-teal-400']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-glow-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['hidden']} */ ;
/** @type {__VLS_StyleScopedClasses['w-[260px]']} */ ;
/** @type {__VLS_StyleScopedClasses['shrink-0']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-col']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-2xl']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.08]']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-slate-950/60']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['backdrop-blur-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['lg:flex']} */ ;
/** @type {__VLS_StyleScopedClasses['border-b']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.06]']} */ ;
/** @type {__VLS_StyleScopedClasses['p-3']} */ ;
/** @type {__VLS_StyleScopedClasses['w-full']} */ ;
/** @type {__VLS_StyleScopedClasses['new-chat-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['min-h-0']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-1']} */ ;
/** @type {__VLS_StyleScopedClasses['overflow-y-auto']} */ ;
/** @type {__VLS_StyleScopedClasses['p-2']} */ ;
/** @type {__VLS_StyleScopedClasses['space-y-2']} */ ;
/** @type {__VLS_StyleScopedClasses['px-1']} */ ;
/** @type {__VLS_StyleScopedClasses['py-2']} */ ;
/** @type {__VLS_StyleScopedClasses['h-11']} */ ;
/** @type {__VLS_StyleScopedClasses['animate-pulse']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-xl']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-slate-800/80']} */ ;
/** @type {__VLS_StyleScopedClasses['session-row']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-1']} */ ;
/** @type {__VLS_StyleScopedClasses['w-full']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-xl']} */ ;
/** @type {__VLS_StyleScopedClasses['px-3']} */ ;
/** @type {__VLS_StyleScopedClasses['py-2.5']} */ ;
/** @type {__VLS_StyleScopedClasses['text-left']} */ ;
/** @type {__VLS_StyleScopedClasses['transition-colors']} */ ;
/** @type {__VLS_StyleScopedClasses['truncate']} */ ;
/** @type {__VLS_StyleScopedClasses['text-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['font-medium']} */ ;
/** @type {__VLS_StyleScopedClasses['text-slate-200']} */ ;
/** @type {__VLS_StyleScopedClasses['mt-0.5']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['text-[10px]']} */ ;
/** @type {__VLS_StyleScopedClasses['text-slate-500']} */ ;
/** @type {__VLS_StyleScopedClasses['px-2']} */ ;
/** @type {__VLS_StyleScopedClasses['py-6']} */ ;
/** @type {__VLS_StyleScopedClasses['text-center']} */ ;
/** @type {__VLS_StyleScopedClasses['text-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['text-slate-500']} */ ;
/** @type {__VLS_StyleScopedClasses['fixed']} */ ;
/** @type {__VLS_StyleScopedClasses['inset-0']} */ ;
/** @type {__VLS_StyleScopedClasses['z-[60]']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-black/60']} */ ;
/** @type {__VLS_StyleScopedClasses['backdrop-blur-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['lg:hidden']} */ ;
/** @type {__VLS_StyleScopedClasses['fixed']} */ ;
/** @type {__VLS_StyleScopedClasses['inset-y-0']} */ ;
/** @type {__VLS_StyleScopedClasses['left-0']} */ ;
/** @type {__VLS_StyleScopedClasses['z-[70]']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['w-[min(88vw,300px)]']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-col']} */ ;
/** @type {__VLS_StyleScopedClasses['border-r']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.08]']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-slate-950/95']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-2xl']} */ ;
/** @type {__VLS_StyleScopedClasses['backdrop-blur-md']} */ ;
/** @type {__VLS_StyleScopedClasses['lg:hidden']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['items-center']} */ ;
/** @type {__VLS_StyleScopedClasses['justify-between']} */ ;
/** @type {__VLS_StyleScopedClasses['border-b']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.06]']} */ ;
/** @type {__VLS_StyleScopedClasses['p-3']} */ ;
/** @type {__VLS_StyleScopedClasses['text-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['font-medium']} */ ;
/** @type {__VLS_StyleScopedClasses['text-slate-300']} */ ;
/** @type {__VLS_StyleScopedClasses['!text-slate-400']} */ ;
/** @type {__VLS_StyleScopedClasses['border-b']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.06]']} */ ;
/** @type {__VLS_StyleScopedClasses['p-3']} */ ;
/** @type {__VLS_StyleScopedClasses['w-full']} */ ;
/** @type {__VLS_StyleScopedClasses['new-chat-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['min-h-0']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-1']} */ ;
/** @type {__VLS_StyleScopedClasses['overflow-y-auto']} */ ;
/** @type {__VLS_StyleScopedClasses['p-2']} */ ;
/** @type {__VLS_StyleScopedClasses['session-row']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-1']} */ ;
/** @type {__VLS_StyleScopedClasses['w-full']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-xl']} */ ;
/** @type {__VLS_StyleScopedClasses['px-3']} */ ;
/** @type {__VLS_StyleScopedClasses['py-2.5']} */ ;
/** @type {__VLS_StyleScopedClasses['text-left']} */ ;
/** @type {__VLS_StyleScopedClasses['truncate']} */ ;
/** @type {__VLS_StyleScopedClasses['text-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['font-medium']} */ ;
/** @type {__VLS_StyleScopedClasses['text-slate-200']} */ ;
/** @type {__VLS_StyleScopedClasses['mt-0.5']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['text-[10px]']} */ ;
/** @type {__VLS_StyleScopedClasses['text-slate-500']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['min-h-0']} */ ;
/** @type {__VLS_StyleScopedClasses['min-w-0']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-1']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-col']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-3']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['items-center']} */ ;
/** @type {__VLS_StyleScopedClasses['justify-between']} */ ;
/** @type {__VLS_StyleScopedClasses['gap-3']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['items-center']} */ ;
/** @type {__VLS_StyleScopedClasses['gap-3']} */ ;
/** @type {__VLS_StyleScopedClasses['inline-flex']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-lg']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['border-teal-500/20']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-slate-900/80']} */ ;
/** @type {__VLS_StyleScopedClasses['p-0.5']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['backdrop-blur-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-mode-toggle']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-btn-ghost']} */ ;
/** @type {__VLS_StyleScopedClasses['mission-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['relative']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-3']} */ ;
/** @type {__VLS_StyleScopedClasses['overflow-hidden']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-2xl']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['border-teal-500/25']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-gradient-to-r']} */ ;
/** @type {__VLS_StyleScopedClasses['from-slate-950/95']} */ ;
/** @type {__VLS_StyleScopedClasses['via-slate-900/90']} */ ;
/** @type {__VLS_StyleScopedClasses['to-slate-950/95']} */ ;
/** @type {__VLS_StyleScopedClasses['px-4']} */ ;
/** @type {__VLS_StyleScopedClasses['py-3']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-glow-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['backdrop-blur-md']} */ ;
/** @type {__VLS_StyleScopedClasses['mission-grid-bg']} */ ;
/** @type {__VLS_StyleScopedClasses['pointer-events-none']} */ ;
/** @type {__VLS_StyleScopedClasses['absolute']} */ ;
/** @type {__VLS_StyleScopedClasses['inset-0']} */ ;
/** @type {__VLS_StyleScopedClasses['opacity-30']} */ ;
/** @type {__VLS_StyleScopedClasses['relative']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['items-start']} */ ;
/** @type {__VLS_StyleScopedClasses['gap-4']} */ ;
/** @type {__VLS_StyleScopedClasses['mission-bars']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['shrink-0']} */ ;
/** @type {__VLS_StyleScopedClasses['gap-0.5']} */ ;
/** @type {__VLS_StyleScopedClasses['pt-1']} */ ;
/** @type {__VLS_StyleScopedClasses['mission-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['min-w-0']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-1']} */ ;
/** @type {__VLS_StyleScopedClasses['font-display']} */ ;
/** @type {__VLS_StyleScopedClasses['text-[15px]']} */ ;
/** @type {__VLS_StyleScopedClasses['font-semibold']} */ ;
/** @type {__VLS_StyleScopedClasses['tracking-tight']} */ ;
/** @type {__VLS_StyleScopedClasses['text-white']} */ ;
/** @type {__VLS_StyleScopedClasses['mt-1']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['text-[11px]']} */ ;
/** @type {__VLS_StyleScopedClasses['leading-relaxed']} */ ;
/** @type {__VLS_StyleScopedClasses['text-teal-100/85']} */ ;
/** @type {__VLS_StyleScopedClasses['relative']} */ ;
/** @type {__VLS_StyleScopedClasses['mt-3']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['max-h-16']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['gap-1.5']} */ ;
/** @type {__VLS_StyleScopedClasses['overflow-y-auto']} */ ;
/** @type {__VLS_StyleScopedClasses['pr-1']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['text-[10px]']} */ ;
/** @type {__VLS_StyleScopedClasses['leading-snug']} */ ;
/** @type {__VLS_StyleScopedClasses['signal-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-md']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.06]']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-black/25']} */ ;
/** @type {__VLS_StyleScopedClasses['px-2']} */ ;
/** @type {__VLS_StyleScopedClasses['py-1']} */ ;
/** @type {__VLS_StyleScopedClasses['text-slate-400']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-scroll']} */ ;
/** @type {__VLS_StyleScopedClasses['relative']} */ ;
/** @type {__VLS_StyleScopedClasses['min-h-0']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-1']} */ ;
/** @type {__VLS_StyleScopedClasses['overflow-y-auto']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-2xl']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.08]']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-slate-950/50']} */ ;
/** @type {__VLS_StyleScopedClasses['p-4']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['backdrop-blur-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['sm:p-5']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-col']} */ ;
/** @type {__VLS_StyleScopedClasses['items-center']} */ ;
/** @type {__VLS_StyleScopedClasses['justify-center']} */ ;
/** @type {__VLS_StyleScopedClasses['px-4']} */ ;
/** @type {__VLS_StyleScopedClasses['py-24']} */ ;
/** @type {__VLS_StyleScopedClasses['text-center']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-orbit']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-6']} */ ;
/** @type {__VLS_StyleScopedClasses['h-14']} */ ;
/** @type {__VLS_StyleScopedClasses['w-14']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-full']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['border-teal-500/30']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-glow-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['font-display']} */ ;
/** @type {__VLS_StyleScopedClasses['text-base']} */ ;
/** @type {__VLS_StyleScopedClasses['font-semibold']} */ ;
/** @type {__VLS_StyleScopedClasses['text-white']} */ ;
/** @type {__VLS_StyleScopedClasses['mt-2']} */ ;
/** @type {__VLS_StyleScopedClasses['max-w-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['text-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['leading-relaxed']} */ ;
/** @type {__VLS_StyleScopedClasses['text-slate-500']} */ ;
/** @type {__VLS_StyleScopedClasses['text-slate-400']} */ ;
/** @type {__VLS_StyleScopedClasses['space-y-6']} */ ;
/** @type {__VLS_StyleScopedClasses['max-w-[min(100%,40rem)]']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-2xl']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['border-teal-500/25']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-gradient-to-br']} */ ;
/** @type {__VLS_StyleScopedClasses['from-teal-950/80']} */ ;
/** @type {__VLS_StyleScopedClasses['to-slate-900/90']} */ ;
/** @type {__VLS_StyleScopedClasses['px-4']} */ ;
/** @type {__VLS_StyleScopedClasses['py-3']} */ ;
/** @type {__VLS_StyleScopedClasses['text-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['text-slate-100']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-glow-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-assistant-bubble']} */ ;
/** @type {__VLS_StyleScopedClasses['w-full']} */ ;
/** @type {__VLS_StyleScopedClasses['max-w-[min(100%,48rem)]']} */ ;
/** @type {__VLS_StyleScopedClasses['overflow-hidden']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-2xl']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.07]']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-slate-900/70']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['relative']} */ ;
/** @type {__VLS_StyleScopedClasses['border-b']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.06]']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-slate-950/80']} */ ;
/** @type {__VLS_StyleScopedClasses['px-4']} */ ;
/** @type {__VLS_StyleScopedClasses['py-3']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-scanline']} */ ;
/** @type {__VLS_StyleScopedClasses['pointer-events-none']} */ ;
/** @type {__VLS_StyleScopedClasses['absolute']} */ ;
/** @type {__VLS_StyleScopedClasses['inset-0']} */ ;
/** @type {__VLS_StyleScopedClasses['opacity-40']} */ ;
/** @type {__VLS_StyleScopedClasses['neural-line']} */ ;
/** @type {__VLS_StyleScopedClasses['pointer-events-none']} */ ;
/** @type {__VLS_StyleScopedClasses['absolute']} */ ;
/** @type {__VLS_StyleScopedClasses['bottom-0']} */ ;
/** @type {__VLS_StyleScopedClasses['left-0']} */ ;
/** @type {__VLS_StyleScopedClasses['h-0.5']} */ ;
/** @type {__VLS_StyleScopedClasses['w-full']} */ ;
/** @type {__VLS_StyleScopedClasses['opacity-80']} */ ;
/** @type {__VLS_StyleScopedClasses['relative']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['items-center']} */ ;
/** @type {__VLS_StyleScopedClasses['gap-3']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-pulse-ring']} */ ;
/** @type {__VLS_StyleScopedClasses['shrink-0']} */ ;
/** @type {__VLS_StyleScopedClasses['min-w-0']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-1']} */ ;
/** @type {__VLS_StyleScopedClasses['font-mono']} */ ;
/** @type {__VLS_StyleScopedClasses['text-[12px]']} */ ;
/** @type {__VLS_StyleScopedClasses['leading-snug']} */ ;
/** @type {__VLS_StyleScopedClasses['tracking-wide']} */ ;
/** @type {__VLS_StyleScopedClasses['text-teal-100/95']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-answer']} */ ;
/** @type {__VLS_StyleScopedClasses['px-4']} */ ;
/** @type {__VLS_StyleScopedClasses['py-4']} */ ;
/** @type {__VLS_StyleScopedClasses['sm:px-5']} */ ;
/** @type {__VLS_StyleScopedClasses['sm:py-5']} */ ;
/** @type {__VLS_StyleScopedClasses['prose']} */ ;
/** @type {__VLS_StyleScopedClasses['prose-invert']} */ ;
/** @type {__VLS_StyleScopedClasses['prose-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['max-w-none']} */ ;
/** @type {__VLS_StyleScopedClasses['prose-headings:font-display']} */ ;
/** @type {__VLS_StyleScopedClasses['prose-p:text-slate-300']} */ ;
/** @type {__VLS_StyleScopedClasses['prose-a:text-teal-400']} */ ;
/** @type {__VLS_StyleScopedClasses['prose-strong:text-white']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-caret']} */ ;
/** @type {__VLS_StyleScopedClasses['ml-0.5']} */ ;
/** @type {__VLS_StyleScopedClasses['inline-block']} */ ;
/** @type {__VLS_StyleScopedClasses['h-3.5']} */ ;
/** @type {__VLS_StyleScopedClasses['w-0.5']} */ ;
/** @type {__VLS_StyleScopedClasses['translate-y-0.5']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-teal-400']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-glow-sm']} */ ;
/** @type {__VLS_StyleScopedClasses['composer-dock']} */ ;
/** @type {__VLS_StyleScopedClasses['mt-4']} */ ;
/** @type {__VLS_StyleScopedClasses['shrink-0']} */ ;
/** @type {__VLS_StyleScopedClasses['composer-inner']} */ ;
/** @type {__VLS_StyleScopedClasses['flex']} */ ;
/** @type {__VLS_StyleScopedClasses['gap-2']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded-2xl']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['border-white/[0.08]']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-slate-950/85']} */ ;
/** @type {__VLS_StyleScopedClasses['p-2']} */ ;
/** @type {__VLS_StyleScopedClasses['shadow-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['backdrop-blur-md']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-input']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-1']} */ ;
/** @type {__VLS_StyleScopedClasses['agent-send']} */ ;
/** @type {__VLS_StyleScopedClasses['shrink-0']} */ ;
/** @type {__VLS_StyleScopedClasses['self-end']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            messages: messages,
            sessionId: sessionId,
            loading: loading,
            input: input,
            scrollRef: scrollRef,
            interactionMode: interactionMode,
            sessions: sessions,
            sessionsLoading: sessionsLoading,
            drawerOpen: drawerOpen,
            liveMissionTitle: liveMissionTitle,
            signalFeed: signalFeed,
            lastAssistantForStatus: lastAssistantForStatus,
            assistantBubbleHtml: assistantBubbleHtml,
            assistantStatusLine: assistantStatusLine,
            sessionTitle: sessionTitle,
            formatTime: formatTime,
            openSessionById: openSessionById,
            newConversation: newConversation,
            onSend: onSend,
            onClear: onClear,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
