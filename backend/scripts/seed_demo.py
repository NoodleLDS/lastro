"""
Demo seed — populates the database with realistic fictitious data so the app
is immediately testable after `alembic upgrade head`.

Run with:
    uv run python scripts/seed_demo.py
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import bcrypt  # noqa: E402 (installed as backend dep)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlmodel import Session, SQLModel, create_engine, select  # noqa: E402

from lastro.core.config import settings  # noqa: E402
from lastro.models.allocation_target import AllocationTarget  # noqa: E402
from lastro.models.card import Card  # noqa: E402
from lastro.models.category import Category  # noqa: E402
from lastro.models.contribution import Contribution  # noqa: E402
from lastro.models.emergency_reserve import EmergencyReserve  # noqa: E402
from lastro.models.fixed_expense import FixedExpense  # noqa: E402
from lastro.models.income import Income  # noqa: E402
from lastro.models.merchant_rule import MerchantRule  # noqa: E402
from lastro.models.position import AssetType, Position  # noqa: E402
from lastro.models.transaction import (  # noqa: E402
    CategorizedBy,
    Transaction,
    TransactionSource,
    TransactionStatus,
)
from lastro.models.user import User  # noqa: E402

# Strip async driver — seed runs synchronously
db_url = settings.database_url.replace("+aiosqlite", "").replace("sqlite:///./", "sqlite:///")
if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
    db_path = Path(__file__).resolve().parents[1] / "lastro.db"
    db_url = f"sqlite:///{db_path}"
engine = create_engine(db_url)
SQLModel.metadata.create_all(engine)

TODAY = date.today()
THIS_YEAR = TODAY.year
THIS_MONTH = TODAY.month


with Session(engine) as session:
    # ── User ──────────────────────────────────────────────────────────────────
    if not session.exec(select(User)).first():
        hashed = bcrypt.hashpw(b"demo1234", bcrypt.gensalt()).decode()
        session.add(User(username="admin", password_hash=hashed))
        session.commit()
        print("✓ user: admin / demo1234")

    # ── Categories ────────────────────────────────────────────────────────────
    categories = [
        "Alimentação",
        "Transporte",
        "Saúde",
        "Lazer",
        "Assinaturas",
        "Moradia",
        "Educação",
        "Vestuário",
        "Supermercado",
        "Outros",
    ]
    cat_map: dict[str, int] = {}
    for name in categories:
        existing = session.exec(select(Category).where(Category.name == name)).first()
        if existing:
            cat_map[name] = existing.id  # type: ignore[assignment]
        else:
            c = Category(name=name)
            session.add(c)
            session.flush()
            cat_map[name] = c.id  # type: ignore[assignment]
    session.commit()
    print(f"✓ {len(categories)} categories")

    # ── Cards ─────────────────────────────────────────────────────────────────
    cards_data = [
        dict(name="Nubank", color="#820ad1", closing_day=2, due_day=9),
        dict(name="Inter", color="#ff7a00", closing_day=20, due_day=27),
    ]
    card_ids: list[int] = []
    for cd in cards_data:
        existing = session.exec(select(Card).where(Card.name == cd["name"])).first()
        if existing:
            card_ids.append(existing.id)  # type: ignore[assignment]
        else:
            c = Card(**cd)
            session.add(c)
            session.flush()
            card_ids.append(c.id)  # type: ignore[assignment]
    session.commit()
    print(f"✓ {len(card_ids)} cards")

    # ── Merchant rules ────────────────────────────────────────────────────────
    rules = [
        ("ifood", "Alimentação"),
        ("rappi", "Alimentação"),
        ("uber eats", "Alimentação"),
        ("uber", "Transporte"),
        ("99", "Transporte"),
        ("spotify", "Assinaturas"),
        ("netflix", "Assinaturas"),
        ("amazon prime", "Assinaturas"),
        ("farmácia", "Saúde"),
        ("droga", "Saúde"),
        ("médico", "Saúde"),
        ("cinema", "Lazer"),
        ("bar", "Lazer"),
        ("supermercado", "Supermercado"),
        ("mercado", "Supermercado"),
        ("pão de açúcar", "Supermercado"),
    ]
    rule_count = 0
    for pattern, cat_name in rules:
        existing = session.exec(select(MerchantRule).where(MerchantRule.pattern == pattern)).first()
        if not existing:
            session.add(MerchantRule(pattern=pattern, category_id=cat_map[cat_name]))
            rule_count += 1
    session.commit()
    print(f"✓ {rule_count} merchant rules")

    # ── Transactions (last 3 months) ──────────────────────────────────────────
    nu_id, inter_id = card_ids[0], card_ids[1]
    tx_data = [
        # (card_id, days_ago, description, amount_cents, category)
        (nu_id, 2, "iFood - Almoço", 4_290, "Alimentação"),
        (nu_id, 3, "Uber - Trabalho", 1_850, "Transporte"),
        (nu_id, 4, "Spotify", 2_190, "Assinaturas"),
        (nu_id, 5, "Farmácia São João", 3_500, "Saúde"),
        (nu_id, 6, "Supermercado Extra", 28_000, "Supermercado"),
        (nu_id, 8, "Netflix", 5_590, "Assinaturas"),
        (nu_id, 10, "Cinema - Ingresso", 3_500, "Lazer"),
        (nu_id, 12, "Uber Eats - Jantar", 5_800, "Alimentação"),
        (nu_id, 14, "Tablet Samsung 1/6", 90_000, "Educação"),
        (nu_id, 44, "Tablet Samsung 2/6", 90_000, "Educação"),
        (nu_id, 74, "Tablet Samsung 3/6", 90_000, "Educação"),
        (inter_id, 3, "Rappi - Mercado", 9_500, "Supermercado"),
        (inter_id, 7, "Amazon Prime", 1_990, "Assinaturas"),
        (inter_id, 9, "Médico Particular", 25_000, "Saúde"),
        (inter_id, 15, "Supermercado Carrefour", 31_000, "Supermercado"),
        (inter_id, 33, "iFood - Almoço", 3_800, "Alimentação"),
        (inter_id, 35, "Uber", 2_200, "Transporte"),
        (inter_id, 37, "Cinema", 3_500, "Lazer"),
    ]
    tx_count = 0
    for card_id, days_ago, desc, amount_cents, cat_name in tx_data:
        tx_date = TODAY - timedelta(days=days_ago)
        existing = session.exec(
            select(Transaction).where(
                Transaction.date == tx_date,
                Transaction.description == desc,
                Transaction.card_id == card_id,
            )
        ).first()
        if not existing:
            session.add(
                Transaction(
                    date=tx_date,
                    description=desc,
                    amount_cents=amount_cents,
                    card_id=card_id,
                    category_id=cat_map[cat_name],
                    categorized_by=CategorizedBy.RULE,
                    source=TransactionSource.MANUAL,
                    status=TransactionStatus.CONFIRMED,
                )
            )
            tx_count += 1
    session.commit()
    print(f"✓ {tx_count} transactions")

    # ── Positions ─────────────────────────────────────────────────────────────
    positions_data = [
        dict(
            ticker="CPTS11",
            name="Capitânia Securities II",
            asset_type=AssetType.FII,
            target_yield_pct=12.0,
        ),
        dict(ticker="XPML11", name="XP Malls", asset_type=AssetType.FII, target_yield_pct=9.0),
        dict(
            ticker="HGLG11", name="CSHG Logística", asset_type=AssetType.FII, target_yield_pct=9.5
        ),
        dict(ticker="IVVB11", name="iShares S&P 500 (BR)", asset_type=AssetType.ETF),
        dict(
            ticker="BBAS3",
            name="Banco do Brasil",
            asset_type=AssetType.STOCK,
            roe_percentage=18.0,
            price_earnings=5.2,
        ),
        dict(
            ticker="TESOURO IPCA+ 2035",
            name="Tesouro IPCA+ 2035",
            asset_type=AssetType.FIXED_INCOME,
        ),
        dict(ticker="BTC", name="Bitcoin", asset_type=AssetType.CRYPTO),
    ]
    position_ids: dict[str, int] = {}
    for pd_kwargs in positions_data:
        ticker = pd_kwargs["ticker"]
        existing = session.exec(select(Position).where(Position.ticker == ticker)).first()
        if existing:
            position_ids[ticker] = existing.id  # type: ignore[assignment]
        else:
            p = Position(**pd_kwargs)
            session.add(p)
            session.flush()
            position_ids[ticker] = p.id  # type: ignore[assignment]
    session.commit()
    print(f"✓ {len(position_ids)} positions")

    # ── Contributions ─────────────────────────────────────────────────────────
    contributions_data = [
        # (ticker, date, qty, unit_price_cents)
        ("CPTS11", date(THIS_YEAR, 1, 10), 10, 985_0),
        ("CPTS11", date(THIS_YEAR, 2, 10), 10, 990_0),
        ("CPTS11", date(THIS_YEAR, 3, 10), 15, 975_0),
        ("XPML11", date(THIS_YEAR, 1, 12), 5, 1_050_0),
        ("HGLG11", date(THIS_YEAR, 2, 12), 5, 1_620_0),
        ("XPML11", date(THIS_YEAR, 3, 12), 5, 1_030_0),
        ("IVVB11", date(THIS_YEAR, 1, 15), 3, 2_500_0),
        ("IVVB11", date(THIS_YEAR, 2, 15), 3, 2_550_0),
        ("BBAS3", date(THIS_YEAR, 1, 8), 20, 256_0),
        ("BBAS3", date(THIS_YEAR, 2, 8), 20, 249_0),
        ("TESOURO IPCA+ 2035", date(THIS_YEAR, 1, 5), 1, 50_000_0),
        ("BTC", date(THIS_YEAR, 1, 20), 0.002, 520_000_00),
    ]
    contrib_count = 0
    for ticker, contrib_date, qty, unit_price in contributions_data:
        pos_id = position_ids.get(ticker)
        if not pos_id:
            continue
        existing = session.exec(
            select(Contribution).where(
                Contribution.position_id == pos_id,
                Contribution.date == contrib_date,
                Contribution.quantity == qty,
            )
        ).first()
        if not existing:
            session.add(
                Contribution(
                    position_id=pos_id,
                    date=contrib_date,
                    quantity=qty,
                    unit_price_cents=unit_price,
                )
            )
            contrib_count += 1
    session.commit()
    print(f"✓ {contrib_count} contributions")

    # ── Allocation targets (per asset_type, not per ticker) ───────────────────
    alloc_targets = [
        (AssetType.STOCK, 30.0),
        (AssetType.FII, 30.0),
        (AssetType.ETF, 15.0),
        (AssetType.FIXED_INCOME, 5.0),
        (AssetType.CRYPTO, 5.0),
    ]
    for asset_type, pct in alloc_targets:
        existing = session.exec(
            select(AllocationTarget).where(AllocationTarget.asset_type == asset_type)
        ).first()
        if not existing:
            session.add(AllocationTarget(asset_type=asset_type, target_percentage=pct))
    session.commit()
    print(f"✓ {len(alloc_targets)} allocation targets")

    # ── Emergency reserve ─────────────────────────────────────────────────────
    if not session.exec(select(EmergencyReserve)).first():
        session.add(
            EmergencyReserve(
                institution="CDB Nubank",
                balance_cents=1_200_000,
                cdi_percentage=102.0,
            )
        )
        session.commit()
        print("✓ emergency reserve: R$ 12.000")

    # ── Income (last 3 months) ────────────────────────────────────────────────
    if not session.exec(select(Income)).first():
        for i in range(3):
            m = THIS_MONTH - i
            y = THIS_YEAR
            if m <= 0:
                m += 12
                y -= 1
            session.add(Income(description="Salário", amount_cents=650_000, year=y, month=m))
        session.commit()
        print("✓ 3 months of income")

    # ── Fixed expenses (last 3 months) ────────────────────────────────────────
    if not session.exec(select(FixedExpense)).first():
        fixed = [
            ("Aluguel", 150_000),
            ("Internet", 10_000),
            ("Plano de saúde", 45_000),
        ]
        for i in range(3):
            m = THIS_MONTH - i
            y = THIS_YEAR
            if m <= 0:
                m += 12
                y -= 1
            for desc, cents in fixed:
                session.add(
                    FixedExpense(
                        description=desc,
                        amount_cents=cents,
                        year=y,
                        month=m,
                    )
                )
        session.commit()
        print(f"✓ {len(fixed) * 3} fixed expense entries")

print("\nSeed concluído. Acesse o Lastro em http://localhost:5173")
print("Login: admin / demo1234")
