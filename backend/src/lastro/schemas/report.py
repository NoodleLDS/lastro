from enum import StrEnum

from pydantic import BaseModel

from lastro.schemas.contribution import ContributionRead
from lastro.schemas.dividend import DividendRead
from lastro.schemas.monthly_summary import FixedExpenseRead, IncomeRead, VariableExpenseRead
from lastro.schemas.sale import SaleRead
from lastro.schemas.transaction import TransactionRead


class ReportModule(StrEnum):
    TRANSACTIONS = "transactions"
    CONTRIBUTIONS = "contributions"
    DIVIDENDS = "dividends"
    SALES = "sales"
    INCOMES = "incomes"
    FIXED_EXPENSES = "fixed_expenses"
    VARIABLE_EXPENSES = "variable_expenses"
    POSITIONS = "positions"


class PositionSnapshot(BaseModel):
    id: int
    ticker: str
    name: str
    asset_type: str
    quantity: float
    last_price_cents: int | None


class Report(BaseModel):
    transactions: list[TransactionRead] | None = None
    contributions: list[ContributionRead] | None = None
    dividends: list[DividendRead] | None = None
    sales: list[SaleRead] | None = None
    incomes: list[IncomeRead] | None = None
    fixed_expenses: list[FixedExpenseRead] | None = None
    variable_expenses: list[VariableExpenseRead] | None = None
    positions: list[PositionSnapshot] | None = None
