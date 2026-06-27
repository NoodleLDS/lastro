const BRAND_ICONS: Record<string, string> = {
  nubank: '/branding/cards/nubank.svg',
  picpay: '/branding/cards/picpay.png',
  inter: '/branding/cards/inter.png',
  santander: '/branding/cards/santander.png',
}

export function getCardBrandIcon(cardName: string): string | null {
  const key = cardName.trim().toLowerCase()
  return BRAND_ICONS[key] ?? null
}
