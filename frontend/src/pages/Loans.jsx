import { useState } from 'react'
import { Alert, Button, Chip, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material'
import { api, errMsg } from '../api'
import { useGet } from '../hooks'
import { Panel, State, money } from '../components'

export function LoanTable({ rows }) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>{['Application', 'Customer', 'Category', 'Status', 'Amount', 'Age (days)', 'Fraud review', 'Escalation'].map((h) => <TableCell key={h}><b>{h}</b></TableCell>)}</TableRow>
      </TableHead>
      <TableBody>
        {rows.map((r) => (
          <TableRow key={r.record_id} hover>
            <TableCell>{r.record_id}</TableCell><TableCell>{r.customer_id}</TableCell><TableCell>{r.category}</TableCell>
            <TableCell>{r.status}</TableCell><TableCell>{money(r.loan_amount_inr)}</TableCell><TableCell>{r.days_since_created}</TableCell>
            <TableCell>{r.flagged_for_fraud_review ? <Chip size="small" color="error" label="Flagged" /> : 'No'}</TableCell>
            <TableCell>{r.escalation_score.toFixed(2)} {r.escalate && <Chip size="small" color="error" label="Escalate" />}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export default function Loans() {
  const [appId, setAppId] = useState('')
  const [custId, setCustId] = useState('')
  const [filter, setFilter] = useState({})
  const [detail, setDetail] = useState(null)
  const [err, setErr] = useState(null)
  const list = useGet('/loans', filter, [])

  const searchApp = async () => {
    setErr(null); setDetail(null)
    try { setDetail((await api.get(`/loans/${encodeURIComponent(appId.trim())}`)).data) } catch (e) { setErr(errMsg(e)) }
  }
  return (
    <Stack spacing={2}>
      <Panel title="Search">
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
          <TextField size="small" label="Application ID (e.g. LA-1005)" value={appId} onChange={(e) => setAppId(e.target.value)} />
          <Button variant="contained" onClick={searchApp} disabled={!appId.trim()}>Find application</Button>
          <TextField size="small" label="Customer ID (e.g. CUST-12345)" value={custId} onChange={(e) => setCustId(e.target.value)} />
          <Button variant="outlined" onClick={() => setFilter(custId.trim() ? { customer_id: custId.trim() } : {})}>{custId.trim() ? 'Filter by customer' : 'Show all'}</Button>
        </Stack>
        {err && <Alert severity="warning" sx={{ mt: 1 }}>{err}</Alert>}
        {detail && (
          <Alert severity={detail.escalate ? 'error' : 'info'} sx={{ mt: 1 }}>
            <b>{detail.record_id}</b> — {detail.applicant_name} ({detail.customer_id}) · {detail.category} · <b>{detail.status}</b> · {money(detail.loan_amount_inr)} ·
            created {detail.created_date} ({detail.days_since_created} days ago) · fraud review: {String(detail.flagged_for_fraud_review)} · escalation score {detail.escalation_score.toFixed(2)}
          </Alert>
        )}
      </Panel>
      <Panel title={`Applications (${list.data?.length ?? 0})`}>
        <State loading={list.loading} error={list.error}>
          <div style={{ overflowX: 'auto' }}>{list.data && <LoanTable rows={list.data} />}</div>
          {list.data?.length === 0 && <Typography color="text.secondary">No applications match.</Typography>}
        </State>
      </Panel>
    </Stack>
  )
}
