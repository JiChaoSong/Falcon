import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'ant-design-vue/dist/reset.css'
import {createPinia} from "pinia";

// 创建实例
const app = createApp(App)
const pinia = createPinia()

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
    console.error('Vue error:', err)
    console.log('Component instance:', instance)
    console.log('Error info:', info)
}

// 使用插件
app.use(pinia)
app.use(router)

app.mount('#app')