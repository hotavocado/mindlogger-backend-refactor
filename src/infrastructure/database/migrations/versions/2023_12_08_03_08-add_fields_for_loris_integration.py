"""Add fields for LORIS integration

Revision ID: d41da0a122a0
Revises: 63a2a290c7e6
Create Date: 2023-12-08 03:08:10.843102

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d41da0a122a0"
down_revision = "63a2a290c7e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "answers", sa.Column("is_data_share", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "applets",
        sa.Column(
            "integrations", sa.ARRAY(sa.String(length=32)), nullable=True
        ),
    )
    op.add_column(
        "users_workspaces",
        sa.Column(
            "integrations", sa.ARRAY(sa.String(length=32)), nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users_workspaces", "integrations")
    op.drop_column("applets", "integrations")
    op.drop_column("answers", "is_data_share")
    # ### end Alembic commands ###
