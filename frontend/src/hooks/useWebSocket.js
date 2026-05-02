import { useEffect, useRef, useCallback } from 'react'

export function useWebSocket(onMessage) {
  const ws = useRef(null)
  const retryDelay = useRef(1000)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    const url = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/api/ws`
    ws.current = new WebSocket(url)

    ws.current.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        onMessageRef.current(msg)
      } catch {}
    }

    ws.current.onopen = () => {
      retryDelay.current = 1000
    }

    ws.current.onclose = () => {
      setTimeout(() => {
        retryDelay.current = Math.min(retryDelay.current * 2, 30000)
        connect()
      }, retryDelay.current)
    }

    ws.current.onerror = () => {
      ws.current?.close()
    }
  }, [])

  useEffect(() => {
    connect()
    return () => ws.current?.close()
  }, [connect])
}
