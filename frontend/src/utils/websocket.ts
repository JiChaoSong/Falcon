export interface TaskRuntimeSocketMessage {
  channel: string
  event: string
  task_id: number
  timestamp: string | null
  data: Record<string, unknown>
}

const resolveApiBaseUrl = () => {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL
  if (configuredBaseUrl) {
    return configuredBaseUrl.replace(/\/api\/?$/, '').replace(/\/$/, '')
  }

  return window.location.origin.replace(/\/$/, '')
}

const toWebSocketBaseUrl = (baseUrl: string) => {
  if (baseUrl.startsWith('https://')) {
    return baseUrl.replace('https://', 'wss://')
  }
  if (baseUrl.startsWith('http://')) {
    return baseUrl.replace('http://', 'ws://')
  }
  return `${window.location.protocol === 'https:' ? 'wss://' : 'ws://'}${window.location.host}`
}

class TaskRuntimeSocketManager {
  private socket: WebSocket | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private manualClose = false
  private currentTaskId: number | null = null
  private token = ''
  private readonly wsBaseUrl = toWebSocketBaseUrl(resolveApiBaseUrl())

  private onMessageCallback: ((message: TaskRuntimeSocketMessage) => void) | null = null
  private onConnectionChangeCallback: ((connected: boolean) => void) | null = null
  private onErrorCallback: ((event: Event) => void) | null = null

  connect(taskId: number, token: string) {
    if (!taskId || !token) {
      return
    }

    const targetUrl = `${this.wsBaseUrl}/ws/task/${taskId}?token=${encodeURIComponent(token)}`
    if (this.socket && this.socket.readyState === WebSocket.OPEN && this.currentTaskId === taskId) {
      return
    }

    this.manualClose = false
    this.currentTaskId = taskId
    this.token = token
    this.clearReconnectTimer()
    this.closeSocket()

    this.socket = new WebSocket(targetUrl)
    this.socket.onopen = () => {
      this.startHeartbeat()
      this.onConnectionChangeCallback?.(true)
    }
    this.socket.onmessage = (event: MessageEvent<string>) => {
      try {
        this.onMessageCallback?.(JSON.parse(event.data) as TaskRuntimeSocketMessage)
      } catch (error) {
        console.error('Failed to parse task runtime websocket message:', error)
      }
    }
    this.socket.onerror = (error) => {
      console.error('Task runtime websocket error:', error)
      this.onErrorCallback?.(error)
    }
    this.socket.onclose = () => {
      this.stopHeartbeat()
      this.onConnectionChangeCallback?.(false)
      this.socket = null

      if (!this.manualClose && this.currentTaskId && this.token) {
        this.reconnectTimer = setTimeout(() => {
          this.connect(this.currentTaskId as number, this.token)
        }, 3000)
      }
    }
  }

  disconnect() {
    this.manualClose = true
    this.currentTaskId = null
    this.token = ''
    this.clearReconnectTimer()
    this.closeSocket()
    this.onConnectionChangeCallback?.(false)
  }

  setOnMessage(callback: (message: TaskRuntimeSocketMessage) => void) {
    this.onMessageCallback = callback
  }

  setOnConnectionChange(callback: (connected: boolean) => void) {
    this.onConnectionChangeCallback = callback
  }

  setOnError(callback: (event: Event) => void) {
    this.onErrorCallback = callback
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send('ping')
      }
    }, 20000)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private clearReconnectTimer() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  private closeSocket() {
    this.stopHeartbeat()
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
  }
}

export const taskRuntimeSocket = new TaskRuntimeSocketManager()
