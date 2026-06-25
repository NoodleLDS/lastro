def project_portfolio_value(
    current_value_cents: int,
    monthly_contribution_cents: int,
    monthly_return_rate: float,
    months: int,
) -> list[int]:
    """Projeta o valor do patrimônio mês a mês com aporte mensal fixo e taxa
    de retorno mensal constante (juros compostos):

        FV = PV*(1+i)^n + PMT*(((1+i)^n - 1) / i)

    Retorna uma lista de tamanho `months + 1`: índice 0 é o valor atual
    (sem nenhum aporte/juros aplicado ainda), índice N é a projeção após N
    meses.
    """
    values = [current_value_cents]
    value = float(current_value_cents)

    for _ in range(months):
        value = value * (1 + monthly_return_rate) + monthly_contribution_cents
        values.append(round(value))

    return values
