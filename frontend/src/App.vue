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
/* 全局样式已移至 style.css */
</style>
