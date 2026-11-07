import { Alert, Button, Chip, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'
import { useGet } from '../hooks'
import { Panel, State } from '../components'

const TOOL = { rag: 'RAG retrieval tool', loan_tool: 'check_loan_application_status', clarify: 'none (clarification)', blocked: 'none (blocked by guardrail)' }

export default function AgentMonitor() {
  const runs = useGet('/monitor/runs')
  const health = useGet('/health')
  return (
    <Stack spacing={2}>
      <Alert severity="info">Shows only runs recorded by this API process since it started (in-memory, last 50). Nothing here is simulated.</Alert>
      <Panel title="Current agent status">
        {health.data ? <Chip color="success" label={`Online · ${health.data.llm_mode}`} /> : <Chip color="error" label="API unreachable" />}
        <Typography variant="caption" sx={{ ml: 1 }}>Graph: guard_input → classify_intent → {'{rag_retrieve | loan_lookup | clarify}'} → generate_answer → groundedness_check → finalize (refuse on injection)</Typography>
      </Panel>
      <Panel title={`Recent executions (${runs.data?.length ?? 0})`}>
        <Button size="small" onClick={runs.reload} sx={{ mb: 1 }}>Refresh</Button>
        <State loading={runs.loading} error={runs.error}>
          {runs.data?.length === 0 && <Typography color="text.secondary">No agent runs yet.</Typography>}
          <div style={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead><TableRow>{['Time', 'Query (masked)', 'LangGraph stages executed', 'Tool selected', 'Retrieved docs', 'ms', 'Error'].map((h) => <TableCell key={h}><b>{h}</b></TableCell>)}</TableRow></TableHead>
              <TableBody>
                {runs.data?.map((r, i) => (
                  <TableRow key={i}>
                    <TableCell>{new Date(r.ts * 1000).toLocaleTimeString()}</TableCell>
                    <TableCell sx={{ maxWidth: 260 }}>{r.query}</TableCell>
                    <TableCell>{r.nodes?.join(' → ') ?? '—'}</TableCell>
                    <TableCell>{TOOL[r.route] ?? '—'}</TableCell>
                    <TableCell>{r.sources?.join(', ') || '—'}</TableCell>
                    <TableCell>{r.duration_ms ?? '—'}</TableCell>
                    <TableCell>{r.error ? <Chip size="small" color="error" label={r.error} /> : '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </State>
      </Panel>
    </Stack>
  )
}
