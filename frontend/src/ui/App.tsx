import React, { useEffect, useMemo, useState } from 'react'
import { Lead } from '../types'
import { getLeads, getReport, runCampaign, uploadCsv } from '../api'

export default function App() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [report, setReport] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [q, setQ] = useState('')

  const filtered = useMemo(() => {
    const key = q.trim().toLowerCase()
    if (!key) return leads
    return leads.filter(l =>
      (l.name||'').toLowerCase().includes(key) ||
      (l.company||'').toLowerCase().includes(key) ||
      (l.title||'').toLowerCase().includes(key) ||
      (l.email||'').toLowerCase().includes(key) ||
      (l.persona||'').toLowerCase().includes(key)
    )
  }, [leads, q])

  async function refreshAll() {
    const [ls, rp] = await Promise.all([getLeads(), getReport()])
    setLeads(ls.leads || [])
    setReport(rp || '')
  }

  useEffect(() => { refreshAll() }, [])

  async function handleRun() {
    setLoading(true)
    try {
      await runCampaign()
      await refreshAll()
    } finally {
      setLoading(false)
    }
  }

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const input = e.currentTarget.querySelector('input[type=file]') as HTMLInputElement
    if (!input?.files?.length) return
    await uploadCsv(input.files[0])
    input.value = ''
    await refreshAll()
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Sales Campaign CRM — React</h1>
        <div style={{display:'flex', gap:8}}>
          <button className="btn" onClick={() => refreshAll()}>Refresh</button>
          <button className="btn primary" onClick={handleRun} disabled={loading}>
            {loading ? 'Running…' : 'Run Campaign'}
          </button>
          <a className="btn" href="/files/data/leads_enriched.csv" download>Download CSV</a>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleUpload} style={{display:'flex', gap:8, alignItems:'center'}}>
          <input type="file" accept=".csv" />
          <button className="btn primary" type="submit">Upload CSV</button>
          <input className="btn" placeholder="Search…" onChange={e=>setQ(e.target.value)} />
        </form>
        <div className="footer">Tip: upload your own leads.csv with headers: name,title,company,email,notes</div>
      </div>

      <div className="card" style={{overflow:'auto'}}>
        <table className="table">
          <thead>
            <tr>
              <th>Name</th><th>Title</th><th>Company</th><th>Email</th>
              <th>Score</th><th>Persona</th><th>Priority</th>
              <th>Status</th><th>Response</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((l, i) => (
              <tr key={i}>
                <td>{l.name}</td>
                <td>{l.title}</td>
                <td>{l.company}</td>
                <td>{l.email}</td>
                <td>{l.score}</td>
                <td>{l.persona}</td>
                <td>
                  <span className={"badge " + (l.priority||'').toLowerCase()}>{l.priority}</span>
                </td>
                <td>{l.status}</td>
                <td>{l.response_class}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3 style={{marginTop:0}}>Campaign Report</h3>
        <pre>{report || 'No report yet.'}</pre>
      </div>

      <div className="footer">FastAPI backend on :8000 · React on :3000 (prod) / :5173 (dev)</div>
    </div>
  )
}