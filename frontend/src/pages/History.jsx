import { useState } from 'react'
import { Box, Grid2 as Grid, List, ListItemButton, ListItemText, Paper, Typography } from '@mui/material'
import { api } from '../api'
import { useGet } from '../hooks'
import { Panel, State } from '../components'

export default function History() {
  const convs = useGet('/conversations')
  const [sel, setSel] = useState(null)
  const [msgs, setMsgs] = useState([])
  const open = async (id) => { setSel(id); setMsgs((await api.get(`/conversations/${id}`)).data.messages) }
  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, md: 4 }}>
        <Panel title="Conversations (persisted in JSON)">
          <State loading={convs.loading} error={convs.error}>
            {convs.data?.length === 0 && <Typography color="text.secondary">None yet.</Typography>}
            <List dense>
              {convs.data?.map((c) => (
                <ListItemButton key={c.conversation_id} selected={sel === c.conversation_id} onClick={() => open(c.conversation_id)}>
                  <ListItemText primary={c.conversation_id} secondary={`${c.turns} messages · ${c.last_message}`} />
                </ListItemButton>
              ))}
            </List>
          </State>
        </Panel>
      </Grid>
      <Grid size={{ xs: 12, md: 8 }}>
        <Panel title={sel ? `Conversation ${sel}` : 'Select a conversation'}>
          {msgs.map((m, i) => (
            <Box key={i} sx={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', mb: 1 }}>
              <Paper variant="outlined" sx={{ p: 1.2, maxWidth: '80%', bgcolor: m.role === 'user' ? '#0b2545' : '#fff', color: m.role === 'user' ? '#fff' : 'inherit' }}>
                <Typography variant="body2">{m.content}</Typography>
                <Typography variant="caption" sx={{ opacity: 0.7 }}>{new Date(m.ts * 1000).toLocaleString()}</Typography>
              </Paper>
            </Box>
          ))}
        </Panel>
      </Grid>
    </Grid>
  )
}
