import { Alert, Typography } from '@mui/material'
import { useGet } from '../hooks'
import { Panel, State } from '../components'
import { LoanTable } from './Loans.jsx'

export default function Escalations() {
  const loans = useGet('/loans')
  const rows = (loans.data ?? []).filter((r) => r.escalate).sort((a, b) => b.escalation_score - a.escalation_score)
  const watch = (loans.data ?? []).filter((r) => !r.escalate && r.flagged_for_fraud_review)
  return (
    <State loading={loans.loading} error={loans.error}>
      <Alert severity="info" sx={{ mb: 2 }}>
        Escalation score = 0.5 × fraud-review flag + 0.5 × (days since created ÷ 30). Escalate at ≥ {loans.data?.[0]?.escalation_threshold ?? 0.7}.
      </Alert>
      <Panel title={`Escalate now (${rows.length})`}>
        <div style={{ overflowX: 'auto' }}><LoanTable rows={rows} /></div>
        {rows.length === 0 && <Typography color="text.secondary">No applications currently meet the escalation threshold.</Typography>}
      </Panel>
      <Panel title={`Fraud-flagged, below threshold — monitor (${watch.length})`} sx={{ mt: 2 }}>
        <div style={{ overflowX: 'auto' }}><LoanTable rows={watch} /></div>
      </Panel>
    </State>
  )
}
