<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import { CONFIG } from './config'

import LoginPanel from './components/panels/LoginPanel.vue'
import MultiAgentView from './views/MultiAgentView.vue'

const authStore = useAuthStore()

onMounted(() => {
  authStore.init()
  console.log(`[App] TopMat v${CONFIG.version} - ${CONFIG.mode} 模式`)
})
</script>

<template>
  <LoginPanel v-if="!authStore.isAuthenticated" />
  <MultiAgentView v-else />
</template>

<style>
/* 全局样式 */
:root {
  --primary: #667eea;
  --primary-dark: #764ba2;
  --success: #4caf50;
  --warning: #ff9800;
  --danger: #f44336;
  --info: #2196f3;
  --border-color: #e0e0e0;
  --text-primary: #333;
  --text-secondary: #666;
  --bg-light: #f5f7fa;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100vh;
  overflow: hidden;
}
</style>
