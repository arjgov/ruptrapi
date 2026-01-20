"""Add analysis_run_id and consumer_name to Impact

Revision ID: e44bee4c2afc
Revises: 4e4c902338ad
Create Date: 2026-01-20 23:48:47.504159

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e44bee4c2afc'
down_revision: Union[str, Sequence[str], None] = '4e4c902338ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add analysis_run_id column
    op.add_column('impacts', sa.Column('analysis_run_id', sa.UUID(), nullable=True))
    op.create_foreign_key('impacts_analysis_run_id_fkey', 'impacts', 'analysis_runs', ['analysis_run_id'], ['id'])
    
    # Add consumer_name column
    op.add_column('impacts', sa.Column('consumer_name', sa.String(), nullable=True))
    
    # Backfill existing records (if any) with placeholder data
    op.execute("""
        UPDATE impacts 
        SET analysis_run_id = (
            SELECT ar.id 
            FROM analysis_runs ar
            INNER JOIN api_changes ac ON ac.old_spec_id = ar.old_spec_id AND ac.new_spec_id = ar.new_spec_id
            WHERE ac.id = impacts.api_change_id
            LIMIT 1
        ),
        consumer_name = (
            SELECT c.name 
            FROM consumers c 
            WHERE c.id = impacts.consumer_id
        )
        WHERE analysis_run_id IS NULL OR consumer_name IS NULL
    """)
    
    # Now make columns NOT NULL
    op.alter_column('impacts', 'analysis_run_id', nullable=False)
    op.alter_column('impacts', 'consumer_name', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('impacts_analysis_run_id_fkey', 'impacts', type_='foreignkey')
    op.drop_column('impacts', 'consumer_name')
    op.drop_column('impacts', 'analysis_run_id')
