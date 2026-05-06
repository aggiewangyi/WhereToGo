import { agentHeaders, getToken } from './api';
import api from './api';
function streamHeaders() {
    const h = {
        'Content-Type': 'application/json',
        ...agentHeaders(),
    };
    const t = getToken();
    if (t)
        h.Authorization = `Bearer ${t}`;
    return h;
}
export async function listAgentSessions() {
    const { data } = await api.get('/agent/sessions');
    return data;
}
export async function getAgentSessionMessages(sessionId) {
    const { data } = await api.get(`/agent/sessions/${encodeURIComponent(sessionId)}/messages`);
    return data;
}
/** 阻塞式整段回复 */
export async function agentChatBlocking(message, options) {
    const res = await fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: streamHeaders(),
        body: JSON.stringify({
            message,
            stream: false,
            session_id: options?.session_id || undefined,
            history: options?.history,
            interaction_mode: options?.interaction_mode,
        }),
    });
    if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(text || `HTTP ${res.status}`);
    }
    return res.json();
}
/** SSE */
export function agentChatStream(message, options) {
    const { session_id, history, interaction_mode } = options || {};
    return fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: streamHeaders(),
        body: JSON.stringify({
            message,
            stream: true,
            ...(session_id ? { session_id } : {}),
            history,
            interaction_mode,
        }),
    });
}
