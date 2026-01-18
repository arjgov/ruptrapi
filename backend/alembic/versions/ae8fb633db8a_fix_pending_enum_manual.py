"""Fix_PENDING_enum_manual

Revision ID: ae8fb633db8a
Revises: 42e77648d8f5
Create Date: 2026-01-18 20:23:16.380590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae8fb633db8a'
down_revision: Union[str, Sequence[str], None] = '42e77648d8f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Explicitly add value to Postgres Enum
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE analysisstatus ADD VALUE IF NOT EXISTS 'PENDING'")


def downgrade() -> None:
    pass
