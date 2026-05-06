"""chat_sessions.pending_prep_payload for deferred prep agent

Revision ID: e2a3b4c5d6e7
Revises: d1e2f3a4b5c6
Create Date: 2026-03-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e2a3b4c5d6e7"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_sessions",
        sa.Column("pending_prep_payload", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chat_sessions", "pending_prep_payload")
