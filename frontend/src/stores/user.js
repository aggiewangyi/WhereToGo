import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import api, { getToken, setToken } from '@/services/api';
import { authMe } from '@/services/auth';
export const useUserStore = defineStore('user', () => {
    const token = ref(getToken());
    const user = ref(null);
    const isLoggedIn = computed(() => Boolean(token.value));
    async function bootstrap() {
        if (!getToken()) {
            token.value = null;
            user.value = null;
            return;
        }
        token.value = getToken();
        try {
            user.value = await authMe();
        }
        catch {
            setToken(null);
            token.value = null;
            user.value = null;
        }
    }
    async function login(phone, password) {
        const { data } = await api.post('/auth/login', { phone, password });
        setToken(data.access_token);
        token.value = data.access_token;
        user.value = await authMe();
    }
    async function register(payload) {
        const { data } = await api.post('/auth/register', payload);
        setToken(data.access_token);
        token.value = data.access_token;
        user.value = await authMe();
    }
    function logout() {
        setToken(null);
        token.value = null;
        user.value = null;
        localStorage.removeItem('wheretogo_chat_session_id');
    }
    return { token, user, isLoggedIn, bootstrap, login, register, logout };
});
