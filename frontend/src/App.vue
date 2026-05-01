<template>
  <div class="layout">
    <!-- 顶部导航 -->
    <div class="navbar">
      <div class="logo">
        🌳 素材拆解与裂变系统
        <em>Marketing Material Intelligence</em>
      </div>
      <div class="nav-tabs">
        <router-link
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          class="nav-tab"
          :class="{ active: $route.path === tab.path }"
        >
          {{ tab.icon }} {{ tab.label }}
        </router-link>
        <el-dropdown trigger="click" class="nav-dropdown">
          <span class="nav-tab">更多 ▾</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>
                <router-link to="/tag-manage" class="dropdown-link">🏷️ 标签管理</router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/fission-records" class="dropdown-link">📋 裂变记录</router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/option-manage" class="dropdown-link">⚙️ 选项管理</router-link>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 页面内容 -->
    <div class="content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
const tabs = [
  { path: '/dashboard', label: '数据统计', icon: '📊' },
  { path: '/', label: '素材拆解', icon: '🔍' },
  { path: '/material-lib', label: '素材库', icon: '📚' },
  { path: '/fission', label: '素材裂变', icon: '⚡' },
  { path: '/skeleton-lib', label: '骨架库', icon: '🦴' },
]
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f0f2f5;
  color: #1a1a2e;
}

.layout { min-height: 100vh; }

.navbar {
  background: linear-gradient(135deg, #667eea, #764ba2);
  padding: 0 32px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}
.logo em {
  font-size: 12px;
  opacity: .7;
  margin-left: 8px;
  font-style: normal;
}

.nav-tabs { display: flex; gap: 4px; }

.nav-tab {
  padding: 8px 20px;
  border-radius: 8px 8px 0 0;
  color: rgba(255,255,255,.7);
  text-decoration: none;
  font-size: 14px;
  transition: all .2s;
  cursor: pointer;
}

.nav-tab.active {
  background: #f0f2f5;
  color: #667eea;
  font-weight: 600;
}

.nav-tab:hover:not(.active) {
  color: #fff;
  background: rgba(255,255,255,.1);
}

.nav-dropdown { margin-left: 4px; }
.dropdown-link { text-decoration: none; color: #333; display: block; }

.content { min-height: calc(100vh - 60px); }
</style>
