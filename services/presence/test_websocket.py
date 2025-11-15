#!/usr/bin/env python3
"""
WebSocket Test Client for Presence Service

Tests:
- WebSocket connection with JWT auth
- Subscribe/unsubscribe to channels
- Typing indicators
- Heartbeat/ping-pong
- Presence tracking
"""

import asyncio
import json
import sys
from datetime import datetime

import websockets


# Mock JWT token for testing (bypasses signature verification in dev mode)
MOCK_JWT = (
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0."
    "eyJzdWIiOiJ1c2VyLTEyMyIsInByZWZlcnJlZF91c2VybmFtZSI6ImFsaWNlIiwiZW1haWwiOiJhbGljZUBjb2xpbmsuZGV2Iiwicm9sZXMiOlsidXNlciJdLCJpYXQiOjE3MDUyNDAwMDAsImV4cCI6OTk5OTk5OTk5OX0."
    "mock-signature"
)

WS_URL = "ws://localhost:8006/ws"


class PresenceTestClient:
    """WebSocket test client"""

    def __init__(self, username: str = "alice"):
        self.username = username
        self.websocket = None
        self.running = False

    async def connect(self):
        """Connect to WebSocket server"""
        url = f"{WS_URL}?token={MOCK_JWT}"

        print(f"🔌 Connecting to {WS_URL}...")

        try:
            self.websocket = await websockets.connect(url)
            self.running = True
            print(f"✅ Connected as {self.username}")

            # Start message listener
            asyncio.create_task(self.listen_messages())

            # Wait for initial pong
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)

    async def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("👋 Disconnected")

    async def send_message(self, message: dict):
        """Send message to server"""
        if not self.websocket:
            print("❌ Not connected")
            return

        try:
            await self.websocket.send(json.dumps(message))
            print(f"📤 Sent: {message['type']}")
        except Exception as e:
            print(f"❌ Send failed: {e}")

    async def listen_messages(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "pong":
                    timestamp = data.get("timestamp")
                    print(f"💓 Pong received at {timestamp}")

                elif msg_type == "subscribed":
                    channel = data.get("channel_id") or data.get("dm_id")
                    print(f"✅ Subscribed to {channel}")

                elif msg_type == "unsubscribed":
                    channel = data.get("channel_id") or data.get("dm_id")
                    print(f"✅ Unsubscribed from {channel}")

                elif msg_type == "presence":
                    user = data.get("username")
                    status = data.get("status")
                    print(f"👤 Presence: {user} is {status}")

                elif msg_type == "typing":
                    user = data.get("username")
                    channel = data.get("channel_id") or data.get("dm_id")
                    print(f"⌨️  Typing: {user} in {channel}")

                elif msg_type == "message":
                    print(f"💬 Message: {json.dumps(data, indent=2)}")

                elif msg_type == "error":
                    error = data.get("error")
                    code = data.get("code")
                    print(f"❌ Error [{code}]: {error}")

                else:
                    print(f"📨 Received: {json.dumps(data, indent=2)}")

        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed")
            self.running = False
        except Exception as e:
            print(f"❌ Listener error: {e}")
            self.running = False

    async def subscribe(self, channel_id: str):
        """Subscribe to a channel"""
        await self.send_message(
            {"type": "subscribe", "channel_id": channel_id}
        )

    async def unsubscribe(self, channel_id: str):
        """Unsubscribe from a channel"""
        await self.send_message(
            {"type": "unsubscribe", "channel_id": channel_id}
        )

    async def send_typing(self, channel_id: str):
        """Send typing indicator"""
        await self.send_message(
            {"type": "typing", "channel_id": channel_id}
        )

    async def ping(self):
        """Send ping for heartbeat"""
        await self.send_message({"type": "ping"})

    async def run_interactive(self):
        """Run interactive test mode"""
        await self.connect()

        print("\n" + "=" * 60)
        print("WebSocket Test Client - Interactive Mode")
        print("=" * 60)
        print("\nCommands:")
        print("  sub <channel_id>   - Subscribe to channel")
        print("  unsub <channel_id> - Unsubscribe from channel")
        print("  typing <channel_id> - Send typing indicator")
        print("  ping               - Send heartbeat ping")
        print("  quit               - Exit")
        print("=" * 60 + "\n")

        while self.running:
            try:
                # Get user input
                cmd = await asyncio.get_event_loop().run_in_executor(
                    None, input, ">>> "
                )

                parts = cmd.strip().split()
                if not parts:
                    continue

                command = parts[0].lower()

                if command == "quit":
                    break

                elif command == "sub" and len(parts) > 1:
                    await self.subscribe(parts[1])

                elif command == "unsub" and len(parts) > 1:
                    await self.unsubscribe(parts[1])

                elif command == "typing" and len(parts) > 1:
                    await self.send_typing(parts[1])

                elif command == "ping":
                    await self.ping()

                else:
                    print("❌ Unknown command")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        await self.disconnect()

    async def run_automated_test(self):
        """Run automated test sequence"""
        print("\n" + "=" * 60)
        print("WebSocket Test Client - Automated Test")
        print("=" * 60 + "\n")

        await self.connect()

        # Test 1: Subscribe to channel
        print("\n[Test 1] Subscribe to #general")
        await self.subscribe("channel_general")
        await asyncio.sleep(1)

        # Test 2: Send typing indicator
        print("\n[Test 2] Send typing indicator")
        await self.send_typing("channel_general")
        await asyncio.sleep(1)

        # Test 3: Send heartbeat
        print("\n[Test 3] Send heartbeat ping")
        await self.ping()
        await asyncio.sleep(1)

        # Test 4: Subscribe to another channel
        print("\n[Test 4] Subscribe to #random")
        await self.subscribe("channel_random")
        await asyncio.sleep(1)

        # Test 5: Typing in second channel
        print("\n[Test 5] Typing in #random")
        await self.send_typing("channel_random")
        await asyncio.sleep(1)

        # Test 6: Unsubscribe from first channel
        print("\n[Test 6] Unsubscribe from #general")
        await self.unsubscribe("channel_general")
        await asyncio.sleep(1)

        # Test 7: DM subscription
        print("\n[Test 7] Subscribe to DM")
        await self.send_message({"type": "subscribe", "dm_id": "dm_123"})
        await asyncio.sleep(1)

        # Test 8: Multiple pings
        print("\n[Test 8] Multiple heartbeats")
        for i in range(3):
            await self.ping()
            await asyncio.sleep(0.5)

        print("\n✅ All tests completed!")
        await asyncio.sleep(2)

        await self.disconnect()


async def main():
    """Main entry point"""
    client = PresenceTestClient()

    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        await client.run_automated_test()
    else:
        await client.run_interactive()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
