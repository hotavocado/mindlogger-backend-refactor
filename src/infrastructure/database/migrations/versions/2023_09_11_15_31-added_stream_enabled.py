"""added stream_enabled

Revision ID: 34b60d19140d
Revises: 39d0778295f1
Create Date: 2023-09-11 15:31:30.451729

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "34b60d19140d"
down_revision = "c60599479c20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "applet_histories",
        sa.Column("stream_enabled", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "applets", sa.Column("stream_enabled", sa.Boolean(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("applets", "stream_enabled")
    op.drop_column("applet_histories", "stream_enabled")
    # ### end Alembic commands ###