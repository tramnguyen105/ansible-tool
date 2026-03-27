export function formatDateTime(value?: string | null) {
  if (!value) return 'Not scheduled'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatRelativeTime(value?: string | null) {
  if (!value) return 'No recent activity'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const diffMs = date.getTime() - Date.now()
  const absSeconds = Math.round(Math.abs(diffMs) / 1000)
  const units = [
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
    ['second', 1],
  ] as const

  for (const [unit, seconds] of units) {
    if (absSeconds >= seconds || unit === 'second') {
      const value = Math.round(diffMs / 1000 / seconds)
      return new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' }).format(value, unit)
    }
  }

  return value
}

export function pluralize(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`
}

export function truncateMiddle(value: string, max = 20) {
  if (value.length <= max) return value
  const slice = Math.max(4, Math.floor((max - 3) / 2))
  return `${value.slice(0, slice)}...${value.slice(-slice)}`
}
