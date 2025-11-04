/**
 * WebSocket通信组合式函数
 */
import { ref } from 'vue'

export function useWebSocket() {
  const ws = ref(null)
  const isConnected = ref(false)
  const messageHandler = ref(null)
  
  /**
   * 连接WebSocket服务器
   * @param {string} url - WebSocket URL
   * @param {function} onMessage - 消息处理回调函数
   */
  const connect = (url, onMessage) => {
    if (ws.value) {
      ws.value.close()
    }
    
    messageHandler.value = onMessage
    ws.value = new WebSocket(url)
    
    ws.value.onopen = () => {
      console.log('[WebSocket] 连接成功')
      isConnected.value = true
    }
    
    ws.value.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        console.log('[WebSocket] 收到消息:', message.type)
        
        if (messageHandler.value) {
          messageHandler.value(message)
        }
      } catch (error) {
        console.error('[WebSocket] 解析消息失败:', error)
      }
    }
    
    ws.value.onerror = (error) => {
      console.error('[WebSocket] 连接错误:', error)
      isConnected.value = false
    }
    
    ws.value.onclose = () => {
      console.log('[WebSocket] 连接关闭')
      isConnected.value = false
    }
  }
  
  /**
   * 发送消息
   * @param {object} data - 要发送的数据
   */
  const send = (data) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
      console.log('[WebSocket] 发送消息:', data.type)
    } else {
      console.error('[WebSocket] 连接未建立，无法发送消息')
    }
  }
  
  /**
   * 断开连接
   */
  const disconnect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
      isConnected.value = false
    }
  }
  
  return {
    connect,
    send,
    disconnect,
    isConnected
  }
}
