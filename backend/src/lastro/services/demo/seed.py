"""Seed demo data into an empty database (async version for use in lifespan)."""

from datetime import date, timedelta

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.allocation_target import AllocationTarget
from lastro.models.card import Card
from lastro.models.category import Category
from lastro.models.contribution import Contribution
from lastro.models.emergency_reserve import EmergencyReserve
from lastro.models.fixed_expense import FixedExpense
from lastro.models.income import Income
from lastro.models.merchant_rule import MerchantRule
from lastro.models.position import AssetType, Position
from lastro.models.transaction import (
    CategorizedBy,
    Transaction,
    TransactionSource,
    TransactionStatus,
)
from lastro.models.user import User
from lastro.services.auth.security import hash_password


async def is_empty(session: AsyncSession) -> bool:
    result = await session.exec(select(Card))
    return result.first() is None


async def run(session: AsyncSession) -> None:
    """Populate DB with realistic fictitious data. Idempotent — skips existing rows."""
    today = date.today()
    year = today.year
    month = today.month

    # ── Categories ────────────────────────────────────────────────────────────
    category_names = [
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
    for name in category_names:
        row = (await session.exec(select(Category).where(Category.name == name))).first()
        if row:
            cat_map[name] = row.id  # type: ignore[assignment]
        else:
            c = Category(name=name)
            session.add(c)
            await session.flush()
            cat_map[name] = c.id  # type: ignore[assignment]
    await session.commit()

    # ── Cards ─────────────────────────────────────────────────────────────────
    cards_data = [
        dict(name="Nubank", color="#820ad1", closing_day=2, due_day=9),
        dict(name="Inter", color="#ff7a00", closing_day=20, due_day=27),
    ]
    card_ids: list[int] = []
    for cd in cards_data:
        row = (await session.exec(select(Card).where(Card.name == cd["name"]))).first()
        if row:
            card_ids.append(row.id)  # type: ignore[assignment]
        else:
            c = Card(**cd)
            session.add(c)
            await session.flush()
            card_ids.append(c.id)  # type: ignore[assignment]
    await session.commit()

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
    for pattern, cat_name in rules:
        exists = (
            await session.exec(select(MerchantRule).where(MerchantRule.pattern == pattern))
        ).first()
        if not exists:
            session.add(MerchantRule(pattern=pattern, category_id=cat_map[cat_name]))
    await session.commit()

    # ── Transactions ──────────────────────────────────────────────────────────
    nu_id, inter_id = card_ids[0], card_ids[1]
    tx_data = [
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
    for card_id, days_ago, desc, amount_cents, cat_name in tx_data:
        tx_date = today - timedelta(days=days_ago)
        exists = (
            await session.exec(
                select(Transaction).where(
                    Transaction.date == tx_date,
                    Transaction.description == desc,
                    Transaction.card_id == card_id,
                )
            )
        ).first()
        if not exists:
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
    await session.commit()

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
        row = (await session.exec(select(Position).where(Position.ticker == ticker))).first()
        if row:
            position_ids[ticker] = row.id  # type: ignore[assignment]
        else:
            p = Position(**pd_kwargs)
            session.add(p)
            await session.flush()
            position_ids[ticker] = p.id  # type: ignore[assignment]
    await session.commit()

    # ── Contributions ─────────────────────────────────────────────────────────
    contributions_data = [
        ("CPTS11", date(year, 1, 10), 10, 9_850),
        ("CPTS11", date(year, 2, 10), 10, 9_900),
        ("CPTS11", date(year, 3, 10), 15, 9_750),
        ("XPML11", date(year, 1, 12), 5, 10_500),
        ("HGLG11", date(year, 2, 12), 5, 16_200),
        ("XPML11", date(year, 3, 12), 5, 10_300),
        ("IVVB11", date(year, 1, 15), 3, 25_000),
        ("IVVB11", date(year, 2, 15), 3, 25_500),
        ("BBAS3", date(year, 1, 8), 20, 2_560),
        ("BBAS3", date(year, 2, 8), 20, 2_490),
        ("TESOURO IPCA+ 2035", date(year, 1, 5), 1, 500_000),
        ("BTC", date(year, 1, 20), 0.002, 52_000_00),
    ]
    for ticker, contrib_date, qty, unit_price in contributions_data:
        pos_id = position_ids.get(ticker)
        if not pos_id:
            continue
        exists = (
            await session.exec(
                select(Contribution).where(
                    Contribution.position_id == pos_id,
                    Contribution.date == contrib_date,
                    Contribution.quantity == qty,
                )
            )
        ).first()
        if not exists:
            session.add(
                Contribution(
                    position_id=pos_id,
                    date=contrib_date,
                    quantity=qty,
                    unit_price_cents=unit_price,
                )
            )
    await session.commit()

    # ── Allocation targets ────────────────────────────────────────────────────
    alloc_targets = [
        (AssetType.STOCK, 30.0),
        (AssetType.FII, 30.0),
        (AssetType.ETF, 15.0),
        (AssetType.FIXED_INCOME, 5.0),
        (AssetType.CRYPTO, 5.0),
    ]
    for asset_type, pct in alloc_targets:
        exists = (
            await session.exec(
                select(AllocationTarget).where(AllocationTarget.asset_type == asset_type)
            )
        ).first()
        if not exists:
            session.add(AllocationTarget(asset_type=asset_type, target_percentage=pct))
    await session.commit()

    # ── Emergency reserve ─────────────────────────────────────────────────────
    if not (await session.exec(select(EmergencyReserve))).first():
        session.add(
            EmergencyReserve(
                institution="CDB Nubank",
                balance_cents=1_200_000,
                cdi_percentage=102.0,
            )
        )
        await session.commit()

    # ── Income (last 3 months) ────────────────────────────────────────────────
    if not (await session.exec(select(Income))).first():
        for i in range(3):
            m = month - i
            y = year
            if m <= 0:
                m += 12
                y -= 1
            session.add(Income(description="Salário", amount_cents=650_000, year=y, month=m))
        await session.commit()

    # ── Fixed expenses (last 3 months) ────────────────────────────────────────
    if not (await session.exec(select(FixedExpense))).first():
        fixed = [
            ("Aluguel", 150_000),
            ("Internet", 10_000),
            ("Plano de saúde", 45_000),
        ]
        for i in range(3):
            m = month - i
            y = year
            if m <= 0:
                m += 12
                y -= 1
            for desc, cents in fixed:
                session.add(FixedExpense(description=desc, amount_cents=cents, year=y, month=m))
        await session.commit()

    # ── Demo user (separate from admin) ──────────────────────────────────────
    demo_user = "demo"
    if not (await session.exec(select(User).where(User.username == demo_user))).first():
        session.add(User(username=demo_user, password_hash=hash_password("demo1234")))
        await session.commit()
