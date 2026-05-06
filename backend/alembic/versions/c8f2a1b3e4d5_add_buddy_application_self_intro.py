"""add buddy application self_intro

Revision ID: c8f2a1b3e4d5
Revises: b1253cdfaa3d
Create Date: 2026-03-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c8f2a1b3e4d5"
down_revision: Union[str, None] = "b1253cdfaa3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "buddy_applications",
        sa.Column("self_intro", sa.Text(), nullable=True, comment="申请者简介"),
    )


def downgrade() -> None:
    op.drop_column("buddy_applications", "self_intro")
