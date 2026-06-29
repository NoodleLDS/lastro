export const ASSET_TYPE_LABELS: Record<string, string> = {
  stock: 'Ações',
  fii: 'FIIs',
  etf: 'ETFs',
  fixed_income: 'Renda fixa',
  crypto: 'Cripto',
}

export function assetTypeLabel(assetType: string): string {
  return ASSET_TYPE_LABELS[assetType] ?? assetType
}
