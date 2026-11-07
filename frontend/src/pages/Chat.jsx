import { useEffect, useRef, useState } from 'react'
import { Alert, Box, Button, Chip, Grid2 as Grid, Paper, Stack, TextField, Typography } from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import { api, errMsg } from '../api'
import { Panel, money } from '../components'

const SAMPLES = ['What is the prepayment penalty on a fixed-rate loan?', 'What is the status of LA-1009?', 'Is it flagged for fraud and should it be escalated?']

export default function Chat() {
  const [cid, setCid] = useState(null)
  const [msgs, setMsgs] = useState([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [last, setLast] = useState(null)
  const end = useRef(null)
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs])

  const send = async (q) => {
    const query = (q ?? text).trim()
    if (!query || busy) return
    setText(''); setBusy(true); setError(null)
    setMsgs((m) => [...m, { role: 'user', content: query }])
    try {
      const { data } = await api.post('/ask', { query, conversation_id: cid })
      setCid(data.conversation_id); setLast(data)
      setMsgs((m) => [...m, { role: 'assistant', content: data.answer, meta: data }])
    } catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }
  const newChat = () => { setCid(null); setMsgs([]); setLast(null); setError(null) }

  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, lg: 8 }}>
        <Panel sx={{ display: 'flex', flexDirection: 'column' }}>
          <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
            <Typography variant="caption" color="text.secondary">Conversation: {cid ?? 'new (id assigned on first message)'}</Typography>
            <Button size="small" onClick={newChat}>New conversation</Button>
          </Stack>
          <Box sx={{ height: 420, overflowY: 'auto', bgcolor: 'rgba(5,8,25,0.6)', border: '1px solid rgba(0,229,255,0.15)', p: 1.5, borderRadius: 2 }}>
            {msgs.length === 0 && (
              <Stack spacing={1}>
                <Typography color="text.secondary">Ask a policy question or check a loan application. Try:</Typography>
                {SAMPLES.map((s) => <Chip key={s} label={s} onClick={() => send(s)} sx={{ alignSelf: 'flex-start' }} />)}
              </Stack>
            )}
            {msgs.map((m, i) => (
              <Box key={i} sx={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', mb: 1, animation: 'fadeUp .35s ease both' }}>
                <Paper sx={{ p: 1.4, maxWidth: '80%', color: '#fff',
                  background: m.role === 'user' ? 'linear-gradient(135deg,#7c5cff,#4b8bff)' : 'rgba(255,255,255,0.08)',
                  border: m.role === 'user' ? 'none' : '1px solid rgba(0,229,255,0.3)',
                  borderRadius: m.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px' }}>
                  <Typography variant="body2">{m.content}</Typography>
                  {m.meta?.loan?.escalate && <Chip size="small" color="error" label="ESCALATE" sx={{ mt: 0.5, animation: 'pulse 1.6s infinite' }} />}
                </Paper>
              </Box>
            ))}
            {busy && (
              <Box sx={{ display: 'flex', gap: 0.6, p: 1.4, width: 'fit-content', borderRadius: 3, bgcolor: 'rgba(255,255,255,0.08)' }}>
                {[0, 1, 2].map((d) => <Box key={d} sx={{ width: 9, height: 9, borderRadius: '50%', bgcolor: 'secondary.main', animation: `bounce 1.2s ${d * 0.18}s infinite` }} />)}
              </Box>
            )}
            <div ref={end} />
          </Box>
          {error && <Alert severity="error" sx={{ mt: 1 }}>{error}</Alert>}
          <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
            <TextField fullWidth size="small" placeholder="Type your question…" value={text} disabled={busy}
              onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && send()} />
            <Button variant="contained" endIcon={<SendIcon />} disabled={busy} onClick={() => send()}>{busy ? 'Thinking…' : 'Send'}</Button>
          </Stack>
        </Panel>
      </Grid>
      <Grid size={{ xs: 12, lg: 4 }}>
        <Stack spacing={2}>
          <Panel title="Model & routing">
            {last ? (
              <Stack spacing={0.5}>
                <Typography variant="body2">Model: <b>{last.model}</b></Typography>
                <Typography variant="body2">Intent: <b>{last.intent}</b> → route <b>{last.route}</b></Typography>
                <Typography variant="body2">Trace ID: {last.trace_id}</Typography>
                <Typography variant="caption" color="text.secondary">Agent graph path:</Typography>
                <Stack direction="row" flexWrap="wrap" useFlexGap spacing={0.6} alignItems="center">
                  {last.nodes_executed.map((n, k) => (
                    <Chip key={`${last.trace_id}-${k}`} size="small" label={n} color="secondary" variant="outlined"
                      sx={{ opacity: 0, animation: `pop .35s ${k * 0.15}s ease forwards`, boxShadow: '0 0 8px rgba(0,229,255,0.5)' }} />
                  ))}
                </Stack>
                <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                  {last.guardrails.pii_masked.map((p) => <Chip key={p} size="small" color="warning" label={`${p} masked`} />)}
                  {last.guardrails.injection_detected && <Chip size="small" color="error" label="Injection blocked" />}
                  {last.guardrails.fallback_triggered && <Chip size="small" label="Fallback (no evidence)" />}
                </Stack>
              </Stack>
            ) : <Typography variant="body2" color="text.secondary">Send a message to see execution details.</Typography>}
          </Panel>
          <Panel title="Retrieved sources">
            {last?.sources?.length ? last.sources.map((s) => (
              <Box key={s.doc_id} sx={{ mb: 1 }}>
                <Typography variant="body2"><b>{s.title}</b> <Chip size="small" label={`sim ${s.similarity.toFixed(2)}`} /></Typography>
                <Typography variant="caption" color="text.secondary">{s.doc_id}</Typography>
              </Box>
            )) : <Typography variant="body2" color="text.secondary">None for this turn.</Typography>}
          </Panel>
          <Panel title="Loan lookup result">
            {last?.loan ? (
              <Stack spacing={0.3}>
                <Typography variant="body2"><b>{last.loan.record_id}</b> · {last.loan.category}</Typography>
                <Typography variant="body2">Status: {last.loan.status}</Typography>
                <Typography variant="body2">Amount: {money(last.loan.loan_amount_inr)}</Typography>
                <Typography variant="body2">Age: {last.loan.days_since_created} days · Fraud flag: {String(last.loan.flagged_for_fraud_review)}</Typography>
                <Typography variant="body2">Escalation score: <b>{last.loan.escalation_score.toFixed(2)}</b> {last.loan.escalate ? <Chip size="small" color="error" label="Escalate" /> : <Chip size="small" color="success" label="No escalation" />}</Typography>
              </Stack>
            ) : <Typography variant="body2" color="text.secondary">No loan lookup on this turn.</Typography>}
          </Panel>
        </Stack>
      </Grid>
    </Grid>
  )
}
