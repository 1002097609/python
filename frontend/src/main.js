import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 动态更新页面标题
router.afterEach((to) => {
  const title = to.meta?.title
  document.title = title ? `${title} — 素材拆解与裂变系统` : '素材拆解与裂变系统'
})

app.mount('#app')
