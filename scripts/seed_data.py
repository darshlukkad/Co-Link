#!/usr/bin/env python3
"""
Seed CoLink database with sample data for development/testing

This script creates:
- 1 workspace
- 5 test users
- 3 channels (#general, #random, #engineering)
- 1 DM session
- 50 messages across channels
- Thread replies
- Emoji reactions
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import List

import psycopg2
from psycopg2.extras import execute_values

# Database connection settings
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://colink:colink_dev_password@localhost:5432/colink'
)

# Sample data
WORKSPACE_NAME = "CoLink Demo"
WORKSPACE_SLUG = "colink-demo"

SAMPLE_USERS = [
    {
        'keycloak_id': 'user-001-keycloak-id',
        'username': 'alice',
        'email': 'alice@colink.demo',
        'display_name': 'Alice Johnson',
        'bio': 'Product Manager',
        'timezone': 'America/New_York',
    },
    {
        'keycloak_id': 'user-002-keycloak-id',
        'username': 'bob',
        'email': 'bob@colink.demo',
        'display_name': 'Bob Smith',
        'bio': 'Software Engineer',
        'timezone': 'America/Los_Angeles',
    },
    {
        'keycloak_id': 'user-003-keycloak-id',
        'username': 'charlie',
        'email': 'charlie@colink.demo',
        'display_name': 'Charlie Brown',
        'bio': 'DevOps Engineer',
        'timezone': 'Europe/London',
    },
    {
        'keycloak_id': 'user-004-keycloak-id',
        'username': 'diana',
        'email': 'diana@colink.demo',
        'display_name': 'Diana Prince',
        'bio': 'UX Designer',
        'timezone': 'America/Chicago',
    },
    {
        'keycloak_id': 'user-005-keycloak-id',
        'username': 'eve',
        'email': 'eve@colink.demo',
        'display_name': 'Eve Anderson',
        'bio': 'Engineering Manager',
        'timezone': 'Asia/Tokyo',
    },
]

SAMPLE_CHANNELS = [
    {
        'name': 'general',
        'description': 'General team discussions',
        'is_private': False,
    },
    {
        'name': 'random',
        'description': 'Random off-topic conversations',
        'is_private': False,
    },
    {
        'name': 'engineering',
        'description': 'Engineering team channel',
        'is_private': True,
    },
]

SAMPLE_MESSAGES = [
    "Hey team! Welcome to CoLink 👋",
    "This is amazing! Really loving the real-time features.",
    "Has anyone seen the new design mockups?",
    "Let's schedule a standup for tomorrow at 10am",
    "Great work on the latest release everyone! 🎉",
    "I'm working on the authentication service",
    "Can someone review my PR?",
    "Coffee break anyone? ☕",
    "The new WebSocket implementation is working great",
    "Don't forget about the all-hands meeting today",
    "I pushed a fix for that bug we discussed",
    "Thanks for the help with debugging!",
    "Looking forward to the demo tomorrow",
    "Happy Friday everyone! 🎊",
    "Who's free for a pair programming session?",
    "The staging environment is ready for testing",
    "Great point in the last meeting",
    "I'll take a look at that issue",
    "Documentation updated in the wiki",
    "Anyone tried the new search feature?",
]


class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def seed_database():
    """Seed the database with sample data"""
    print("\n" + "=" * 70)
    print("CoLink Database Seeding Script")
    print("=" * 70 + "\n")

    try:
        # Connect to database
        print_info("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        print_success("Connected to database")

        # Create workspace
        print_info("Creating workspace...")
        workspace_id = str(uuid.uuid4())
        first_user_id = f"user-{SAMPLE_USERS[0]['keycloak_id']}"

        cursor.execute("""
            INSERT INTO workspaces (workspace_id, name, slug, created_by)
            VALUES (%s, %s, %s, %s)
            RETURNING workspace_id
        """, (workspace_id, WORKSPACE_NAME, WORKSPACE_SLUG, first_user_id))

        workspace_id = cursor.fetchone()[0]
        print_success(f"Created workspace: {WORKSPACE_NAME} ({workspace_id})")

        # Create users
        print_info(f"Creating {len(SAMPLE_USERS)} users...")
        user_ids = []

        for user_data in SAMPLE_USERS:
            user_id = f"user-{user_data['keycloak_id']}"
            cursor.execute("""
                INSERT INTO users (
                    user_id, keycloak_id, workspace_id, username,
                    email, display_name, bio, timezone
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                user_data['keycloak_id'],
                workspace_id,
                user_data['username'],
                user_data['email'],
                user_data['display_name'],
                user_data['bio'],
                user_data['timezone'],
            ))
            user_ids.append(user_id)

        print_success(f"Created {len(user_ids)} users")

        # Set status for a few users
        print_info("Setting user statuses...")
        cursor.execute("""
            INSERT INTO user_status (user_id, status_text, status_emoji, status_expiry)
            VALUES (%s, %s, %s, %s)
        """, (user_ids[0], "In a meeting", "📅", datetime.utcnow() + timedelta(hours=1)))

        cursor.execute("""
            INSERT INTO user_status (user_id, status_text, status_emoji)
            VALUES (%s, %s, %s)
        """, (user_ids[1], "Coding", "💻"))

        print_success("Set statuses for 2 users")

        # Create channels
        print_info(f"Creating {len(SAMPLE_CHANNELS)} channels...")
        channel_ids = []

        for channel_data in SAMPLE_CHANNELS:
            channel_id = uuid.uuid4()
            cursor.execute("""
                INSERT INTO channels (channel_id, workspace_id, name, description, is_private, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING channel_id
            """, (
                channel_id,
                workspace_id,
                channel_data['name'],
                channel_data['description'],
                channel_data['is_private'],
                user_ids[0],  # Alice creates all channels
            ))
            channel_ids.append(cursor.fetchone()[0])

        print_success(f"Created {len(channel_ids)} channels")

        # Add all users to all channels
        print_info("Adding channel members...")
        member_data = []
        for channel_id in channel_ids:
            for user_id in user_ids:
                role = 'owner' if user_id == user_ids[0] else 'member'
                member_data.append((channel_id, user_id, role))

        execute_values(cursor, """
            INSERT INTO channel_members (channel_id, user_id, role)
            VALUES %s
        """, member_data)

        print_success(f"Added {len(member_data)} channel memberships")

        # Create DM session between Alice and Bob
        print_info("Creating DM session...")
        dm_id = uuid.uuid4()
        cursor.execute("""
            INSERT INTO direct_messages (dm_id, workspace_id)
            VALUES (%s, %s)
            RETURNING dm_id
        """, (dm_id, workspace_id))
        dm_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO dm_participants (dm_id, user_id)
            VALUES (%s, %s), (%s, %s)
        """, (dm_id, user_ids[0], dm_id, user_ids[1]))

        print_success("Created DM session between Alice and Bob")

        # Create messages in channels
        print_info(f"Creating {len(SAMPLE_MESSAGES) * 2} messages...")
        message_ids = []
        base_time = datetime.utcnow() - timedelta(days=7)

        # Messages in #general
        for i, content in enumerate(SAMPLE_MESSAGES):
            message_id = uuid.uuid4()
            user_id = user_ids[i % len(user_ids)]
            created_at = base_time + timedelta(hours=i * 2)

            cursor.execute("""
                INSERT INTO messages (message_id, channel_id, user_id, content, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING message_id
            """, (message_id, channel_ids[0], user_id, content, created_at))
            message_ids.append(cursor.fetchone()[0])

        # Messages in #random
        for i, content in enumerate(SAMPLE_MESSAGES):
            message_id = uuid.uuid4()
            user_id = user_ids[(i + 1) % len(user_ids)]
            created_at = base_time + timedelta(hours=i * 2, minutes=30)

            cursor.execute("""
                INSERT INTO messages (message_id, channel_id, user_id, content, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (message_id, channel_ids[1], user_id, content, created_at))
            message_ids.append(message_id)

        # DM messages
        for i in range(5):
            message_id = uuid.uuid4()
            user_id = user_ids[i % 2]  # Alternate between Alice and Bob
            content = f"DM message {i + 1}"
            created_at = base_time + timedelta(hours=i * 3)

            cursor.execute("""
                INSERT INTO messages (message_id, dm_id, user_id, content, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (message_id, dm_id, user_id, content, created_at))
            message_ids.append(message_id)

        print_success(f"Created {len(message_ids)} messages")

        # Create thread on first message
        print_info("Creating thread replies...")
        first_message_id = message_ids[0]

        cursor.execute("""
            INSERT INTO threads (parent_message_id)
            VALUES (%s)
            RETURNING thread_id
        """, (first_message_id,))
        thread_id = cursor.fetchone()[0]

        # Add thread replies
        thread_replies = [
            "Great point!",
            "I agree with this",
            "Thanks for sharing",
        ]

        for i, content in enumerate(thread_replies):
            user_id = user_ids[(i + 1) % len(user_ids)]
            cursor.execute("""
                INSERT INTO thread_messages (thread_id, user_id, content)
                VALUES (%s, %s, %s)
            """, (thread_id, user_id, content))

        # Update thread reply count
        cursor.execute("""
            UPDATE threads SET reply_count = %s, last_reply_at = CURRENT_TIMESTAMP
            WHERE thread_id = %s
        """, (len(thread_replies), thread_id))

        print_success(f"Created thread with {len(thread_replies)} replies")

        # Add reactions to messages
        print_info("Adding reactions...")
        reaction_emojis = ["👍", "❤️", "😂", "🎉", "👏"]
        reaction_count = 0

        for i, message_id in enumerate(message_ids[:10]):  # React to first 10 messages
            for j in range((i % 3) + 1):  # 1-3 reactions per message
                user_id = user_ids[j % len(user_ids)]
                emoji = reaction_emojis[j % len(reaction_emojis)]

                try:
                    cursor.execute("""
                        INSERT INTO reactions (message_id, user_id, emoji)
                        VALUES (%s, %s, %s)
                    """, (message_id, user_id, emoji))
                    reaction_count += 1
                except psycopg2.IntegrityError:
                    # Skip duplicate reactions
                    pass

        print_success(f"Added {reaction_count} reactions")

        # Create audit log entries
        print_info("Creating audit log entries...")
        audit_actions = [
            ('user_created', 'user', user_ids[0]),
            ('channel_created', 'channel', str(channel_ids[0])),
            ('message_sent', 'message', str(message_ids[0])),
        ]

        for action, resource_type, resource_id in audit_actions:
            cursor.execute("""
                INSERT INTO audit_log (workspace_id, user_id, action, resource_type, resource_id, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (workspace_id, user_ids[0], action, resource_type, resource_id, {}))

        print_success(f"Created {len(audit_actions)} audit log entries")

        # Commit transaction
        conn.commit()
        print_success("All data committed successfully")

        # Print summary
        print("\n" + "=" * 70)
        print_success("Database seeding completed successfully!")
        print("=" * 70)
        print(f"\nWorkspace: {WORKSPACE_NAME}")
        print(f"  ID: {workspace_id}")
        print(f"\nUsers: {len(user_ids)}")
        for i, user_data in enumerate(SAMPLE_USERS):
            print(f"  - {user_data['display_name']} (@{user_data['username']})")
        print(f"\nChannels: {len(channel_ids)}")
        for i, channel_data in enumerate(SAMPLE_CHANNELS):
            print(f"  - #{channel_data['name']}")
        print(f"\nMessages: {len(message_ids)}")
        print(f"Thread Replies: {len(thread_replies)}")
        print(f"Reactions: {reaction_count}")
        print(f"DM Sessions: 1")
        print("\n" + "=" * 70)
        print("\nYou can now query the database:")
        print(f"  psql {DATABASE_URL}")
        print("\nOr test the APIs with seeded data!")
        print("=" * 70 + "\n")

    except psycopg2.Error as e:
        print_error(f"Database error: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    seed_database()
