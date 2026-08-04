"""Remove disputed wager status

Revision ID: 1420377628ab
Revises: fa735d66bdcb
Create Date: 2026-08-04 00:12:25.894898

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1420377628ab'
down_revision: Union[str, Sequence[str], None] = 'fa735d66bdcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Postgres can't drop an enum value directly -- swap in a new type instead.
    op.execute("ALTER TYPE wager_status RENAME TO wager_status_old")
    op.execute(
        "CREATE TYPE wager_status AS ENUM "
        "('MATCHED', 'AWAITING_RESULT', 'SETTLED', 'CANCELLED')"
    )
    op.execute(
        "ALTER TABLE wagers ALTER COLUMN status TYPE wager_status "
        "USING status::text::wager_status"
    )
    op.execute("DROP TYPE wager_status_old")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TYPE wager_status RENAME TO wager_status_new")
    op.execute(
        "CREATE TYPE wager_status AS ENUM "
        "('MATCHED', 'AWAITING_RESULT', 'SETTLED', 'DISPUTED', 'CANCELLED')"
    )
    op.execute(
        "ALTER TABLE wagers ALTER COLUMN status TYPE wager_status "
        "USING status::text::wager_status"
    )
    op.execute("DROP TYPE wager_status_new")
