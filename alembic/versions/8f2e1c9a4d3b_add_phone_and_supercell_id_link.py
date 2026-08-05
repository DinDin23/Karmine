"""Add phone_number and supercell_id_link to users

Revision ID: 8f2e1c9a4d3b
Revises: 37eb85bc44b2
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f2e1c9a4d3b'
down_revision: Union[str, Sequence[str], None] = '37eb85bc44b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("phone_number", sa.String(length=20), nullable=True))
    op.add_column(
        "users", sa.Column("supercell_id_link", sa.String(length=255), nullable=True)
    )

    # Backfill existing rows with placeholders so the columns can become NOT NULL.
    op.execute(
        "UPDATE users SET phone_number = '+10000000000' || id::text, "
        "supercell_id_link = 'https://link.clashroyale.com/?supercell_id&p=UNSET-' || id::text "
        "WHERE phone_number IS NULL"
    )

    op.alter_column("users", "phone_number", nullable=False)
    op.alter_column("users", "supercell_id_link", nullable=False)
    op.create_index(
        op.f("ix_users_phone_number"), "users", ["phone_number"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_users_phone_number"), table_name="users")
    op.drop_column("users", "supercell_id_link")
    op.drop_column("users", "phone_number")
