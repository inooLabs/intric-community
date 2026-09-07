# flake8: noqa

"""add_base_url_to_embedding_models
Revision ID: b3e9a1f2c8d5
Revises: 1e58cb567f44
Create Date: 2026-09-06 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "b3e9a1f2c8d5"
down_revision = "1e58cb567f44"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("embedding_models", sa.Column("base_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("embedding_models", "base_url")
