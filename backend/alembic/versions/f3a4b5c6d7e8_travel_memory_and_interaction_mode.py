"""users.travel_memory + chat_sessions.interaction_mode"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, None] = "e2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("travel_memory", sa.Text(), nullable=True, comment="JSON: persistent travel prefs & feedback"),
    )
    op.add_column(
        "chat_sessions",
        sa.Column(
            "interaction_mode",
            sa.String(16),
            nullable=True,
            comment="verbose | quiet",
        ),
    )


def downgrade() -> None:
    op.drop_column("chat_sessions", "interaction_mode")
    op.drop_column("users", "travel_memory")
