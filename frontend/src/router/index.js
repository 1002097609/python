import { createRouter, createWebHistory } from 'vue-router'
import Dismantle from '../views/Dismantle.vue'
import MaterialLib from '../views/MaterialLib.vue'
import Fission from '../views/Fission.vue'
import SkeletonLib from '../views/SkeletonLib.vue'

const routes = [
  { path: '/', name: 'Dismantle', component: Dismantle, meta: { title: '素材拆解' } },
  { path: '/material-lib', name: 'MaterialLib', component: MaterialLib, meta: { title: '素材库' } },
  { path: '/fission', name: 'Fission', component: Fission, meta: { title: '素材裂变' } },
  { path: '/skeleton-lib', name: 'SkeletonLib', component: SkeletonLib, meta: { title: '骨架库' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
