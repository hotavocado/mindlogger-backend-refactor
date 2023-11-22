"""Add nickname encrypted field in invitation

Revision ID: 93087521e7ee
Revises: a7faad5855cc
Create Date: 2023-11-16 16:26:19.400694

"""
import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.encrypted.encrypted_type import StringEncryptedType

from apps.shared.encryption import get_key

# revision identifiers, used by Alembic.
revision = "93087521e7ee"
down_revision = "a7faad5855cc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###

    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT id, meta FROM invitations WHERE role='respondent' and meta is NOT NULL"
        )
    )
    op.add_column(
        "invitations",
        sa.Column(
            "nickname",
            StringEncryptedType(sa.Unicode, get_key),
            nullable=True,
        ),
    )
    for row in result:
        pk, meta = row
        nickname = meta.get("nickname")
        if nickname and nickname != "":
            encrypted_field = StringEncryptedType(
                sa.Unicode, get_key
            ).process_bind_param(nickname, dialect=conn.dialect)
            meta.pop("nickname")
            conn.execute(
                sa.text(
                    f"""
                        UPDATE invitations
                        SET nickname = :encrypted_field, meta= :meta
                        WHERE id = :pk
                    """
                ),
                {
                    "encrypted_field": encrypted_field,
                    "meta": json.dumps(meta),
                    "pk": pk,
                },
            )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT id, nickname, meta FROM invitations  WHERE role='respondent'"
        )
    )
    op.drop_column("invitations", "nickname")
    for row in result:
        pk, nickname, meta = row
        if nickname is not None:
            decrypted_field = StringEncryptedType(
                sa.Unicode, get_key
            ).process_result_value(nickname, dialect=conn.dialect)
            meta["nickname"] = decrypted_field
            conn.execute(
                sa.text(
                    f"""
                        UPDATE invitations
                        SET meta = :decrypted_field
                        WHERE id = :pk
                    """
                ),
                {"decrypted_field": json.dumps(meta), "pk": pk},
            )
    # ### end Alembic commands ###