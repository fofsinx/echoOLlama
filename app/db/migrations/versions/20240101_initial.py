"""initial migration

Revision ID: initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from app.db.models import MessageRole, ResponseStatus

# revision identifiers
revision = 'initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    # Check if enums exist before creating them
    with op.get_context().autocommit_block():
        op.execute('DROP TYPE IF EXISTS message_role CASCADE')
        op.execute('DROP TYPE IF EXISTS response_status CASCADE')

        # Create sessions table with updated defaults and columns
        op.create_table(
            'sessions',
            sa.Column('id', sa.String(), default=lambda: str(uuid.uuid4()), nullable=False),
            sa.Column('object_type', sa.String(), server_default='realtime.session', nullable=True),
            sa.Column('model', sa.String(), server_default='llama3.1', nullable=True),
            sa.Column('modalities', postgresql.JSON(astext_type=sa.Text()), 
                     server_default='["text", "audio"]', nullable=True),
            sa.Column('instructions', sa.String(), server_default='', nullable=True),
            sa.Column('voice', sa.String(), server_default='alloy', nullable=True),
            sa.Column('input_audio_format', sa.String(), server_default='pcm16', nullable=True),
            sa.Column('output_audio_format', sa.String(), server_default='pcm16', nullable=True),
            sa.Column('input_audio_transcription', postgresql.JSON(astext_type=sa.Text()), 
                     server_default='{"model": "whisper-1", "language": "en"}', nullable=True),
            sa.Column('turn_detection', postgresql.JSON(astext_type=sa.Text()), 
                     server_default='''{"type": "server_vad", "threshold": 0.5, 
                                      "prefix_padding_ms": 300, "silence_duration_ms": 500}''',
                     nullable=True),
            sa.Column('tools', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('tool_choice', sa.String(), server_default='auto', nullable=True),
            sa.Column('temperature', sa.Float(), server_default='0.7', nullable=True),
            sa.Column('max_response_output_tokens', sa.String(), server_default='inf', nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), 
                     server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), 
                     server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            if_not_exists=True,
        )

        # Add index for sessions lookup
        op.create_index(
            'idx_sessions_created_at',
            'sessions',
            ['created_at'],
            if_not_exists=True
        )


        # Create conversations table
        op.create_table(
            'conversations',
            sa.Column('id', sa.String(), default=lambda: str(uuid.uuid4()), nullable=False),
            sa.Column('object_type', sa.String(), nullable=True),
            sa.Column('session_id', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
            if_not_exists=True,
        )

        # Create conversation_items table
        op.create_table(
            'conversation_items',
            sa.Column('id', sa.String(), default=lambda: str(uuid.uuid4()), nullable=False),
            sa.Column('conversation_id', sa.String(), nullable=True),
            sa.Column('role', MessageRole.as_pg_enum(), nullable=True),
            sa.Column('content', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('audio_start_ms', sa.Integer(), nullable=True),
            sa.Column('audio_end_ms', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
            if_not_exists=True,
        )

        # Create responses table
        op.create_table(
            'responses',
            sa.Column('id', sa.String(), default=lambda: str(uuid.uuid4()), nullable=False),
            sa.Column('object_type', sa.String(), nullable=True),
            sa.Column('status', ResponseStatus.as_pg_enum(), nullable=True),
            sa.Column('conversation_id', sa.String(), nullable=True),
            sa.Column('total_tokens', sa.Integer(), nullable=True),
            sa.Column('input_tokens', sa.Integer(), nullable=True),
            sa.Column('output_tokens', sa.Integer(), nullable=True),
            sa.Column('input_token_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('output_token_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('status_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            if_not_exists=True,
        )


def downgrade() -> None:
    # Drop tables
    op.drop_table('responses')
    op.drop_table('conversation_items')
    op.drop_table('conversations')
    op.drop_table('sessions')

    # Drop enum types
    op.execute('DROP TYPE response_status')
    op.execute('DROP TYPE rate_limit_type')
    op.execute('DROP TYPE message_role')
