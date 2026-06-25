from pydantic import BaseModel

from lastro.models.allocation_target import AllocationTarget
from lastro.models.position import AssetType, Position

DEVIATION_ALERT_THRESHOLD_PCT = 5.0


class AllocationBreakdown(BaseModel):
    asset_type: AssetType
    current_value_cents: int
    current_percentage: float
    target_percentage: float | None
    deviation_pct: float | None
    is_deviation_alert: bool


def calculate_allocation(
    positions: list[Position],
    targets: list[AllocationTarget],
) -> list[AllocationBreakdown]:
    """Alocação real (por asset_type) vs meta. Posições sem last_price_cents
    não entram no total (cotação ainda não buscada)."""
    values_by_type: dict[AssetType, int] = {}
    for position in positions:
        if position.last_price_cents is None:
            continue
        value_cents = round(position.quantity * position.last_price_cents)
        values_by_type[position.asset_type] = (
            values_by_type.get(position.asset_type, 0) + value_cents
        )

    total_cents = sum(values_by_type.values())
    targets_by_type = {target.asset_type: target.target_percentage for target in targets}

    breakdown: list[AllocationBreakdown] = []
    for asset_type, value_cents in values_by_type.items():
        current_percentage = (value_cents / total_cents * 100) if total_cents else 0.0
        target_percentage = targets_by_type.get(asset_type)

        deviation_pct = None
        is_deviation_alert = False
        if target_percentage is not None:
            deviation_pct = current_percentage - target_percentage
            is_deviation_alert = abs(deviation_pct) > DEVIATION_ALERT_THRESHOLD_PCT

        breakdown.append(
            AllocationBreakdown(
                asset_type=asset_type,
                current_value_cents=value_cents,
                current_percentage=current_percentage,
                target_percentage=target_percentage,
                deviation_pct=deviation_pct,
                is_deviation_alert=is_deviation_alert,
            )
        )

    return breakdown
