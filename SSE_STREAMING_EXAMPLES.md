# SSE Streaming Implementation Examples

Complete guide for implementing Server-Sent Events (SSE) streaming with WisQu Islamic Chatbot API.

---

## What is SSE Streaming?

**Server-Sent Events (SSE)** enables real-time token-by-token streaming from the server to client, providing:
- **Real-time responses**: See AI-generated text appear word-by-word
- **Better UX**: No waiting for complete response
- **Reduced latency**: Start displaying content immediately
- **Standard protocol**: Built into browsers, no WebSocket complexity

---

## API Configuration

### Endpoint
```
POST /api/v1/chat/
```

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: text/event-stream
```

### Request Body
```json
{
  "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "message": "Explain the concept of Tawhid",
  "stream": true
}
```

### Response Format (SSE)
```
data: {"type": "content", "content": "Tawhid"}

data: {"type": "content", "content": " is"}

data: {"type": "content", "content": " the"}

data: {"type": "metadata", "message_id": "...", "usage": {...}}
```

---

## JavaScript / TypeScript

### Using EventSource (Browser)

```javascript
// Create SSE connection
const eventSource = new EventSource('/api/v1/chat/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    conversation_id: conversationId,
    message: userMessage,
    stream: true
  })
});

// Handle incoming messages
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'content':
      // Append token to UI
      appendToken(data.content);
      break;

    case 'metadata':
      // Stream completed
      console.log('Message ID:', data.message_id);
      console.log('Usage:', data.usage);
      eventSource.close();
      break;

    case 'error':
      // Handle error
      console.error('Error:', data.error);
      eventSource.close();
      break;
  }
};

// Handle errors
eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
  eventSource.close();
};
```

### Using Fetch API (Modern Browsers)

```javascript
async function streamChat(message) {
  const response = await fetch('/api/v1/chat/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message: message,
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const jsonStr = line.substring(6);
        const data = JSON.parse(jsonStr);

        if (data.type === 'content') {
          appendToken(data.content);
        } else if (data.type === 'metadata') {
          console.log('Completed:', data);
        }
      }
    }
  }
}
```

### React Example

```tsx
import { useState, useEffect } from 'react';

function ChatComponent() {
  const [response, setResponse] = useState('');
  const [streaming, setStreaming] = useState(false);

  const sendMessage = async (message: string) => {
    setResponse('');
    setStreaming(true);

    const response = await fetch('/api/v1/chat/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message: message,
        stream: true
      })
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        setStreaming(false);
        break;
      }

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.substring(6));

          if (data.type === 'content') {
            setResponse(prev => prev + data.content);
          }
        }
      }
    }
  };

  return (
    <div>
      <div className="chat-response">
        {response}
        {streaming && <span className="cursor">▊</span>}
      </div>
    </div>
  );
}
```

---

## Python

### Using httpx (Async)

```python
import httpx
import json

async def stream_chat(message: str):
    url = "http://localhost:8000/api/v1/chat/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "conversation_id": conversation_id,
        "message": message,
        "stream": True,
    }

    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    json_str = line[6:]  # Remove "data: " prefix
                    data = json.loads(json_str)

                    if data["type"] == "content":
                        print(data["content"], end="", flush=True)
                    elif data["type"] == "metadata":
                        print("\n\nMetadata:", data)
                    elif data["type"] == "error":
                        print("\nError:", data["error"])
```

### Using requests (Synchronous)

```python
import requests
import json

def stream_chat(message: str):
    url = "http://localhost:8000/api/v1/chat/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "conversation_id": conversation_id,
        "message": message,
        "stream": True,
    }

    response = requests.post(url, json=payload, headers=headers, stream=True)

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith("data: "):
                json_str = line[6:]
                data = json.loads(json_str)

                if data["type"] == "content":
                    print(data["content"], end="", flush=True)
                elif data["type"] == "metadata":
                    print("\n\nMessage ID:", data["message_id"])
                    print("Usage:", data["usage"])
```

---

## Node.js / Express

### Using fetch (Node 18+)

```javascript
const fetch = require('node-fetch');

async function streamChat(message) {
  const response = await fetch('http://localhost:8000/api/v1/chat/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message: message,
      stream: true
    })
  });

  for await (const chunk of response.body) {
    const lines = chunk.toString().split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));

        if (data.type === 'content') {
          process.stdout.write(data.content);
        } else if (data.type === 'metadata') {
          console.log('\n\nMetadata:', data);
        }
      }
    }
  }
}
```

### Using axios

```javascript
const axios = require('axios');

