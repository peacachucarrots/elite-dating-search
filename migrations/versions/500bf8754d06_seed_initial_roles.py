"""seed initial roles

Revision ID: 500bf8754d06
Revises: cec617627743
Create Date: 2025-05-24 05:49:37.059648

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '500bf8754d06'
down_revision = 'cec617627743'
branch_labels = None
depends_on = None


def upgrade():
    role_table = sa.table(
        'roles',
        sa.column('name',  sa.String),
        sa.column('level', sa.Integer),
    )

    op.bulk_insert(role_table, [
        {"name": "visitor", "level": 10},
        {"name": "rep",     "level": 20},
        {"name": "admin",   "level": 30},
    ])

def downgrade():
    # Remove the rows on downgrade
    op.execute(
        sa.text("DELETE FROM roles WHERE name IN ('visitor','rep','admin')")
    )