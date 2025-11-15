# WebSocket Events Reference

Complete guide to real-time events in CoLink.

## Overview

CoLink uses WebSocket connections for real-time features:
- Instant message delivery
- Typing indicators
- Online presence
- Live reactions

**WebSocket Server**: Port 8007

## Connection

### JavaScript/TypeScript

```typescript
import io from 'socket.io-client'

const socket = io('http://localhost:8007', {
  auth: {
    token: 'Bearer eyJhbGciOiJSUzI1...' // Your JWT token
  },
  transports: ['websocket'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
})

// Connection events
socket.on('connect', () => {
  console.log('Connected to WebSocket server')
})

socket.on('disconnect', (reason) => {
  console.log('Disconnected:', reason)
})

socket.on('error', (error) => {
  console.error('WebSocket error:', error)
})
```

### Python

```python
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to WebSocket server')

@sio.event
def disconnect():
    print('Disconnected from WebSocket server')

sio.connect('http://localhost:8007', auth={'token': 'Bearer YOUR_JWT_TOKEN'})
```

## Client Events (Emit)

Events that clients send to the server.

### channel:join

Join a channel to receive its messages.

```javascript
socket.emit('channel:join', {
  channel_id: 'ch_123'
})
```

**Response:**
```javascript
socket.on('channel:joined', (data) => {
  // { channel_id: 'ch_123', success: true }
})
```

### channel:leave

Leave a channel.

```javascript
socket.emit('channel:leave', {
  channel_id: 'ch_123'
})
```

### typing:start

Notify others you're typing.

```javascript
socket.emit('typing:start', {
  channel_id: 'ch_123'
})
```

**Note**: Automatically expires after 5 seconds if not sent again.

### typing:stop

Stop typing indicator.

```javascript
socket.emit('typing:stop', {
  channel_id: 'ch_123'
})
```

### presence:update

Update your presence status.

```javascript
socket.emit('presence:update', {
  status: 'online' // 'online' | 'away' | 'offline'
})
```

## Server Events (Listen)

Events that server sends to clients.

### message:new

New message in a channel.

```javascript
socket.on('message:new', (data) => {
  console.log('New message:', data)
})
```

**Payload:**
```typescript
{
  message_id: string
  channel_id: string
  user_id: string
  user: {
    user_id: string
    display_name: string
    avatar_url: string
  }
  content: string
  message_type: 'text' | 'file' | 'system'
  created_at: string // ISO 8601
  reactions: Array<{
    emoji: string
    user_id: string
  }>
  thread_reply_count: number
  parent_message_id?: string
}
```

**Example:**
```json
{
  "message_id": "msg_789",
  "channel_id": "ch_123",
  "user_id": "usr_456",
  "user": {
    "user_id": "usr_456",
    "display_name": "Alice",
    "avatar_url": "https://..."
  },
  "content": "Hello, team!",
  "message_type": "text",
  "created_at": "2024-01-15T10:30:00Z",
  "reactions": [],
  "thread_reply_count": 0
}
```

### message:updated

Message was edited.

```javascript
socket.on('message:updated', (data) => {
  console.log('Message edited:', data)
})
```

**Payload:**
```typescript
{
  message_id: string
  channel_id: string
  content: string
  is_edited: true
  edited_at: string // ISO 8601
}
```

### message:deleted

Message was deleted.

```javascript
socket.on('message:deleted', (data) => {
  console.log('Message deleted:', data)
})
```

**Payload:**
```typescript
{
  message_id: string
  channel_id: string
  deleted_by: string // user_id
  deleted_at: string // ISO 8601
}
```

### reaction:added

Reaction added to a message.

```javascript
socket.on('reaction:added', (data) => {
  console.log('Reaction added:', data)
})
```

**Payload:**
```typescript
{
  message_id: string
  channel_id: string
  emoji: string
  user_id: string
  user: {
    user_id: string
    display_name: string
  }
  created_at: string
}
```

### reaction:removed

Reaction removed from a message.

```javascript
socket.on('reaction:removed', (data) => {
  console.log('Reaction removed:', data)
})
```

**Payload:**
```typescript
{
  message_id: string
  channel_id: string
  emoji: string
  user_id: string
}
```

### typing:start

User started typing.

```javascript
socket.on('typing:start', (data) => {
  console.log('User typing:', data)
})
```

**Payload:**
```typescript
{
  channel_id: string
  user_id: string
  display_name: string
  avatar_url: string
}
```

