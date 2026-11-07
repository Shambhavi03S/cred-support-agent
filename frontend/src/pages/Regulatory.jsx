import { useState } from 'react'
import { Alert, Button, Chip, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material'
import { api, errMsg } from '../api'
import { useGet } from '../hooks'
import { Panel, State } from '../components'

const EMPTY = { doc_id: '', title: '', authority: '', source_url: '', publication_date: '', effective_date: '' }

export default function Regulatory() {
  const docs = useGet('/regulatory/documents')
  const [f, setF] = useState(EMPTY)
  const [msg, setMsg] = useState(null)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const register = async () => {
    setMsg(null)
    const body = Object.fromEntries(Object.entries(f).filter(([, v]) => v !== ''))
    try { await api.post('/regulatory/register', body); setF(EMPTY); docs.reload(); setMsg({ s: 'success', t: 'Source registered. Click "Update" to fetch and index it (requires internet).' }) }
    catch (e) { setMsg({ s: 'error', t: errMsg(e) }) }
  }
  const update = async (id) => {
    setMsg(null)
    try { const { data } = await api.post(`/regulatory/${id}/update`); docs.reload(); setMsg({ s: data.result === 'updated' || data.result === 'unchanged' ? 'success' : 'warning', t: JSON.stringify(data) }) }
    catch (e) { setMsg({ s: 'error', t: errMsg(e) }) }
  }
  return (
    <Stack spacing={2}>
      <Alert severity="info">
        No regulation text is bundled. Register an <b>official</b> source URL (RBI, Ministry of Finance / DFS, India Code …), then run a manual update while online.
        Documents are marked <b>Unverified</b> until a person confirms they are in force. Offline, the last indexed copy keeps serving retrieval.
      </Alert>
      <Panel title="Register official source">
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} flexWrap="wrap" useFlexGap>
          <TextField size="small" label="Document ID" value={f.doc_id} onChange={set('doc_id')} />
          <TextField size="small" label="Title" value={f.title} onChange={set('title')} />
          <TextField size="small" label="Authority (e.g. RBI)" value={f.authority} onChange={set('authority')} />
          <TextField size="small" label="Source URL (https://…)" value={f.source_url} onChange={set('source_url')} sx={{ minWidth: 280 }} />
          <TextField size="small" label="Publication date" placeholder="YYYY-MM-DD" value={f.publication_date} onChange={set('publication_date')} />
          <TextField size="small" label="Effective date" placeholder="YYYY-MM-DD" value={f.effective_date} onChange={set('effective_date')} />
          <Button variant="contained" onClick={register} disabled={!f.doc_id || !f.title || !f.authority || !f.source_url}>Register</Button>
        </Stack>
        {msg && <Alert severity={msg.s} sx={{ mt: 1 }}>{msg.t}</Alert>}
      </Panel>
      <Panel title="Regulatory documents">
        <State loading={docs.loading} error={docs.error}>
          {docs.data?.length === 0 && <Typography color="text.secondary">No regulatory documents registered yet.</Typography>}
          {docs.data?.length > 0 && (
            <div style={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead><TableRow>{['Title', 'Authority', 'Published', 'Effective', 'Version', 'Status', 'Last indexed', 'Source', ''].map((h) => <TableCell key={h}><b>{h}</b></TableCell>)}</TableRow></TableHead>
                <TableBody>
                  {docs.data.map((d) => (
                    <TableRow key={d.doc_id}>
                      <TableCell>{d.title}</TableCell><TableCell>{d.authority}</TableCell>
                      <TableCell>{d.publication_date ?? 'unknown'}</TableCell><TableCell>{d.effective_date ?? 'unknown'}</TableCell>
                      <TableCell>{d.version}{d.versions.some((v) => v.status === 'superseded') && <Chip size="small" sx={{ ml: 0.5 }} label={`${d.versions.filter((v) => v.status === 'superseded').length} superseded`} />}</TableCell>
                      <TableCell>{d.status}</TableCell><TableCell>{d.last_indexed ?? '—'}</TableCell>
                      <TableCell><a href={d.source_url} target="_blank" rel="noreferrer">link</a></TableCell>
                      <TableCell><Button size="small" onClick={() => update(d.doc_id)}>Update</Button></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </State>
      </Panel>
    </Stack>
  )
}
