"""merge multiple heads
Revision ID: 68d47ec6a9ed
Revises: 16ed8ac3ef47, de35b1f40da3
Create Date: 2025-02-18 08:09:37.729509
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '68d47ec6a9ed'
down_revision = ('16ed8ac3ef47', 'de35b1f40da3')
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass