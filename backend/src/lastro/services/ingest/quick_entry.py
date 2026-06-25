import re
from dataclasses import dataclass

_AMOUNT_TOKEN = re.compile(r"^\d+(?:[.,]\d{1,2})?$")
_CATEGORY_TOKEN = re.compile(r"^#(?P<category>\S*)$")
_INSTALLMENT_TOKEN = re.compile(r"^(?P<current>\d+)/(?P<total>\d+)$")
_STRAY_INSTALLMENT_PATTERN = re.compile(r"\d+[-\\]\d+")


class QuickEntryParseError(ValueError):
    """Levantado quando a mini-sintaxe de quick-entry não pode ser interpretada."""


@dataclass
class ParsedEntry:
    description: str
    amount_cents: int
    category_name: str | None
    installment_current: int | None
    installment_total: int | None


def parse_quick_entry(raw: str) -> ParsedEntry:
    text = raw.strip()
    if not text:
        raise QuickEntryParseError("entrada vazia")

    tokens = text.split()

    category_name = None
    installment_current = None
    installment_total = None

    # Consome até 2 tokens finais opcionais (categoria e parcela, em qualquer ordem).
    for _ in range(2):
        if not tokens:
            break

        last = tokens[-1]
        category_match = _CATEGORY_TOKEN.match(last)
        installment_match = _INSTALLMENT_TOKEN.match(last)

        if category_match and category_name is None:
            category_name = category_match.group("category")
            if not category_name:
                raise QuickEntryParseError("categoria vazia após #")
            tokens.pop()
        elif installment_match and installment_current is None:
            installment_current, installment_total = _parse_installment(
                installment_match.group("current"), installment_match.group("total")
            )
            tokens.pop()
        else:
            break

    if not tokens:
        raise QuickEntryParseError(f"não foi possível interpretar: {raw!r}")

    raw_amount = tokens[-1]
    if not _AMOUNT_TOKEN.match(raw_amount):
        if _STRAY_INSTALLMENT_PATTERN.search(raw_amount):
            raise QuickEntryParseError("formato de parcela inválido, use X/Y (ex.: 3/9)")
        raise QuickEntryParseError(f"não foi possível interpretar: {raw!r}")
    amount_cents = _parse_amount_cents(raw_amount)
    tokens.pop()

    if not tokens:
        raise QuickEntryParseError("descrição vazia")

    description = " ".join(tokens)
    if _STRAY_INSTALLMENT_PATTERN.search(description) or _INSTALLMENT_TOKEN.match(tokens[-1]):
        raise QuickEntryParseError("formato inválido: parcela deve vir depois do valor, não antes")

    return ParsedEntry(
        description=description,
        amount_cents=amount_cents,
        category_name=category_name,
        installment_current=installment_current,
        installment_total=installment_total,
    )


def _parse_amount_cents(raw_amount: str) -> int:
    normalized = raw_amount.replace(",", ".")
    value = float(normalized)
    if value <= 0:
        raise QuickEntryParseError("valor deve ser maior que zero")
    return round(value * 100)


def _parse_installment(raw_current: str, raw_total: str) -> tuple[int, int]:
    current = int(raw_current)
    total = int(raw_total)
    if current < 1:
        raise QuickEntryParseError("parcela atual deve ser maior ou igual a 1")
    if total < current:
        raise QuickEntryParseError("parcela total deve ser maior ou igual à atual")
    return current, total
