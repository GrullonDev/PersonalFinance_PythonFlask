"""Add notification preferences per profile."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_notifications"
down_revision: Union[str, None] = "0002_local_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("marketing_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("profile_id", name="uq_notification_preferences_profile_id"),
    )


def downgrade() -> None:
    op.drop_table("notification_preferences")