async function streamChat(message) {
  const response = await axios.post(
    'http://localhost:8000/api/v1/chat/',
    {
      conversation_id: conversationId,
      message: message,
      stream: true
    },
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      responseType: 'stream'
    }
  );

  response.data.on('data', (chunk) => {
    const lines = chunk.toString().split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));

        if (data.type === 'content') {
          process.stdout.write(data.content);
        } else if (data.type === 'metadata') {
          console.log('\n\nCompleted:', data);
        }
      }
    }
  });
}
```

---

## cURL (Testing)

```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "message": "Explain Tawhid",
    "stream": true
  }' \
  --no-buffer
```

---

## Apidog / Postman

### Apidog

1. **Create Request:** `POST /api/v1/chat/`
2. **Set Headers:**
   - `Authorization: Bearer <token>`
   - `Accept: text/event-stream`
3. **Request Body:**
   ```json
   {
     "conversation_id": "...",
     "message": "Test streaming",
     "stream": true
   }
   ```
4. **Enable SSE Mode:** Settings → Enable "Server-Sent Events"
5. **Send Request:** Watch token-by-token streaming

### Postman

1. Create POST request
2. Set headers as above
3. In request body, set `"stream": true`
4. Click "Send"
5. View streaming in "Response" tab (Postman auto-detects SSE)

---

## Error Handling

### Client-Side

```javascript
eventSource.onerror = (error) => {
  console.error('SSE Connection Error:', error);

  // Reconnection logic
  if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
    setTimeout(() => {
      reconnectAttempts++;
      createSSEConnection();
    }, RECONNECT_DELAY);
  } else {
    alert('Failed to connect to chat service');
  }
};
```

### Handling Network Issues

```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

try {
  const response = await fetch('/api/v1/chat/', {
    method: 'POST',
    signal: controller.signal,
    // ... rest of config
  });
} catch (error) {
  if (error.name === 'AbortError') {
    console.error('Request timeout');
  } else {
    console.error('Network error:', error);
  }
} finally {
  clearTimeout(timeoutId);
}
```

---

## Performance Tips

1. **Buffering:** Buffer tokens before rendering to reduce DOM operations
   ```javascript
   let buffer = '';
   const BUFFER_SIZE = 10;

   if (data.type === 'content') {
     buffer += data.content;
     if (buffer.length >= BUFFER_SIZE) {
       appendToDOM(buffer);
       buffer = '';
     }
   }
   ```

2. **Connection Reuse:** Keep connection open for multiple messages when possible

3. **Graceful Degradation:** Fall back to non-streaming if SSE fails
   ```javascript
   try {
     await streamChat(message);
   } catch (error) {
     console.warn('Streaming failed, using non-streaming');
     await sendChatMessage(message, { stream: false });
   }
   ```

4. **Close Connections:** Always close SSE when done
   ```javascript
   useEffect(() => {
     return () => {
       if (eventSource) {
         eventSource.close();
       }
     };
   }, []);
   ```

---

## SSE vs WebSocket

| Feature | SSE | WebSocket |
|---------|-----|-----------|
| **Direction** | Server → Client only | Bidirectional |
| **Protocol** | HTTP | WS/WSS |
| **Browser Support** | All modern browsers | All modern browsers |
| **Reconnection** | Automatic | Manual |
| **Use Case** | Real-time updates, streaming | Real-time chat, gaming |
| **Complexity** | Simple | More complex |

**For AI chat streaming, SSE is perfect!**

---

## Troubleshooting

### Issue: No streaming, getting complete response

**Solution:** Ensure `"stream": true` in request body and `Accept: text/event-stream` header

### Issue: CORS errors

**Solution:** Backend should include:
```python
headers={
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Access-Control-Allow-Origin": "*",  # Or specific origin
}
```

### Issue: Nginx buffering responses

**Solution:** Add to nginx config:
```nginx
proxy_buffering off;
proxy_cache off;
proxy_set_header Connection '';
proxy_http_version 1.1;
chunked_transfer_encoding off;
```

**Or** in response headers:
```
X-Accel-Buffering: no
```

---

**Documentation Version:** 1.0.0
**Last Updated:** 2025-01-13