**Note**: Display typing indicator in UI. Auto-hide after 5 seconds.

### typing:stop

User stopped typing.

```javascript
socket.on('typing:stop', (data) => {
  console.log('User stopped typing:', data)
})
```

**Payload:**
```typescript
{
  channel_id: string
  user_id: string
}
```

### presence:update

User's online status changed.

```javascript
socket.on('presence:update', (data) => {
  console.log('Presence changed:', data)
})
```

**Payload:**
```typescript
{
  user_id: string
  status: 'online' | 'away' | 'offline'
  last_seen?: string // ISO 8601, only when offline
}
```

### channel:created

New channel created.

```javascript
socket.on('channel:created', (data) => {
  console.log('New channel:', data)
})
```

**Payload:**
```typescript
{
  channel_id: string
  workspace_id: string
  name: string
  description: string
  is_private: boolean
  created_by: string
  created_at: string
}
```

### channel:updated

Channel details updated.

```javascript
socket.on('channel:updated', (data) => {
  console.log('Channel updated:', data)
})
```

### member:joined

User joined a channel.

```javascript
socket.on('member:joined', (data) => {
  console.log('Member joined:', data)
})
```

**Payload:**
```typescript
{
  channel_id: string
  user: {
    user_id: string
    display_name: string
    avatar_url: string
  }
  joined_at: string
}
```

### member:left

User left a channel.

```javascript
socket.on('member:left', (data) => {
  console.log('Member left:', data)
})
```

## Complete Example

### React Hook

```typescript
import { useEffect, useState } from 'react'
import io, { Socket } from 'socket.io-client'

interface Message {
  message_id: string
  channel_id: string
  user_id: string
  content: string
  created_at: string
}

export function useWebSocket(token: string, channelId: string) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [typing, setTyping] = useState<Set<string>>(new Set())

  useEffect(() => {
    const ws = io('http://localhost:8007', {
      auth: { token: `Bearer ${token}` },
      transports: ['websocket']
    })

    ws.on('connect', () => {
      console.log('Connected')
      ws.emit('channel:join', { channel_id: channelId })
    })

    ws.on('message:new', (message: Message) => {
      if (message.channel_id === channelId) {
        setMessages(prev => [...prev, message])
      }
    })

    ws.on('typing:start', (data) => {
      if (data.channel_id === channelId) {
        setTyping(prev => new Set(prev).add(data.user_id))
        // Auto-hide after 5 seconds
        setTimeout(() => {
          setTyping(prev => {
            const next = new Set(prev)
            next.delete(data.user_id)
            return next
          })
        }, 5000)
      }
    })

    ws.on('typing:stop', (data) => {
      setTyping(prev => {
        const next = new Set(prev)
        next.delete(data.user_id)
        return next
      })
    })

    setSocket(ws)

    return () => {
      ws.emit('channel:leave', { channel_id: channelId })
      ws.close()
    }
  }, [token, channelId])

  const sendMessage = (content: string) => {
    // Send via REST API, server will broadcast via WebSocket
    fetch('http://localhost:8002/messages', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ channel_id: channelId, content })
    })
  }

  const startTyping = () => {
    socket?.emit('typing:start', { channel_id: channelId })
  }

  const stopTyping = () => {
    socket?.emit('typing:stop', { channel_id: channelId })
  }

  return {
    messages,
    typing: Array.from(typing),
    sendMessage,
    startTyping,
    stopTyping
  }
}
```

### Usage in Component

```typescript
function ChatRoom({ channelId }: { channelId: string }) {
  const token = useAuthToken()
  const { messages, typing, sendMessage, startTyping, stopTyping } =
    useWebSocket(token, channelId)

  const [input, setInput] = useState('')

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
    startTyping()

    // Stop typing after 3 seconds of no input
    clearTimeout(typingTimeout)
    typingTimeout = setTimeout(stopTyping, 3000)
  }

  const handleSubmit = () => {
    sendMessage(input)
    setInput('')
    stopTyping()
  }

  return (
    <div>
      {messages.map(msg => (
        <div key={msg.message_id}>{msg.content}</div>
      ))}

      {typing.length > 0 && (
        <div>Someone is typing...</div>
      )}

      <input value={input} onChange={handleChange} />
      <button onClick={handleSubmit}>Send</button>
    </div>
  )
}
```

## Error Handling

