"""seed initial cards

Revision ID: d5be9e9e731e
Revises: 4d6fde8d3582
Create Date: 2026-06-24 20:13:47.380527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'd5be9e9e731e'
down_revision: Union[str, Sequence[str], None] = '4d6fde8d3582'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CARD_NAMES = ("Nubank", "PicPay", "Inter", "Santander")


def upgrade() -> None:
    """Upgrade schema."""
    card_table = sa.table(
        "card",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("color", sa.String),
        sa.column("closing_day", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        card_table,
        [
            {"name": "Nubank", "color": "#820ad1", "closing_day": None, "is_active": True},
            {"name": "PicPay", "color": "#21c25e", "closing_day": None, "is_active": True},
            {"name": "Inter", "color": "#ff7a00", "closing_day": None, "is_active": True},
            {"name": "Santander", "color": "#ec0000", "closing_day": None, "is_active": True},
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    placeholders = ", ".join(f"'{name}'" for name in _CARD_NAMES)
    op.execute(f"DELETE FROM card WHERE name IN ({placeholders})")
