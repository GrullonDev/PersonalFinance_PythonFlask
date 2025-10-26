"""Initial schema for personal finance domain."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tipo_movimiento = sa.Enum("ingreso", "gasto", name="tipo_movimiento")
    bind = op.get_bind()
    tipo_movimiento.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=True, unique=True),
        sa.Column("nombre", sa.String(length=255), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("ultimo_acceso", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("firebase_uid", sa.String(length=128), nullable=False, unique=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("nombre_completo", sa.String(length=255), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_profiles_id", "profiles", ["id"], unique=False)

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("monto_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("profile_id", "nombre", "fecha_inicio", "fecha_fin", name="uq_budget_period"),
    )
    op.create_index("ix_budgets_profile_id", "budgets", ["profile_id"], unique=False)

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("tipo", tipo_movimiento, nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("profile_id", "nombre", "tipo", name="uq_category_profile_nombre_tipo"),
    )
    op.create_index("ix_categories_profile_id", "categories", ["profile_id"], unique=False)

    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("monto_objetivo", sa.Numeric(12, 2), nullable=False),
        sa.Column("monto_actual", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("fecha_limite", sa.Date(), nullable=False),
        sa.Column("icono", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_goals_profile_id", "goals", ["profile_id"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("tipo", tipo_movimiento, nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("descripcion", sa.String(length=500), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("es_recurrente", sa.Boolean(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_transactions_profile_fecha", "transactions", ["profile_id", "fecha"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transactions_profile_fecha", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_goals_profile_id", table_name="goals")
    op.drop_table("goals")
    op.drop_index("ix_categories_profile_id", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_budgets_profile_id", table_name="budgets")
    op.drop_table("budgets")
    op.drop_index("ix_profiles_id", table_name="profiles")
    op.drop_table("profiles")
    op.drop_table("users")
    sa.Enum(name="tipo_movimiento").drop(op.get_bind(), checkfirst=True)
