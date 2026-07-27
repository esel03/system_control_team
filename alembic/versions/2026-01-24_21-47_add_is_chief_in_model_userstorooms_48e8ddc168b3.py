"""Add is_chief in model UsersToRooms

Revision ID: 48e8ddc168b3
Revises: f26bdc003d45
Create Date: 2026-01-24 18:47:09.646944

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "48e8ddc168b3"
down_revision: str | Sequence[str] | None = "f26bdc003d45"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users_to_rooms",
        sa.Column(
            "is_chief",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
            comment="является ли руководителем комнаты",
        ),
    )
    op.execute("UPDATE users_to_rooms SET is_chief = false WHERE is_chief IS NULL")
    op.alter_column("users_to_rooms", "is_chief", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users_to_rooms", "is_chief")
