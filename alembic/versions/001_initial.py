"""Initial database migration with pgvector support.

Revision ID: 001
Revises:
Create Date: 2024-01-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('project_id', sa.String(255), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
    )

    # Create engagements table
    op.create_table(
        'engagements',
        sa.Column('engagement_id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
    )
    op.create_index('idx_engagement_user', 'engagements', ['user_id'])

    # Create session status enum
    op.execute(text("CREATE TYPE session_status AS ENUM ('active', 'paused', 'completed', 'archived')"))

    # Create accelerator type enum
    op.execute(text("CREATE TYPE accelerator_type AS ENUM ('basic', 'advanced', 'enterprise')"))

    # Create conversation_sessions table
    op.create_table(
        'conversation_sessions',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('engagement_id', sa.String(255), sa.ForeignKey('engagements.engagement_id', ondelete='CASCADE'), nullable=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects.project_id', ondelete='CASCADE'), nullable=True),
        sa.Column('accelerator_type', postgresql.ENUM('basic', 'advanced', 'enterprise', name='accelerator_type', create_type=False), default='basic'),
        sa.Column('conversation_metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('last_active_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('status', postgresql.ENUM('active', 'paused', 'completed', 'archived', name='session_status', create_type=False), default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
    )

    # Create partial index for active sessions
    op.execute(text('''
        CREATE INDEX idx_session_user_active
        ON conversation_sessions (user_id, last_active_at)
        WHERE status = 'active'
    '''))

    # Create message role enum
    op.execute(text("CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system')"))

    # Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('message_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversation_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', postgresql.ENUM('user', 'assistant', 'system', name='message_role', create_type=False), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('parent_message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversation_messages.message_id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )

    op.create_index('idx_session_messages_created', 'conversation_messages', ['session_id', 'created_at'])
    op.create_index('idx_message_parent', 'conversation_messages', ['parent_message_id'])

    # Create action type enum
    op.execute(text("CREATE TYPE action_type AS ENUM ('code_execution', 'file_operation', 'web_search', 'api_call', 'data_processing')"))

    # Create action status enum
    op.execute(text("CREATE TYPE action_status AS ENUM ('pending', 'running', 'completed', 'failed')"))

    # Create conversation_actions table
    op.create_table(
        'conversation_actions',
        sa.Column('action_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversation_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversation_messages.message_id', ondelete='SET NULL'), nullable=True),
        sa.Column('action_type', postgresql.ENUM('code_execution', 'file_operation', 'web_search', 'api_call', 'data_processing', name='action_type', create_type=False), nullable=False),
        sa.Column('action_metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('job_id', sa.String(255), nullable=True),
        sa.Column('logging_id', sa.String(255), nullable=True),
        sa.Column('workflow_id', sa.String(255), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', name='action_status', create_type=False), default='pending'),
        sa.Column('result', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )

    op.create_index('idx_action_type', 'conversation_actions', ['action_type'])
    op.create_index('idx_action_status', 'conversation_actions', ['status'])

    # Create memory type enum
    op.execute(text("CREATE TYPE memory_type AS ENUM ('semantic', 'episodic', 'procedural', 'working')"))

    # Create conversation_memory table
    op.create_table(
        'conversation_memory',
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversation_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('memory_type', postgresql.ENUM('semantic', 'episodic', 'procedural', 'working', name='memory_type', create_type=False), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.JSON(), nullable=True),
        sa.Column('memory_metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )

    op.create_index('idx_memory_session', 'conversation_memory', ['session_id'])
    op.create_index('idx_memory_type', 'conversation_memory', ['memory_type'])


def downgrade() -> None:
    op.drop_table('conversation_memory')
    op.drop_table('conversation_actions')
    op.drop_table('conversation_messages')
    op.drop_table('conversation_sessions')
    op.drop_table('engagements')
    op.drop_table('projects')

    op.execute(text('DROP TYPE IF EXISTS memory_type'))
    op.execute(text('DROP TYPE IF EXISTS action_status'))
    op.execute(text('DROP TYPE IF EXISTS action_type'))
    op.execute(text('DROP TYPE IF EXISTS message_role'))
    op.execute(text('DROP TYPE IF EXISTS session_status'))
    op.execute(text('DROP TYPE IF EXISTS accelerator_type'))