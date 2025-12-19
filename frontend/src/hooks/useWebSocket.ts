import { useEffect, useRef, useState, useCallback } from 'react'

interface WebSocketMessage {
  type: string
  [key: string]: unknown
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

interface UseWebSocketReturn {
  isConnected: boolean
  lastMessage: WebSocketMessage | null
  sendMessage: (message: object) => void
  reconnect: () => void
}

const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
  `ws://${window.location.hostname}:8000`

/**
 * Hook for WebSocket connections with auto-reconnect
 */
export function useWebSocket(
  endpoint: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)

  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    const url = `${WS_BASE_URL}${endpoint}`
    const ws = new WebSocket(url)

    ws.onopen = () => {
      setIsConnected(true)
      reconnectAttemptsRef.current = 0
      onOpen?.()

      // Start ping interval to keep connection alive
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)
    }

    ws.onclose = () => {
      setIsConnected(false)
      onClose?.()

      // Clear ping interval
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current)
      }

      // Attempt reconnect
      if (reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current++
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, reconnectInterval)
      }
    }

    ws.onerror = (error) => {
      onError?.(error)
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage
        setLastMessage(message)
        onMessage?.(message)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    wsRef.current = ws
  }, [endpoint, onMessage, onOpen, onClose, onError, reconnectInterval, maxReconnectAttempts])

  const disconnect = useCallback(() => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    // Clear ping interval
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
    }

    // Reset reconnect attempts to prevent auto-reconnect
    reconnectAttemptsRef.current = maxReconnectAttempts

    // Close connection
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [maxReconnectAttempts])

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, message not sent')
    }
  }, [])

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0
    disconnect()
    setTimeout(connect, 100)
  }, [connect, disconnect])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    isConnected,
    lastMessage,
    sendMessage,
    reconnect,
  }
}

/**
 * Hook for subscribing to analysis updates
 */
export function useAnalysisUpdates(
  conceptId: string | null,
  onProgress?: (stage: string, percent: number, message?: string) => void,
  onComplete?: (result: unknown) => void,
  onError?: (error: string) => void
) {
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'progress':
        onProgress?.(
          message.stage as string,
          message.percent as number,
          message.message as string | undefined
        )
        break
      case 'complete':
        onComplete?.(message.result)
        break
      case 'error':
        onError?.(message.message as string)
        break
    }
  }, [onProgress, onComplete, onError])

  const endpoint = conceptId ? `/ws/analysis/${conceptId}` : '/ws'

  return useWebSocket(endpoint, {
    onMessage: handleMessage,
  })
}

/**
 * Hook for subscribing to job updates
 */
export function useJobUpdates(
  jobId: string | null,
  onProgress?: (stage: string, percent: number, current?: number, total?: number) => void,
  onComplete?: (result: unknown) => void,
  onError?: (error: string) => void
) {
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'progress':
        onProgress?.(
          message.stage as string,
          message.percent as number,
          message.current as number | undefined,
          message.total as number | undefined
        )
        break
      case 'complete':
        onComplete?.(message.result)
        break
      case 'error':
        onError?.(message.message as string)
        break
    }
  }, [onProgress, onComplete, onError])

  const endpoint = jobId ? `/ws/job/${jobId}` : '/ws'

  return useWebSocket(endpoint, {
    onMessage: handleMessage,
  })
}

/**
 * Hook for general notifications
 */
export function useNotifications(
  onNotification?: (type: string, data: unknown) => void
) {
  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'notification') {
      onNotification?.(
        message.notification_type as string,
        message.data
      )
    }
  }, [onNotification])

  return useWebSocket('/ws', {
    onMessage: handleMessage,
  })
}
