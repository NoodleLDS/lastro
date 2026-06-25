"""add categorized_by to transaction

Revision ID: 69b35846310d
Revises: a1f3c9d8e6b2
Create Date: 2026-06-25 10:42:29.113227

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '69b35846310d'
down_revision: Union[str, Sequence[str], None] = 'a1f3c9d8e6b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'transaction',
        sa.Column(
            'categorized_by',
            sa.Enum('RULE', 'LLM', 'MANUAL', 'NONE', name='categorizedby'),
            nullable=False,
            server_default='NONE',
        ),
    )

    connection = op.get_bind()
    transaction_table = sa.table(
        'transaction',
        sa.column('category_id', sa.Integer),
        sa.column('categorized_by', sa.String),
    )
    connection.execute(
        transaction_table.update()
        .where(transaction_table.c.category_id.is_not(None))
        .values(categorized_by='MANUAL')
    )

    with op.batch_alter_table('transaction') as batch_op:
        batch_op.alter_column('categorized_by', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transaction', 'categorized_by')
