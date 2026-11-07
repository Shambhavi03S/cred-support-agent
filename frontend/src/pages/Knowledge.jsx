import { useState } from 'react'
import { Alert, Button, Chip, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material'
import { api, errMsg } from '../api'
import { useGet } from '../hooks'
import { Panel, State } from '../components'

export default function Knowledge() {
  const docs = useGet('/knowledge/documents')
  const [q, setQ] = useState('')
  const [res, setRes] = useState(null)
  const [err, setErr] = useState(null)
  const search = async () => {
    setErr(null)
    try { setRes((await api.get('/knowledge/search', { params: { q, k: 3 } })).data) } catch (e) { setErr(errMsg(e)) }
  }
  return (
    <Stack spacing={2}>
      <Panel title="Test retrieval">
        <Stack direction="row" spacing={1}>
          <TextField fullWidth size="small" placeholder="e.g. documents needed for KYC" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && q && search()} />
          <Button variant="contained" onClick={search} disabled={!q}>Search</Button>
        </Stack>
        {err && <Alert severity="error" sx={{ mt: 1 }}>{err}</Alert>}
        {res && (
          <Stack spacing={1} sx={{ mt: 1.5 }}>
            <Typography variant="caption">"I don't know" threshold: {res.threshold} (calibrated)</Typography>
            {res.results.map((r, i) => (
              <Alert key={i} severity={r.similarity >= res.threshold ? 'success' : 'warning'} icon={false}>
                <b>{r.title}</b> <Chip size="small" label={`similarity ${r.similarity.toFixed(3)}`} /><br />{r.text}
              </Alert>
            ))}
          </Stack>
        )}
      </Panel>
      <Panel title={`Indexed knowledge-base documents (${docs.data?.length ?? 0})`}>
        <State loading={docs.loading} error={docs.error}>
          <Table size="small">
            <TableHead><TableRow>{['ID', 'Title', 'Topic', 'Sentences', 'Source'].map((h) => <TableCell key={h}><b>{h}</b></TableCell>)}</TableRow></TableHead>
            <TableBody>
              {docs.data?.map((d) => (
                <TableRow key={d.doc_id}><TableCell>{d.doc_id}</TableCell><TableCell>{d.title}</TableCell><TableCell>{d.topic}</TableCell><TableCell>{d.sentences}</TableCell><TableCell>{d.source}</TableCell></TableRow>
              ))}
            </TableBody>
          </Table>
        </State>
      </Panel>
    </Stack>
  )
}
