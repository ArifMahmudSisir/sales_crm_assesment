export async function getLeads() {
  const res = await fetch('/api/leads')
  if (!res.ok) throw new Error('Failed to fetch leads')
  return res.json() as Promise<{leads:any[]}>
}

export async function getReport() {
  const res = await fetch('/reports/summary')
  if (!res.ok) return ''
  return res.text()
}

export async function runCampaign() {
  const res = await fetch('/run', { method: 'POST' })
  if (!res.ok) throw new Error('Failed to run campaign')
  return res.json()
}

export async function uploadCsv(file: File) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch('/api/upload', { method: 'POST', body: fd })
  if (!res.ok) throw new Error('Upload failed')
  return res.json()
}