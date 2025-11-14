"""Initial CoLink database schema

Revision ID: 001_initial
Revises:
Create Date: 2025-01-14 12:00:00.000000

Creates all tables for CoLink application:
- Users and authentication
- Workspaces
- Channels and memberships
- Direct messages
- Messages, threads, and reactions
- Audit logs
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')  # For full-text search

    # Workspaces table
    op.create_table(
        'workspaces',
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('created_by', sa.String(255), nullable=False),  # Keycloak user ID
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, onupdate=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_workspaces_slug', 'workspaces', ['slug'])

    # Users table (cached from Keycloak)
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(255), primary_key=True),  # Keycloak user ID
        sa.Column('keycloak_id', sa.String(255), nullable=False, unique=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('bio', sa.String(500), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True, server_default='America/New_York'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.workspace_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_users_workspace', 'users', ['workspace_id'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email', 'users', ['email'])

    # User status table
    op.create_table(
        'user_status',
        sa.Column('user_id', sa.String(255), primary_key=True),
        sa.Column('status_text', sa.String(100), nullable=True),
        sa.Column('status_emoji', sa.String(10), nullable=True),
        sa.Column('status_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    )

    # Channels table
    op.create_table(
        'channels',
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(80), nullable=False),
        sa.Column('description', sa.String(250), nullable=True),
        sa.Column('is_private', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_by', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.workspace_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='RESTRICT'),
    )
    op.create_index('idx_channels_workspace', 'channels', ['workspace_id'])
    op.create_index('idx_channels_name', 'channels', ['workspace_id', 'name'])

    # Channel members table
    op.create_table(
        'channel_members',
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='member'),  # owner, admin, member
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('channel_id', 'user_id'),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.channel_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_channel_members_user', 'channel_members', ['user_id'])

    # Direct messages table
    op.create_table(
        'direct_messages',
        sa.Column('dm_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.workspace_id'], ondelete='CASCADE'),
    )

    # DM participants table
    op.create_table(
        'dm_participants',
        sa.Column('dm_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('dm_id', 'user_id'),
        sa.ForeignKeyConstraint(['dm_id'], ['direct_messages.dm_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_dm_participants_user', 'dm_participants', ['user_id'])

    # Messages table
    op.create_table(
        'messages',
        sa.Column('message_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dm_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('mentions', postgresql.ARRAY(sa.String(255)), nullable=True, server_default='{}'),
        sa.Column('attachments', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True, server_default='{}'),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('(channel_id IS NOT NULL AND dm_id IS NULL) OR (channel_id IS NULL AND dm_id IS NOT NULL)', name='check_channel_or_dm'),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.channel_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dm_id'], ['direct_messages.dm_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='RESTRICT'),
    )
    op.create_index('idx_messages_channel', 'messages', ['channel_id', 'created_at'])
    op.create_index('idx_messages_dm', 'messages', ['dm_id', 'created_at'])
    op.create_index('idx_messages_user', 'messages', ['user_id'])

    # Full-text search index on message content
    op.execute("""
        CREATE INDEX idx_messages_content_fts ON messages
        USING gin(to_tsvector('english', content))
    """)

    # Threads table
    op.create_table(
        'threads',
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('parent_message_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('reply_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_reply_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_message_id'], ['messages.message_id'], ondelete='CASCADE'),
    )

    # Thread messages table
    op.create_table(
        'thread_messages',
        sa.Column('thread_message_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.thread_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='RESTRICT'),
    )
    op.create_index('idx_thread_messages_thread', 'thread_messages', ['thread_id', 'created_at'])

    # Reactions table
    op.create_table(
        'reactions',
        sa.Column('reaction_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('thread_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('emoji', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('(message_id IS NOT NULL AND thread_message_id IS NULL) OR (message_id IS NULL AND thread_message_id IS NOT NULL)', name='check_message_or_thread'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.message_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['thread_message_id'], ['thread_messages.thread_message_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('message_id', 'user_id', 'emoji', name='uq_message_reaction'),
        sa.UniqueConstraint('thread_message_id', 'user_id', 'emoji', name='uq_thread_reaction'),
    )
    op.create_index('idx_reactions_message', 'reactions', ['message_id'])
    op.create_index('idx_reactions_thread_message', 'reactions', ['thread_message_id'])

    # Audit log table
    op.create_table(
        'audit_log',
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.workspace_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='RESTRICT'),
    )
    op.create_index('idx_audit_log_workspace', 'audit_log', ['workspace_id', 'created_at'])
    op.create_index('idx_audit_log_user', 'audit_log', ['user_id', 'created_at'])
    op.create_index('idx_audit_log_action', 'audit_log', ['action'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('audit_log')
    op.drop_table('reactions')
    op.drop_table('thread_messages')
    op.drop_table('threads')
    op.drop_table('messages')
    op.drop_table('dm_participants')
    op.drop_table('direct_messages')
    op.drop_table('channel_members')
    op.drop_table('channels')
    op.drop_table('user_status')
    op.drop_table('users')
    op.drop_table('workspaces')

    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
