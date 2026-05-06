"""chat_sessions.langgraph_thread_id for LangGraph checkpoint thread binding"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g5h6i7j8k9l0"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_sessions",
        sa.Column(
            "langgraph_thread_id",
            sa.String(40),
            nullable=True,
            comment="LangGraph checkpointer thread_id (UUID)",
        ),
    )


def downgrade() -> None:
    op.drop_column("chat_sessions", "langgraph_thread_id")
