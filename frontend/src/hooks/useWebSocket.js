import { useState, useEffect, useRef } from 'react'

export function useWebSocket(url) {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const ws = useRef(null)

  useEffect(() => {
    if (!url) return

    // Create WebSocket connection
    ws.current = new WebSocket(url)

    ws.current.onopen = () => {
      setConnected(true)
      console.log('WebSocket connected')
    }

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setLastMessage(data)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }

    ws.current.onclose = () => {
      setConnected(false)
      console.log('WebSocket disconnected')
    }

    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [url])

  const sendMessage = (message) => {
    if (ws.current && connected) {
      ws.current.send(JSON.stringify(message))
    }
  }

  return { connected, lastMessage, sendMessage }
}

