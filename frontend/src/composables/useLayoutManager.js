/**
 * 布局管理逻辑 - 从App.vue提取
 * 负责处理三栏布局的拖拽调整
 */
import { ref } from 'vue'

export function useLayoutManager() {
  // 面板宽度（左侧、右侧）
  const leftWidth = ref(360)
  const rightWidth = ref(520)
  
  /**
   * 根据整体可用宽度，按比例更新左右面板宽度
   * 在 App.vue 中通过 window.innerWidth 调用，实现基础响应式
   */
  const applyResponsiveWidth = (totalWidth) => {
    if (!totalWidth || Number.isNaN(totalWidth)) return
    
    // 预留一定空间给中间面板和拖动条
    const available = Math.max(totalWidth, 1024)
    const baseLeft = available * 0.22 // 左侧约占 22%
    const baseRight = available * 0.28 // 右侧约占 28%
    
    // 与拖拽时一致的安全范围
    leftWidth.value = Math.max(280, Math.min(420, baseLeft))
    rightWidth.value = Math.max(360, Math.min(720, baseRight))
  }
  
  // 拖动状态
  let isResizing = false
  let resizeDirection = null
  let startX = 0
  let startWidth = 0
  
  /**
   * 开始拖动
   * @param {MouseEvent} e - 鼠标事件
   * @param {string} direction - 拖动方向 'left' | 'right'
   */
  const startResize = (e, direction) => {
    isResizing = true
    resizeDirection = direction
    startX = e.clientX
    startWidth = direction === 'left' ? leftWidth.value : rightWidth.value
    
    document.addEventListener('mousemove', handleResize)
    document.addEventListener('mouseup', stopResize)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }
  
  /**
   * 拖动中
   * @param {MouseEvent} e - 鼠标事件
   */
  const handleResize = (e) => {
    if (!isResizing) return
    
    const delta = e.clientX - startX
    
    if (resizeDirection === 'left') {
      // 左侧面板：向右拖动增大，向左拖动减小
      const newWidth = startWidth + delta
      leftWidth.value = Math.max(280, Math.min(420, newWidth))
    } else if (resizeDirection === 'right') {
      // 右侧面板：向左拖动增大，向右拖动减小
      const newWidth = startWidth - delta
      rightWidth.value = Math.max(360, Math.min(720, newWidth))
    }
  }
  
  /**
   * 停止拖动
   */
  const stopResize = () => {
    isResizing = false
    resizeDirection = null
    
    document.removeEventListener('mousemove', handleResize)
    document.removeEventListener('mouseup', stopResize)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }
  
  return {
    leftWidth,
    rightWidth,
    startResize,
    applyResponsiveWidth
  }
}
