"""
Presence Service - WebSocket Gateway

Provides real-time WebSocket connections for:
- Presence tracking (online, away, offline)
- Typing indicators
- Real-time message broadcasting
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import jwt
from redis.asyncio import Redis
import redis.asyncio as aioredis

from app.models import (
    MessageType,
    PresenceStatus,
    WSMessage,
    SubscribeMessage,
    UnsubscribeMessage,
    TypingMessage,
    PingMessage,
    SubscribedMessage,
    UnsubscribedMessage,
    MessageBroadcast,
    PresenceBroadcast,
    TypingBroadcast,
    PongMessage,
    ErrorMessage,
    UserPresence,
    ConnectionInfo,
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KEYCLOAK_URL = "http://keycloak:8080"
KEYCLOAK_REALM = "colink"
REDIS_URL = "redis://:colink_dev_password@redis:6379/0"

# TTLs
PRESENCE_TTL = 300  # 5 minutes
TYPING_TTL = 5  # 5 seconds
HEARTBEAT_INTERVAL = 30  # 30 seconds

# Global state
redis_client: Optional[Redis] = None
connection_manager: Optional["ConnectionManager"] = None


class ConnectionManager:
    """
    Manages WebSocket connections, subscriptions, and broadcasting
    """

    def __init__(self, redis: Redis):
        self.redis = redis
        # connection_id -> ConnectionInfo
        self.active_connections: Dict[str, ConnectionInfo] = {}
        # connection_id -> WebSocket
        self.websockets: Dict[str, WebSocket] = {}
        # room_id -> set of connection_ids
        self.room_subscriptions: Dict[str, Set[str]] = {}
        # Redis pub/sub
        self.pubsub = None
        self.pubsub_task = None

    async def connect(
        self, websocket: WebSocket, user_id: str, username: str
    ) -> str:
        """
        Accept WebSocket connection and register user
        """
        await websocket.accept()

        connection_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Store connection info
        conn_info = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            username=username,
            connected_at=now,
            last_heartbeat=now,
            subscriptions=[],
        )

        self.active_connections[connection_id] = conn_info
        self.websockets[connection_id] = websocket

        # Update presence in Redis
        await self.update_presence(user_id, username, "online", connection_id)

        # Broadcast presence update
        await self.broadcast_presence(user_id, username, "online")

        logger.info(
            f"User {username} ({user_id}) connected with connection {connection_id}"
        )

        return connection_id

    async def disconnect(self, connection_id: str):
        """
        Disconnect WebSocket and cleanup
        """
        if connection_id not in self.active_connections:
            return

        conn_info = self.active_connections[connection_id]

        # Unsubscribe from all rooms
        for room_id in conn_info.subscriptions[:]:
            await self.unsubscribe(connection_id, room_id)

        # Update presence to offline
        await self.update_presence(
            conn_info.user_id, conn_info.username, "offline", connection_id
        )

        # Broadcast offline status
        await self.broadcast_presence(
            conn_info.user_id, conn_info.username, "offline"
        )

        # Remove connection
        del self.active_connections[connection_id]
        del self.websockets[connection_id]

        logger.info(
            f"User {conn_info.username} ({conn_info.user_id}) disconnected: {connection_id}"
        )

    async def subscribe(self, connection_id: str, room_id: str):
        """
        Subscribe connection to a room (channel or DM)
        """
        if connection_id not in self.active_connections:
            return

        conn_info = self.active_connections[connection_id]

        # Add to room subscriptions
        if room_id not in self.room_subscriptions:
            self.room_subscriptions[room_id] = set()

        self.room_subscriptions[room_id].add(connection_id)
        conn_info.subscriptions.append(room_id)

        logger.info(f"Connection {connection_id} subscribed to room {room_id}")

    async def unsubscribe(self, connection_id: str, room_id: str):
        """
        Unsubscribe connection from a room
        """
        if connection_id not in self.active_connections:
            return

        conn_info = self.active_connections[connection_id]

        # Remove from room subscriptions
        if room_id in self.room_subscriptions:
            self.room_subscriptions[room_id].discard(connection_id)

            if not self.room_subscriptions[room_id]:
                del self.room_subscriptions[room_id]

        if room_id in conn_info.subscriptions:
            conn_info.subscriptions.remove(room_id)

        logger.info(f"Connection {connection_id} unsubscribed from room {room_id}")

    async def send_personal_message(self, connection_id: str, message: dict):
        """
        Send message to a specific connection
        """
        if connection_id not in self.websockets:
            return

        try:
            websocket = self.websockets[connection_id]
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            await self.disconnect(connection_id)

    async def broadcast_to_room(self, room_id: str, message: dict, exclude: Optional[str] = None):
        """
        Broadcast message to all connections in a room
        """
        if room_id not in self.room_subscriptions:
            return

        subscribers = self.room_subscriptions[room_id].copy()

        for connection_id in subscribers:
            if exclude and connection_id == exclude:
                continue

            await self.send_personal_message(connection_id, message)

    async def update_presence(
        self, user_id: str, username: str, status: PresenceStatus, connection_id: str
    ):
        """
        Update user presence in Redis with TTL
        """
        presence_key = f"presence:{user_id}"

        presence = UserPresence(
            user_id=user_id,
            username=username,
            status=status,
            connection_id=connection_id,
            last_seen=datetime.utcnow(),
        )

        # Store in Redis with TTL
        await self.redis.setex(
            presence_key,
            PRESENCE_TTL,
            presence.model_dump_json(),
        )

    async def broadcast_presence(
        self, user_id: str, username: str, status: PresenceStatus
    ):
        """
        Broadcast presence update to all connections
        """
        message = PresenceBroadcast(
            user_id=user_id,
            username=username,
            status=status,
            timestamp=datetime.utcnow(),
        )

        # Publish to Redis for cross-instance broadcasting
        await self.redis.publish(
            "presence:updates",
            message.model_dump_json(),
        )

    async def update_typing(
        self, user_id: str, username: str, room_id: str
    ):
        """
        Update typing indicator with short TTL
        """
        typing_key = f"typing:{room_id}:{user_id}"

        # Store with 5-second TTL
        await self.redis.setex(typing_key, TYPING_TTL, username)

        # Broadcast typing indicator
        message = TypingBroadcast(
            channel_id=room_id if room_id.startswith("channel_") else None,
            dm_id=room_id if room_id.startswith("dm_") else None,
            user_id=user_id,
            username=username,
        )

        await self.broadcast_to_room(room_id, message.model_dump())

    async def update_heartbeat(self, connection_id: str):
        """
        Update last heartbeat timestamp
        """
        if connection_id in self.active_connections:
            self.active_connections[connection_id].last_heartbeat = datetime.utcnow()

            # Also update presence TTL
            conn_info = self.active_connections[connection_id]
            await self.update_presence(
                conn_info.user_id,
                conn_info.username,
                "online",
                connection_id,
            )

    async def start_pubsub_listener(self):
        """
        Start Redis pub/sub listener for cross-instance messages
        """
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(
            "presence:updates",
            "message:broadcast",
        )

        logger.info("Started Redis pub/sub listener")

        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    channel = message["channel"]
                    data = json.loads(message["data"])

                    # Broadcast to local connections
                    if channel == "presence:updates":
                        # Broadcast to all connections
                        for connection_id in list(self.websockets.keys()):
                            await self.send_personal_message(connection_id, data)

                    elif channel == "message:broadcast":
                        # Broadcast to specific room
                        room_id = data.get("room_id")
                        if room_id:
                            await self.broadcast_to_room(room_id, data)

                except Exception as e:
                    logger.error(f"Error processing pub/sub message: {e}")


async def verify_websocket_token(token: str) -> tuple[str, str]:
    """
    Verify JWT token and extract user info

    Returns:
        Tuple of (user_id, username)
    """
    try:
        # For development, we'll do basic JWT decode
        # In production, verify against Keycloak public key
        payload = jwt.decode(
            token,
            options={"verify_signature": False},  # TODO: Verify in production
        )

        user_id = payload.get("sub")
        username = payload.get("preferred_username")

        if not user_id or not username:
            raise ValueError("Invalid token payload")

        return user_id, username

    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    global redis_client, connection_manager

    # Startup
    logger.info("Starting Presence Service...")

    # Initialize Redis
    redis_client = await aioredis.from_url(
        REDIS_URL,
        decode_responses=True,
        encoding="utf-8",
    )
    await redis_client.ping()
    logger.info("Redis connected")

    # Initialize connection manager
    connection_manager = ConnectionManager(redis_client)

    # Start pub/sub listener
    asyncio.create_task(connection_manager.start_pubsub_listener())

    yield

    # Shutdown
    logger.info("Shutting down Presence Service...")

    if connection_manager and connection_manager.pubsub:
        await connection_manager.pubsub.unsubscribe()
        await connection_manager.pubsub.close()

    if redis_client:
        await redis_client.close()


# FastAPI app
app = FastAPI(
    title="CoLink Presence Service",
    description="WebSocket gateway for real-time presence and messaging",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "presence",
        "active_connections": len(connection_manager.active_connections) if connection_manager else 0,
    }


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
):
    """
    WebSocket endpoint for real-time communication

    Authentication: JWT token via query parameter
    """
    connection_id = None

    try:
        # Verify authentication
        user_id, username = await verify_websocket_token(token)

        # Connect user
        connection_id = await connection_manager.connect(websocket, user_id, username)

        # Send initial pong to confirm connection
        await connection_manager.send_personal_message(
            connection_id,
            PongMessage(timestamp=datetime.utcnow()).model_dump(),
        )

        # Start heartbeat checker
        async def heartbeat_checker():
            while connection_id in connection_manager.active_connections:
                await asyncio.sleep(HEARTBEAT_INTERVAL)

                if connection_id not in connection_manager.active_connections:
                    break

                conn_info = connection_manager.active_connections[connection_id]
                time_since_heartbeat = (
                    datetime.utcnow() - conn_info.last_heartbeat
                ).total_seconds()

                # Disconnect if no heartbeat for 2x interval
                if time_since_heartbeat > HEARTBEAT_INTERVAL * 2:
                    logger.warning(
                        f"No heartbeat from {connection_id}, disconnecting"
                    )
                    await websocket.close(code=1008, reason="Heartbeat timeout")
                    break

        heartbeat_task = asyncio.create_task(heartbeat_checker())

        # Message handling loop
        while True:
            try:
                data = await websocket.receive_json()
                message = WSMessage(**data)

                # Handle different message types
                if message.type == "subscribe":
                    subscribe_msg = SubscribeMessage(**data)
                    room_id = subscribe_msg.channel_id or subscribe_msg.dm_id

                    if room_id:
                        await connection_manager.subscribe(connection_id, room_id)
                        await connection_manager.send_personal_message(
                            connection_id,
                            SubscribedMessage(
                                channel_id=subscribe_msg.channel_id,
                                dm_id=subscribe_msg.dm_id,
                            ).model_dump(),
                        )

                elif message.type == "unsubscribe":
                    unsubscribe_msg = UnsubscribeMessage(**data)
                    room_id = unsubscribe_msg.channel_id or unsubscribe_msg.dm_id

                    if room_id:
                        await connection_manager.unsubscribe(connection_id, room_id)
                        await connection_manager.send_personal_message(
                            connection_id,
                            UnsubscribedMessage(
                                channel_id=unsubscribe_msg.channel_id,
                                dm_id=unsubscribe_msg.dm_id,
                            ).model_dump(),
                        )

                elif message.type == "typing":
                    typing_msg = TypingMessage(**data)
                    room_id = typing_msg.channel_id or typing_msg.dm_id

                    if room_id:
                        await connection_manager.update_typing(
                            user_id, username, room_id
                        )

                elif message.type == "ping":
                    await connection_manager.update_heartbeat(connection_id)
                    await connection_manager.send_personal_message(
                        connection_id,
                        PongMessage(timestamp=datetime.utcnow()).model_dump(),
                    )

                else:
                    await connection_manager.send_personal_message(
                        connection_id,
                        ErrorMessage(
                            error=f"Unknown message type: {message.type}",
                            code=400,
                        ).model_dump(),
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await connection_manager.send_personal_message(
                    connection_id,
                    ErrorMessage(error=str(e), code=500).model_dump(),
                )

    except HTTPException as e:
        logger.error(f"Authentication failed: {e.detail}")
        await websocket.close(code=1008, reason=e.detail)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")

    finally:
        # Cleanup
        if connection_id:
            if 'heartbeat_task' in locals():
                heartbeat_task.cancel()
            await connection_manager.disconnect(connection_id)


@app.get("/presence/{user_id}")
async def get_user_presence(user_id: str):
    """
    Get user presence status

    Returns presence information if user is online/away, otherwise offline
    """
    presence_key = f"presence:{user_id}"

    presence_data = await redis_client.get(presence_key)

    if not presence_data:
        return {
            "user_id": user_id,
            "status": "offline",
            "last_seen": None,
        }

    presence = UserPresence.model_validate_json(presence_data)

    return {
        "user_id": presence.user_id,
        "username": presence.username,
        "status": presence.status,
        "last_seen": presence.last_seen,
    }


@app.get("/presence")
async def get_all_presence():
    """
    Get presence for all users (paginated via Redis scan)
    """
    users_presence = []

    # Scan for all presence keys
    async for key in redis_client.scan_iter(match="presence:*", count=100):
        presence_data = await redis_client.get(key)
        if presence_data:
            try:
                presence = UserPresence.model_validate_json(presence_data)
                users_presence.append(
                    {
                        "user_id": presence.user_id,
                        "username": presence.username,
                        "status": presence.status,
                        "last_seen": presence.last_seen,
                    }
                )
            except Exception as e:
                logger.error(f"Error parsing presence for {key}: {e}")

    return {"users": users_presence, "count": len(users_presence)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info",
    )
