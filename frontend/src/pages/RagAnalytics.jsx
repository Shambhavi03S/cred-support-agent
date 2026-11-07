import { Alert, Grid2 as Grid, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useGet } from '../hooks'
import { Panel, State, Stat } from '../components'

export default function RagAnalytics() {
  const a = useGet('/analytics/rag')
  const d = a.data
  const chunk = d?.chunking ? Object.entries(d.chunking).map(([k, v]) => ({
    name: k.replace('_gold', '').replace('kb_', '').replace('fixed_overlap', 'fixed').replace('/', ' · '),
    'Precision@3': v['mean_precision@3'], 'Recall@3': v['mean_recall@3'] })) : []
  return (
    <State loading={a.loading} error={a.error}>
      {d && (!d.chunking || !d.triad) && <Alert severity="warning">Run scripts/eval_chunking.py and scripts/eval_triad.py to generate results.</Alert>}
      <Stack spacing={2}>
        {d?.triad && (
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 4 }}><Stat label="Avg. context relevance (15 queries)" value={d.triad.averages.context_relevance.toFixed(3)} /></Grid>
            <Grid size={{ xs: 12, md: 4 }}><Stat label="Avg. groundedness" value={d.triad.averages.groundedness.toFixed(3)} /></Grid>
            <Grid size={{ xs: 12, md: 4 }}><Stat label="Avg. answer relevance" value={d.triad.averages.answer_relevance.toFixed(3)} /></Grid>
          </Grid>
        )}
        {d?.chunking && (
          <Panel title="Chunking strategies — Precision@3 / Recall@3 (document level)">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chunk}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" fontSize={11} /><YAxis domain={[0, 1]} /><Tooltip /><Legend />
                <Bar dataKey="Precision@3" fill="#7c5cff" radius={[6, 6, 0, 0]} /><Bar dataKey="Recall@3" fill="#00e5ff" radius={[6, 6, 0, 0]} /></BarChart>
            </ResponsiveContainer>
          </Panel>
        )}
        {d?.calibration && (
          <Panel title="Calibrated &quot;I don't know&quot; thresholds">
            {Object.entries(d.calibration).map(([c, v]) => (
              <Typography key={c} variant="body2">{c}: threshold <b>{v.threshold}</b> (min in-scope {v.min_in_scope.toFixed(3)}, max out-of-scope {v.max_out_of_scope.toFixed(3)})</Typography>
            ))}
          </Panel>
        )}
        {d?.triad && (
          <Panel title="Per-query RAG triad (MOCK_LLM judge)">
            <div style={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead><TableRow>{['#', 'Query', 'Ctx. rel.', 'Grounded', 'Ans. rel.', 'Fallback'].map((h) => <TableCell key={h}><b>{h}</b></TableCell>)}</TableRow></TableHead>
                <TableBody>{d.triad.rows.map((r) => (
                  <TableRow key={r.n}><TableCell>{r.n}</TableCell><TableCell>{r.query}</TableCell><TableCell>{r.context_relevance.toFixed(2)}</TableCell><TableCell>{r.groundedness.toFixed(2)}</TableCell><TableCell>{r.answer_relevance.toFixed(2)}</TableCell><TableCell>{String(r.fallback)}</TableCell></TableRow>
                ))}</TableBody>
              </Table>
            </div>
          </Panel>
        )}
      </Stack>
    </State>
  )
}
