export function appendToken(url: string | null | undefined, token: string | null | undefined): string | null {
  if (!url) return null
  if (!token) return url
  return url.includes('?')
    ? `${url}&token=${encodeURIComponent(token)}`
    : `${url}?token=${encodeURIComponent(token)}`
}

