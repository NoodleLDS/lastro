from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.category import Category
from lastro.models.merchant_rule import MerchantRule
from lastro.services.ingest.categorization import (
    categorize_with_llm,
    find_category_by_rule,
    learn_rule,
)
from lastro.services.llm.provider import VisionExtractedItem


class _StubLLM:
    def __init__(self, category_name: str | None) -> None:
        self._category_name = category_name

    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]:
        raise NotImplementedError

    async def categorize(self, description: str, category_names: list[str]) -> str | None:
        return self._category_name


async def _create_category(session: AsyncSession, name: str) -> Category:
    category = Category(name=name)
    session.add(category)
    await session.flush()
    return category


async def test_find_category_by_rule_contains_case_insensitive(session: AsyncSession) -> None:
    category = await _create_category(session, "transporte")
    session.add(MerchantRule(pattern="uber", category_id=category.id))
    await session.flush()

    found = await find_category_by_rule(session, "UBER *TRIP SAO PAULO")

    assert found is not None
    assert found.id == category.id


async def test_find_category_by_rule_sem_match(session: AsyncSession) -> None:
    category = await _create_category(session, "transporte")
    session.add(MerchantRule(pattern="uber", category_id=category.id))
    await session.flush()

    found = await find_category_by_rule(session, "supermercado extra")

    assert found is None


async def test_find_category_by_rule_prioriza_pattern_mais_longo(session: AsyncSession) -> None:
    transporte = await _create_category(session, "transporte")
    combustivel = await _create_category(session, "combustível")
    session.add(MerchantRule(pattern="posto", category_id=transporte.id))
    session.add(MerchantRule(pattern="posto shell", category_id=combustivel.id))
    await session.flush()

    found = await find_category_by_rule(session, "posto shell av paulista")

    assert found is not None
    assert found.id == combustivel.id


async def test_find_category_by_rule_ignora_regra_inativa(session: AsyncSession) -> None:
    category = await _create_category(session, "transporte")
    session.add(MerchantRule(pattern="uber", category_id=category.id, is_active=False))
    await session.flush()

    found = await find_category_by_rule(session, "uber trip")

    assert found is None


async def test_learn_rule_cria_nova_regra(session: AsyncSession) -> None:
    category = await _create_category(session, "transporte")

    rule = await learn_rule(session, "posto shell av paulista", category.id)

    assert rule.pattern == "posto shell av paulista"
    assert rule.category_id == category.id


async def test_learn_rule_e_idempotente(session: AsyncSession) -> None:
    category = await _create_category(session, "transporte")

    first = await learn_rule(session, "posto shell av paulista", category.id)
    second = await learn_rule(session, "posto shell av paulista", category.id)

    assert first.id == second.id


async def test_categorize_with_llm_aprende_regra_quando_llm_acerta_categoria(
    session: AsyncSession,
) -> None:
    category = await _create_category(session, "Alimentação")
    await _create_category(session, "Transporte")
    llm = _StubLLM("Alimentação")

    found = await categorize_with_llm(session, llm, "zebu 22")

    assert found is not None
    assert found.id == category.id

    rule = await find_category_by_rule(session, "zebu 22")
    assert rule is not None
    assert rule.id == category.id


async def test_categorize_with_llm_retorna_none_quando_llm_nao_decide(
    session: AsyncSession,
) -> None:
    await _create_category(session, "Alimentação")
    llm = _StubLLM(None)

    found = await categorize_with_llm(session, llm, "zebu 22")

    assert found is None


async def test_categorize_with_llm_sem_categorias_cadastradas_nao_chama_llm(
    session: AsyncSession,
) -> None:
    llm = _StubLLM("Alimentação")

    found = await categorize_with_llm(session, llm, "zebu 22")

    assert found is None
