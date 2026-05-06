import { createApp } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import zhCn from 'element-plus/es/locale/lang/zh-cn';
import App from './App.vue';
import router from './router';
import { useUserStore } from './stores/user';
import './style.css';
const app = createApp(App);
const pinia = createPinia();
setActivePinia(pinia);
app.use(pinia);
app.use(router);
app.use(ElementPlus, { locale: zhCn });
void router.isReady().then(async () => {
    await useUserStore().bootstrap();
    app.mount('#app');
});
