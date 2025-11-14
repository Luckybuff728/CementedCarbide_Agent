/**
 * ResizeObserver composable
 */
import { ref, onBeforeUnmount } from 'vue'

export function useResizeObserver() {
  const resizeObserver = ref(null)

  /**
   * 设置大小监听器
   */
  const setupResizeObserver = (targetElement, renderWindow, onResize) => {
    if (!targetElement || !renderWindow) return

    try {
      const observer = new ResizeObserver(entries => {
        for (const entry of entries) {
          const { width, height } = entry.contentRect

          if (width > 0 && height > 0) {
            // 更新VTK渲染器大小
            renderWindow.getInteractor().getView().setSize(
              Math.floor(width), 
              Math.floor(height)
            )

            // 重新渲染
            renderWindow.render()

            // 执行自定义回调
            if (onResize) {
              onResize(width, height)
            }

            console.log('[VTK时间序列] 尺寸变化:', width, 'x', height)
          }
        }
      })

      observer.observe(targetElement)
      resizeObserver.value = observer

    } catch (err) {
      console.error('[VTK时间序列] 设置大小监听失败:', err)
    }
  }

  /**
   * 清理监听器
   */
  const cleanup = () => {
    if (resizeObserver.value) {
      resizeObserver.value.disconnect()
      resizeObserver.value = null
    }
  }

  // 组件卸载时自动清理
  onBeforeUnmount(() => {
    cleanup()
  })

  return {
    setupResizeObserver,
    cleanup
  }
}