```javascript
socket.on('error', (error) => {
  if (error.code === 'UNAUTHORIZED') {
    console.error('Invalid token, please re-authenticate')
    // Redirect to login
  } else if (error.code === 'CHANNEL_NOT_FOUND') {
    console.error('Channel does not exist')
  } else {
    console.error('WebSocket error:', error)
  }
})
```

## Best Practices

### 1. Reconnection Strategy

```javascript
const socket = io(url, {
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: 5
})

socket.on('reconnect', (attemptNumber) => {
  console.log('Reconnected after', attemptNumber, 'attempts')
  // Re-join channels
  channels.forEach(ch => {
    socket.emit('channel:join', { channel_id: ch })
  })
})
```

### 2. Typing Indicators

```javascript
let typingTimeout
const handleTyping = () => {
  socket.emit('typing:start', { channel_id })

  clearTimeout(typingTimeout)
  typingTimeout = setTimeout(() => {
    socket.emit('typing:stop', { channel_id })
  }, 3000)
}
```

### 3. Optimistic UI Updates

```javascript
const sendMessage = async (content) => {
  // Optimistically add message to UI
  const tempMessage = {
    message_id: `temp_${Date.now()}`,
    content,
    pending: true
  }
  setMessages(prev => [...prev, tempMessage])

  try {
    // Send via REST API
    const response = await fetch('/messages', {
      method: 'POST',
      body: JSON.stringify({ channel_id, content })
    })
    const message = await response.json()

    // Replace temp message with real one
    setMessages(prev =>
      prev.map(m => m.message_id === tempMessage.message_id ? message : m)
    )
  } catch (error) {
    // Remove failed message
    setMessages(prev => prev.filter(m => m.message_id !== tempMessage.message_id))
  }
}
```

### 4. Memory Leaks Prevention

```javascript
useEffect(() => {
  const socket = io(url)

  const handleMessage = (msg) => { /* ... */ }
  socket.on('message:new', handleMessage)

  return () => {
    socket.off('message:new', handleMessage)
    socket.close()
  }
}, [])
```

## Testing WebSocket Events

### Manual Testing

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket server
wscat -c "ws://localhost:8007" -H "Authorization: Bearer YOUR_TOKEN"

# Send events
> {"event": "channel:join", "data": {"channel_id": "ch_123"}}

# Receive events
< {"event": "message:new", "data": {...}}
```

### Automated Testing

```javascript
import { io } from 'socket.io-client'

describe('WebSocket Events', () => {
  let socket

  beforeEach((done) => {
    socket = io('http://localhost:8007', {
      auth: { token: 'Bearer test_token' }
    })
    socket.on('connect', done)
  })

  afterEach(() => {
    socket.close()
  })

  it('should receive new messages', (done) => {
    socket.emit('channel:join', { channel_id: 'ch_test' })

    socket.on('message:new', (data) => {
      expect(data.channel_id).toBe('ch_test')
      done()
    })

    // Trigger message via API
    fetch('http://localhost:8002/messages', {
      method: 'POST',
      body: JSON.stringify({
        channel_id: 'ch_test',
        content: 'Test message'
      })
    })
  })
})
```

## Troubleshooting

### Connection Issues

```javascript
socket.on('connect_error', (error) => {
  console.error('Connection failed:', error.message)

  if (error.message === 'Authentication error') {
    // Token expired or invalid
    refreshToken()
  }
})
```

### Not Receiving Events

1. Ensure you've joined the channel:
   ```javascript
   socket.emit('channel:join', { channel_id })
   ```

2. Check event listeners are registered:
   ```javascript
   socket.listeners('message:new') // Should return array of listeners
   ```

3. Verify server is broadcasting:
   ```bash
   docker-compose logs gateway-service
   ```

## Performance Considerations

- **Throttle typing events**: Send at most once per second
- **Batch reactions**: Debounce rapid reaction changes
- **Limit message history**: Load recent messages only
- **Unsubscribe from channels**: Leave channels when navigating away
- **Use connection pooling**: Reuse socket connection across components

## Security

- **Always use TLS in production**: `wss://` not `ws://`
- **Validate JWT tokens**: Server validates on connection
- **Rate limiting**: Server enforces event rate limits
- **Channel authorization**: Server checks channel membership

## Additional Resources

- [Socket.io Client API](https://socket.io/docs/v4/client-api/)
- [API Documentation](./API_DOCUMENTATION.md)
- [Development Guide](../DEVELOPMENT.md)
