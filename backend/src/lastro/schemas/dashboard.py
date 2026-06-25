from pydantic import BaseModel

from lastro.services.analytics.evolution import BenchmarkComparison, EvolutionPoint


class EvolutionResponse(BaseModel):
    points: list[EvolutionPoint]
    comparison: BenchmarkComparison | None


class ProjectionResponse(BaseModel):
    values_cents: list[int]
