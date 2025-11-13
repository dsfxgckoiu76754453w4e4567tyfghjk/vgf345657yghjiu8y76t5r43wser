"""
WebSocket endpoint for real-time chat with typing indicators and live updates.

Provides:
- Bidirectional communication
- Typing indicators
- Real-time workflow progress
- Connection management
"""

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.temporal_client import get_temporal_client
from app.db.base import get_db
from app.workflows.chat_workflow import ChatWorkflow, ChatWorkflowInput

router = APIRouter()
logger = get_logger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a websocket."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info("websocket_connected", user_id=user_id)
    
    def disconnect(self, user_id: str):
        """Disconnect a websocket."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info("websocket_disconnected", user_id=user_id)
    
    async def send_message(self, user_id: str, message: dict[str, Any]):
        """Send message to specific user."""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
    
    async def broadcast(self, message: dict[str, Any]):
        """Broadcast message to all connected users."""
        for websocket in self.active_connections.values():
            await websocket.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    user_id: str = Query(...),
):
    """
    WebSocket endpoint for real-time chat.
    
    Message types:
    - **typing**: User is typing
    - **message**: Send chat message
    - **workflow_progress**: Workflow step updates
    - **response**: Chat response from server
    
    Example client code:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/chat/conv-id?user_id=user-id');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'response') {
            console.log('Response:', data.content);
        }
    };
    
    ws.send(JSON.stringify({
        type: 'message',
        content: 'What is Salat?'
    }));
    ```
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            logger.info(
                "websocket_message_received",
                user_id=user_id,
                conversation_id=conversation_id,
                type=message_type,
            )
            
            # Handle typing indicator
            if message_type == "typing":
                await websocket.send_json({
                    "type": "typing_ack",
                    "user_id": user_id,
                })
            
            # Handle chat message
            elif message_type == "message":
                content = data.get("content")
                
                if not content:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Message content required",
                    })
                    continue
                
                # Send acknowledgment
                await websocket.send_json({
                    "type": "message_received",
                    "status": "processing",
                })
                
                # Process with Temporal if enabled
                if settings.temporal_enabled:
                    try:
                        temporal_client = get_temporal_client()
                        
                        # Create workflow
                        workflow_input = ChatWorkflowInput(
                            user_id=user_id,
                            conversation_id=conversation_id,
                            message=content,
                            enable_caching=True,
                        )
                        
                        workflow_id = f"chat-ws-{user_id}-{conversation_id}"
                        handle = await temporal_client.start_workflow(
                            ChatWorkflow.run,
                            workflow_input,
                            id=workflow_id,
                            task_queue=settings.temporal_task_queue,
                        )
                        
                        # Send progress updates
                        await websocket.send_json({
                            "type": "workflow_started",
                            "workflow_id": workflow_id,
                        })
                        
                        # TODO: Stream workflow progress (requires Temporal async iterator)
                        # For now, wait for result
                        result = await handle.result()
                        
                        # Send response
                        await websocket.send_json({
                            "type": "response",
                            "content": result.response,
                            "intent": result.intent,
                            "sources": result.sources,
                            "tokens_used": result.tokens_used,
                            "from_cache": result.from_cache,
                        })
                        
                    except Exception as e:
                        logger.error("websocket_workflow_error", error=str(e))
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Processing failed: {str(e)}",
                        })
                else:
                    # Fallback to sync processing (simplified)
                    await websocket.send_json({
                        "type": "error",
                        "message": "Temporal not enabled. Use HTTP endpoint instead.",
                    })
            
            # Unknown message type
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                })
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(
            "websocket_client_disconnected",
            user_id=user_id,
            conversation_id=conversation_id,
        )
    except Exception as e:
        logger.error(
            "websocket_error",
            user_id=user_id,
            error=str(e),
        )
        manager.disconnect(user_id)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "active_connections": len(manager.active_connections),
        "connected_users": list(manager.active_connections.keys()),
    }
