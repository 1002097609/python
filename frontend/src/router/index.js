import { createRouter, createWebHistory } from 'vue-router'
import Dismantle from '../views/Dismantle.vue'
import MaterialLib from '../views/MaterialLib.vue'
import Fission from '../views/Fission.vue'
import SkeletonLib from '../views/SkeletonLib.vue'
import OptionManage from '../views/OptionManage.vue'
import FissionRecords from '../views/FissionRecords.vue'
import TagManage from '../views/TagManage.vue'
import Dashboard from '../views/Dashboard.vue'

const routes = [
  { path: '/', name: 'Dismantle', component: Dismantle, meta: { title: '素材拆解' } },
  { path: '/material-lib', name: 'MaterialLib', component: MaterialLib, meta: { title: '素材库' } },
  { path: '/fission', name: 'Fission', component: Fission, meta: { title: '素材裂变' } },
  { path: '/skeleton-lib', name: 'SkeletonLib', component: SkeletonLib, meta: { title: '骨架库' } },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { title: '数据统计' } },
  { path: '/fission-records', name: 'FissionRecords', component: FissionRecords, meta: { title: '裂变记录' } },
  { path: '/option-manage', name: 'OptionManage', component: OptionManage, meta: { title: '选项管理' } },
  { path: '/tag-manage', name: 'TagManage', component: TagManage, meta: { title: '标签管理' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
