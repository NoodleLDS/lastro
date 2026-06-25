"""seed real portfolio positions

Revision ID: 1b2efd06ac8f
Revises: dc1cdf23f373
Create Date: 2026-06-24 23:38:13.512503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1b2efd06ac8f'
down_revision: Union[str, Sequence[str], None] = 'dc1cdf23f373'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_POSITIONS = [
    {"ticker": "BBAS3", "name": "Banco do Brasil", "asset_type": "STOCK", "quantity": 311},
    {"ticker": "BBDC4", "name": "Bradesco", "asset_type": "STOCK", "quantity": 41},
    {"ticker": "CMIG4", "name": "Cemig", "asset_type": "STOCK", "quantity": 121},
    {"ticker": "PETR4", "name": "Petrobras", "asset_type": "STOCK", "quantity": 22},
    {"ticker": "IVVB11", "name": "iShares S&P 500", "asset_type": "ETF", "quantity": 9},
    {"ticker": "BTCI11", "name": "BTG Pactual Crédito Imobiliário", "asset_type": "FII", "quantity": 5},
    {"ticker": "CPTS11", "name": "Capitania Securities II", "asset_type": "FII", "quantity": 601},
    {"ticker": "HGLG11", "name": "CSHG Logística", "asset_type": "FII", "quantity": 9},
    {"ticker": "PSEC11", "name": "Patria Securities", "asset_type": "FII", "quantity": 2},
    {"ticker": "XPML11", "name": "XP Malls", "asset_type": "FII", "quantity": 33},
    {
        "ticker": "TESOURO_IPCA_2035",
        "name": "Tesouro IPCA+ com Juros Semestrais 2035",
        "asset_type": "FIXED_INCOME",
        "quantity": 0.16,
    },
]

_RESERVE_INSTITUTION = "PicPay"


def upgrade() -> None:
    """Upgrade schema."""
    position_table = sa.table(
        "position",
        sa.column("id", sa.Integer),
        sa.column("ticker", sa.String),
        sa.column("name", sa.String),
        sa.column("asset_type", sa.String),
        sa.column("quantity", sa.Float),
        sa.column("is_active", sa.Boolean),
        sa.column("last_price_cents", sa.Integer),
        sa.column("last_price_fetched_at", sa.DateTime),
    )
    op.bulk_insert(
        position_table,
        [
            {
                "ticker": p["ticker"],
                "name": p["name"],
                "asset_type": p["asset_type"],
                "quantity": p["quantity"],
                "is_active": True,
                "last_price_cents": None,
                "last_price_fetched_at": None,
            }
            for p in _POSITIONS
        ],
    )

    reserve_table = sa.table(
        "emergencyreserve",
        sa.column("id", sa.Integer),
        sa.column("institution", sa.String),
        sa.column("balance_cents", sa.Integer),
        sa.column("cdi_percentage", sa.Float),
    )
    op.bulk_insert(
        reserve_table,
        [{"institution": _RESERVE_INSTITUTION, "balance_cents": 1_200_000, "cdi_percentage": 102.0}],
    )


def downgrade() -> None:
    """Downgrade schema."""
    tickers = ", ".join(f"'{p['ticker']}'" for p in _POSITIONS)
    op.execute(f"DELETE FROM position WHERE ticker IN ({tickers})")
    op.execute(f"DELETE FROM emergencyreserve WHERE institution = '{_RESERVE_INSTITUTION}'")
