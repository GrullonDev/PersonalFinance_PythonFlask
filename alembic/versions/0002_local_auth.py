"""Add local auth support (profiles extended, credentials, reset tokens)."""

from __future__ import annotations

from datetime import datetime

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_local_auth"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("nombres", sa.String(length=150), nullable=True))
    op.add_column("profiles", sa.Column("apellidos", sa.String(length=150), nullable=True))
    op.add_column("profiles", sa.Column("fecha_nacimiento", sa.Date(), nullable=True))
    op.add_column("profiles", sa.Column("username", sa.String(length=80), nullable=True))
    op.create_index(op.f("ix_profiles_username"), "profiles", ["username"], unique=True)

    op.create_table(
        "local_credentials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("ultimo_login", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("profile_id", name="uq_local_credentials_profile_id"),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token", name="uq_password_reset_tokens_token"),
    )
    op.create_index(op.f("ix_password_reset_tokens_token"), "password_reset_tokens", ["token"], unique=False)

    # Rellena columnas nuevas con datos existentes
    op.execute("UPDATE profiles SET nombres = nombre_completo WHERE nombres IS NULL")
    op.execute("UPDATE profiles SET apellidos = '' WHERE apellidos IS NULL")


def downgrade() -> None:
    op.drop_index(op.f("ix_password_reset_tokens_token"), table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("local_credentials")
    op.drop_index(op.f("ix_profiles_username"), table_name="profiles")
    op.drop_column("profiles", "username")
    op.drop_column("profiles", "fecha_nacimiento")
    op.drop_column("profiles", "apellidos")
    op.drop_column("profiles", "nombres")
