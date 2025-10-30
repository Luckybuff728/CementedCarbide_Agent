/**
 * WebSocket组合式函数
 * 处理实时通信和流式数据接收
 */
import { ref, onUnmounted } from 'vue'

export function useWebSocket() {
  const ws = ref(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  let messageHandler = null
  let reconnectTimer = null

  /**
   * 连接WebSocket
   */
  const connect = (url, onMessage) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      console.log('WebSocket已连接')
      return
    }

    messageHandler = onMessage

    try {
      ws.value = new WebSocket(url)

      ws.value.onopen = () => {
        console.log('WebSocket连接成功')
        isConnected.value = true
        reconnectAttempts.value = 0
        
        if (messageHandler) {
          messageHandler({
            type: 'connected',
            timestamp: new Date().toISOString()
          })
        }
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('收到消息:', data)
          
          if (messageHandler) {
            messageHandler(data)
          }
        } catch (error) {
          console.error('解析消息失败:', error)
        }
      }

      ws.value.onerror = (error) => {
        console.error('WebSocket错误:', error)
        isConnected.value = false
      }

      ws.value.onclose = () => {
        console.log('WebSocket连接关闭')
        isConnected.value = false
        
        // 自动重连
        if (reconnectAttempts.value < maxReconnectAttempts) {
          reconnectAttempts.value++
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 10000)
          console.log(`${delay}ms后尝试重连 (${reconnectAttempts.value}/${maxReconnectAttempts})`)
          
          reconnectTimer = setTimeout(() => {
            connect(url, messageHandler)
          }, delay)
        } else {
          console.error('达到最大重连次数')
          if (messageHandler) {
            messageHandler({
              type: 'error',
              message: '无法连接到服务器，请检查后端是否运行'
            })
          }
        }
      }
    } catch (error) {
      console.error('创建WebSocket连接失败:', error)
      isConnected.value = false
    }
  }

  /**
   * 发送消息
   */
  const send = (data) => {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      console.error('WebSocket未连接')
      return false
    }

    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      ws.value.send(message)
      console.log('发送消息:', data)
      return true
    } catch (error) {
      console.error('发送消息失败:', error)
      return false
    }
  }

  /**
   * 断开连接
   */
  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    if (ws.value) {
      ws.value.close()
      ws.value = null
    }

    isConnected.value = false
    reconnectAttempts.value = 0
  }

  // 组件卸载时自动断开
  onUnmounted(() => {
    disconnect()
  })

  return {
    connect,
    send,
    disconnect,
    isConnected
  }
}
