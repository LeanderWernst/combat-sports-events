import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config';
import { definePreset } from '@primevue/themes';
import Aura from '@primevue/themes/aura';
import ToastService from 'primevue/toastservice';

import App from './App.vue'
import router from './router'

const app = createApp(App)

const MyPreset = definePreset(Aura, {
    semantic: {
        primary: {
            50: '{red.50}',
            100: '{red.100}',
            200: '{red.200}',
            300: '{red.300}',
            400: '{red.400}',
            500: '{red.500}',
            600: '{red.600}',
            700: '{red.700}',
            800: '{red.800}',
            900: '{red.900}',
            950: '{red.950}'
        }
    }
});

app.use(createPinia())
app.use(ToastService)
app.use(router)
app.use(PrimeVue, {
    theme: {
        preset: MyPreset,
        options: {
            prefix: 'p',
            cssLayer: false,
        }
    }
});

app.mount('#app')
