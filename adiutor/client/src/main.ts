import './assets/base.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import initGlobal from './mixins/Global'

const app = createApp(App)

app.use(ElementPlus)
app.use(createPinia())
app.use(router)
initGlobal(app)

app.mount('#vue-app')
console.log(import.meta,import.meta.env)