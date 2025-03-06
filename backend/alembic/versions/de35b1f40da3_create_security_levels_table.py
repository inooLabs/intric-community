# Copyright (c) 2025 Sundsvalls Kommun
#
# Licensed under the MIT License.

"""create_security_levels_table

Revision ID: de35b1f40da3
Revises: bd5e20893670
Create Date: 2025-01-09 13:14:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision = "de35b1f40da3"
down_revision = "bd5e20893670"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create security levels table
    op.create_table(
        "security_levels",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.UUID(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "deleted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "tenant_id"),
    )

    # Add security level reference to spaces table
    op.add_column(
        "spaces",
        sa.Column(
            "security_level_id",
            sa.UUID(),
            sa.ForeignKey("security_levels.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Add security level reference to completion model settings table
    op.add_column(
        "completion_model_settings",
        sa.Column(
            "security_level_id",
            sa.UUID(),
            sa.ForeignKey("security_levels.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Add security level reference to embedding model settings table
    op.add_column(
        "embedding_model_settings",
        sa.Column(
            "security_level_id",
            sa.UUID(),
            sa.ForeignKey("security_levels.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # Remove security level references
    op.drop_column("embedding_model_settings", "security_level_id")
    op.drop_column("completion_model_settings", "security_level_id")
    op.drop_column("spaces", "security_level_id")

    # Drop security levels table
    op.drop_table("security_levels")
