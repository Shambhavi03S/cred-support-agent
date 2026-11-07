import { Grid2 as Grid, Chip, List, ListItem, ListItemText, Typography } from '@mui/material'
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useGet } from '../hooks'
import { Panel, Stat, State } from '../components'

const COLORS = ['#7c5cff', '#00e5ff', '#2ee59d', '#ffb547', '#ff5d7a']

export default function Dashboard() {
  const s = useGet('/stats')
  const h = useGet('/health')
  const d = s.data
  const st = d ? Object.entries(d.by_status).map(([name, value]) => ({ name, value })) : []
  const cat = d ? Object.entries(d.by_category).map(([name, value]) => ({ name, value })) : []
  return (
    <State loading={s.loading} error={s.error}>
      {d && (
        <Grid container spacing={2}>
          <Grid size={{ xs: 6, md: 3 }}><Stat label="Total loan applications" value={d.total_loans} /></Grid>
          <Grid size={{ xs: 6, md: 3 }}><Stat label="Approved" value={d.by_status.Approved ?? 0} color="success.main" /></Grid>
          <Grid size={{ xs: 6, md: 3 }}><Stat label="Pending (Submitted + Under Review)" value={(d.by_status.Submitted ?? 0) + (d.by_status['Under Review'] ?? 0)} color="warning.main" /></Grid>
          <Grid size={{ xs: 6, md: 3 }}><Stat label="Rejected" value={d.by_status.Rejected ?? 0} color="error.main" /></Grid>
          <Grid size={{ xs: 6, md: 3 }}><Stat label="Fraud-review cases" value={d.fraud_review} color="error.main" /></Grid>
          <Grid size={{ xs: 6, md: 3 }}><Stat label={`Escalation cases (score ≥ ${d.escalation_threshold})`} value={d.escalations} color="error.main" /></Grid>
          <Grid size={{ xs: 6, md: 3 }}><Stat label="Knowledge-base documents" value={d.kb_documents} /></Grid>
          <Grid size={{ xs: 6, md: 3 }}>
            <Panel title="API health">
              {h.data ? <Chip color="success" label={`${h.data.status.toUpperCase()} · ${h.data.llm_mode}`} /> : <Chip color="error" label="UNREACHABLE" />}
            </Panel>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Panel title="Applications by status">
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={st} dataKey="value" nameKey="name" outerRadius={90} label>
                    {st.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Panel>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Panel title="Applications by category">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={cat}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={11} /><YAxis allowDecimals={false} /><Tooltip />
                  <Bar dataKey="value" fill="#00e5ff" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Panel>
          </Grid>
          <Grid size={12}>
            <Panel title="Recent customer conversations">
              {d.recent_queries.length === 0 && <Typography color="text.secondary">No conversations yet — try the AI Support Agent.</Typography>}
              <List dense>
                {d.recent_queries.map((c) => (
                  <ListItem key={c.conversation_id} divider>
                    <ListItemText primary={c.last_message} secondary={`${c.conversation_id} · ${c.turns} messages`} />
                  </ListItem>
                ))}
              </List>
            </Panel>
          </Grid>
        </Grid>
      )}
    </State>
  )
}
