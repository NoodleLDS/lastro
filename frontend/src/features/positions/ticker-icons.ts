const TICKER_ICONS: Record<string, string> = {
  BBAS3: '/branding/tickers/bbas3.avif',
  BBDC4: '/branding/tickers/bbdc4.avif',
  CMIG4: '/branding/tickers/cmig4.avif',
  ITUB4: '/branding/tickers/itub4.avif',
  PETR4: '/branding/tickers/petr4.avif',
  IVVB11: '/branding/tickers/ivvb11.svg',
}

const FII_SUFFIX = /11B?$/

export function getTickerIcon(ticker: string, assetType: string): string | null {
  const key = ticker.trim().toUpperCase()
  if (TICKER_ICONS[key]) return TICKER_ICONS[key]
  if (assetType === 'fii' || FII_SUFFIX.test(key)) return '/branding/tickers/fii-generic.svg'
  return null
}
