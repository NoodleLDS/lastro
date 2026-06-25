from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.category import Category
from lastro.models.merchant_rule import MerchantRule
from lastro.services.llm.provider import LLMProvider


async def find_category_by_rule(session: AsyncSession, description: str) -> Category | None:
    """Busca a categoria cuja MerchantRule ativa combina (contains, case-insensitive)
    com a descrição. Se múltiplas regras combinam, a de pattern mais longo (mais
    específica) vence."""
    result = await session.exec(select(MerchantRule).where(MerchantRule.is_active.is_(True)))
    rules = result.all()

    description_lower = description.lower()
    matching = [rule for rule in rules if rule.pattern.lower() in description_lower]
    if not matching:
        return None

    best_match = max(matching, key=lambda rule: len(rule.pattern))
    return await session.get(Category, best_match.category_id)


async def learn_rule(session: AsyncSession, description: str, category_id: int) -> MerchantRule:
    """Cria uma MerchantRule com pattern = descrição inteira, se ainda não existir
    uma regra idêntica (case-insensitive) para a mesma categoria."""
    result = await session.exec(select(MerchantRule).where(MerchantRule.pattern == description))
    existing = result.first()
    if existing is not None:
        return existing

    rule = MerchantRule(pattern=description, category_id=category_id)
    session.add(rule)
    await session.flush()
    return rule


async def categorize_with_llm(
    session: AsyncSession, llm: LLMProvider, description: str
) -> Category | None:
    """Fallback de IA quando nenhuma MerchantRule combina. Pede ao LLM para escolher
    entre as categorias já existentes; se acertar uma, aprende a regra (vira
    MerchantRule) para não precisar de IA na próxima vez que esse merchant aparecer."""
    result = await session.exec(select(Category))
    categories = result.all()
    if not categories:
        return None

    by_name = {category.name: category for category in categories}
    chosen_name = await llm.categorize(description, list(by_name))
    if chosen_name is None:
        return None

    category = by_name[chosen_name]
    await learn_rule(session, description, category.id)
    return category
