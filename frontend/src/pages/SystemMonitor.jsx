import { Button, Chip, Grid2 as Grid, Stack, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material'
import { API_URL } from '../api'
import { useGet } from '../hooks'
import { Panel, State, Stat } from '../components'

export default function SystemMonitor() {
  const h = useGet('/health')
  const logs = useGet('/monitor/logs', { limit: 50 })
  return (
    <Stack spacing={2}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 6, md: 3 }}><Stat label="API status" value={h.data?.status ?? (h.error ? 'down' : '…')} color={h.data ? 'success.main' : 'error.main'} /></Grid>
        <Grid size={{ xs: 6, md: 3 }}><Stat label="LLM mode" value={h.data?.llm_mode} /></Grid>
        <Grid size={{ xs: 6, md: 3 }}><Stat label="KB documents" value={h.data?.kb_documents} /></Grid>
        <Grid size={{ xs: 6, md: 3 }}><Stat label="'I don't know' threshold" value={h.data?.similarity_threshold} /></Grid>
      </Grid>
      <Panel title="Request log (JSON-Lines, newest first)">
        <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
          <Button size="small" onClick={logs.reload}>Refresh</Button>
          <Button size="small" href={`${API_URL}/docs`} target="_blank">Open Swagger UI</Button>
        </Stack>
        <State loading={logs.loading} error={logs.error}>
          <div style={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead><TableRow>{['Time (UTC)', 'Trace ID', 'Method', 'Path', 'Status', 'ms', 'Masked query'].map((x) => <TableCell key={x}><b>{x}</b></TableCell>)}</TableRow></TableHead>
              <TableBody>
                {logs.data?.map((l, i) => (
                  <TableRow key={i}><TableCell>{l.ts}</TableCell><TableCell>{l.trace_id}</TableCell><TableCell>{l.method}</TableCell><TableCell>{l.path}</TableCell>
                    <TableCell><Chip size="small" color={l.status < 400 ? 'success' : 'error'} label={l.status} /></TableCell><TableCell>{l.duration_ms}</TableCell><TableCell>{l.query_masked ?? '—'}</TableCell></TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </State>
      </Panel>
    </Stack>
  )
}
