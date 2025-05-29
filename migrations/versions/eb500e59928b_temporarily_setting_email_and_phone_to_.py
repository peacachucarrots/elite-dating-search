"""temporarily setting email and phone to not unique

Revision ID: eb500e59928b
Revises: 94b0268bbd6a
Create Date: 2025-05-28 11:06:12.578658

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb500e59928b'
down_revision = '94b0268bbd6a'
branch_labels = None
depends_on = None


def upgrade():
    # ---- users table changes ------------------------------------
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_phone", type_="unique")
        batch_op.drop_index("ix_users_email")
        batch_op.create_index(batch_op.f("ix_users_email"), ["email"], unique=False)

    # ---- chat_sessions table: new column ------------------------
    op.add_column(
        "chat_sessions",
        sa.Column("assigned_at", sa.DateTime(), nullable=True)
    )


def downgrade():
    # ---- chat_sessions rollback ---------------------------------
    op.drop_column("chat_sessions", "assigned_at")

    # ---- users table rollback -----------------------------------
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_email"))
        batch_op.create_index("ix_users_email", ["email"], unique=True)
        batch_op.create_unique_constraint("uq_users_phone", ["phone"])
