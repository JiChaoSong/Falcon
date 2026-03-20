const CHINA_LOCALE = 'zh-CN'
const CHINA_TIME_ZONE = 'Asia/Shanghai'

const normalizeUtcInput = (value: string): string => {
  const trimmed = value.trim()
  if (!trimmed) {
    return trimmed
  }

  if (/[zZ]$/.test(trimmed) || /[+-]\d{2}:\d{2}$/.test(trimmed)) {
    return trimmed
  }

  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(trimmed)) {
    return trimmed.replace(' ', 'T') + 'Z'
  }

  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(trimmed)) {
    return `${trimmed}Z`
  }

  return trimmed
}

export const parseUtcDate = (value: string | undefined | null): Date | null => {
  if (!value) {
    return null
  }

  const date = new Date(normalizeUtcInput(value))
  if (Number.isNaN(date.getTime())) {
    return null
  }

  return date
}

export const formatNumber = (value: number | undefined, fallback: string = '0.00'): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return fallback
  }
  return value.toFixed(2)
}

export const formatPercent = (value: number | undefined, fallback: string = '0.00%'): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return fallback
  }
  return (value * 100).toFixed(2) + '%'
}

export const formatNumberWithCommas = (value: number | undefined, fallback: string = '0'): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return fallback
  }
  return value.toLocaleString('en-US')
}

export const formatDateTime = (value: string | undefined | null, fallback: string = '-'): string => {
  const date = parseUtcDate(value)
  if (!date) {
    return fallback
  }

  return date.toLocaleString(CHINA_LOCALE, {
    hour12: false,
    timeZone: CHINA_TIME_ZONE,
  })
}

export const formatTimeOnly = (value: string | undefined | null, fallback: string = '-'): string => {
  const date = parseUtcDate(value)
  if (!date) {
    return fallback
  }

  return date.toLocaleTimeString(CHINA_LOCALE, {
    hour12: false,
    timeZone: CHINA_TIME_ZONE,
  })
}

export const downloadTextFile = (filename: string, content: string, type: string = 'text/plain;charset=utf-8'): void => {
  const blob = new Blob([content], { type })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export const generateUUID = () => {
    let d = new Date().getTime();
  let d2 = (performance && performance.now && (performance.now()*1000)) || 0;
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    let r = Math.random() * 16;
    if (d > 0) {
      r = (d + r) % 16 | 0;
      d = Math.floor(d / 16);
    } else {
      r = (d2 + r) % 16 | 0;
      d2 = Math.floor(d2 / 16);
    }
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}