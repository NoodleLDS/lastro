"""seed merchant rules from spreadsheet

Revision ID: a1f3c9d8e6b2
Revises: 7fe01dca9671
Create Date: 2026-06-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a1f3c9d8e6b2'
down_revision: Union[str, Sequence[str], None] = '7fe01dca9671'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (pattern, categoria) extraído de GestorFinanceiro2026 (1).xlsx (abas PICPAY/INTER/SANTANDER),
# descrições com sufixo de parcela (ex.: "Tablet 3/9") normalizadas para o nome base.
_RULES: tuple[tuple[str, str], ...] = (
    ("Almoço", "Alimentação"),
    ("BH", "Alimentação"),
    ("Belo Horizonte Trip", "Lazer"),
    ("Biblia", "Lazer"),
    ("Bicicleta", "Transporte"),
    ("Biotech", "Saúde"),
    ("Boticario", "Casa"),
    ("Cemig", "Luz"),
    ("Churrasco", "Alimentação"),
    ("Claude", "Assinaturas"),
    ("Coca", "Alimentação"),
    ("Comida", "Alimentação"),
    ("Consorcio", "Outros"),
    ("Conveniencia", "Alimentação"),
    ("Elmiro", "Outros"),
    ("Espeto", "Alimentação"),
    ("Estrelinha", "Casa"),
    ("Farmácia", "Saúde"),
    ("Finclass", "Assinaturas"),
    ("Frango", "Alimentação"),
    ("Fritis", "Alimentação"),
    ("Gasolina", "Transporte"),
    ("Globoplay", "Assinaturas"),
    ("Ifood", "Alimentação"),
    ("Juliana", "Outros"),
    ("Juliocesar", "Outros"),
    ("Kabum", "Tecnologia"),
    ("Kanpai", "Alimentação"),
    ("Lab", "Saúde"),
    ("Livro", "Lazer"),
    ("Lounge", "Lazer"),
    ("Manual", "Outros"),
    ("Mercado", "Alimentação"),
    ("Mercearia", "Alimentação"),
    ("Microondas", "Móveis"),
    ("Oficina", "Transporte"),
    ("Panificadora", "Alimentação"),
    ("Papelaria", "Educação"),
    ("Pizza", "Alimentação"),
    ("Pizzaria", "Alimentação"),
    ("Poke", "Alimentação"),
    ("Posto", "Transporte"),
    ("Primo", "Alimentação"),
    ("Roupa", "Lazer"),
    ("Shopee", "Outros"),
    ("Shoppe", "Outros"),
    ("Subway", "Alimentação"),
    ("Tablet", "Tecnologia"),
    ("Uberlandia", "Alimentação"),
    ("Unimed", "Saúde"),
    ("Viagem BH", "Lazer"),
    ("Viviane", "Outros"),
    ("Zebu", "Alimentação"),
)


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()

    category_table = sa.table(
        "category",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
    )
    merchant_rule_table = sa.table(
        "merchantrule",
        sa.column("id", sa.Integer),
        sa.column("pattern", sa.String),
        sa.column("category_id", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )

    category_names = sorted({category for _, category in _RULES})
    existing = connection.execute(
        sa.select(category_table.c.name, category_table.c.id).where(
            category_table.c.name.in_(category_names)
        )
    ).all()
    category_ids = {name: id_ for name, id_ in existing}

    missing = [name for name in category_names if name not in category_ids]
    if missing:
        connection.execute(
            sa.insert(category_table),
            [{"name": name} for name in missing],
        )
        refetched = connection.execute(
            sa.select(category_table.c.name, category_table.c.id).where(
                category_table.c.name.in_(missing)
            )
        ).all()
        category_ids.update(dict(refetched))

    connection.execute(
        sa.insert(merchant_rule_table),
        [
            {
                "pattern": pattern,
                "category_id": category_ids[category],
                "is_active": True,
            }
            for pattern, category in _RULES
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    placeholders = ", ".join(f"'{pattern}'" for pattern, _ in _RULES)
    connection.execute(sa.text(f"DELETE FROM merchantrule WHERE pattern IN ({placeholders})"))
