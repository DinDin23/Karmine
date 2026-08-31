"""Make phone_number optional and add sms_consent

Revision ID: b3d7f4a91c02
Revises: 8f2e1c9a4d3b
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3d7f4a91c02'
down_revision: Union[str, Sequence[str], None] = '8f2e1c9a4d3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "sms_consent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column(
        "users",
        "phone_number",
        existing_type=sa.String(length=20),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Backfill any NULL phone numbers so the column can go back to NOT NULL.
    op.execute(
        "UPDATE users SET phone_number = '+10000000000' || id::text "
        "WHERE phone_number IS NULL"
    )
    op.alter_column(
        "users",
        "phone_number",
        existing_type=sa.String(length=20),
        nullable=False,
    )
    op.drop_column("users", "sms_consent")
