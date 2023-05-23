"""Add user_pins table

Revision ID: 00a67bc1b11d
Revises: 2d9cbd7b0928
Create Date: 2023-05-12 13:41:40.232409

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "00a67bc1b11d"
down_revision = "b8a742bc9b35"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user_pins",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("timezone('utc', now())"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("timezone('utc', now())"),
            nullable=True,
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "pinned_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "role",
            sa.Enum("manager", "respondent", name="user_pin_role"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_user_pins_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pinned_user_id"],
            ["users.id"],
            name=op.f("fk_user_pins_pinned_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_pins_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_pins")),
        sa.UniqueConstraint(
            "user_id",
            "pinned_user_id",
            "owner_id",
            "role",
            name="user_pins_uq",
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user_pins")
    sa.Enum(name='user_pin_role').drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###