import { useState } from 'react'
import { Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText, Typography, Toolbar, AppBar, IconButton, useMediaQuery } from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import DashboardIcon from '@mui/icons-material/Dashboard'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import MenuBookIcon from '@mui/icons-material/MenuBook'
import GavelIcon from '@mui/icons-material/Gavel'
import AccountTreeIcon from '@mui/icons-material/AccountTree'
import InsightsIcon from '@mui/icons-material/Insights'
import PriorityHighIcon from '@mui/icons-material/PriorityHigh'
import HistoryIcon from '@mui/icons-material/History'
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart'
import Dashboard from './pages/Dashboard.jsx'
import Chat from './pages/Chat.jsx'
import Loans from './pages/Loans.jsx'
import Knowledge from './pages/Knowledge.jsx'
import Regulatory from './pages/Regulatory.jsx'
import AgentMonitor from './pages/AgentMonitor.jsx'
import RagAnalytics from './pages/RagAnalytics.jsx'
import Escalations from './pages/Escalations.jsx'
import History from './pages/History.jsx'
import SystemMonitor from './pages/SystemMonitor.jsx'

const NAV = [
  ['Overview Dashboard', DashboardIcon, Dashboard],
  ['AI Support Agent', SmartToyIcon, Chat],
  ['Loan Management', AccountBalanceIcon, Loans],
  ['Knowledge Base', MenuBookIcon, Knowledge],
  ['Regulatory Centre', GavelIcon, Regulatory],
  ['Agent Monitor', AccountTreeIcon, AgentMonitor],
  ['RAG Analytics', InsightsIcon, RagAnalytics],
  ['Escalation Centre', PriorityHighIcon, Escalations],
  ['Conversation History', HistoryIcon, History],
  ['System Monitor', MonitorHeartIcon, SystemMonitor],
]
const W = 250

export default function App() {
  const [idx, setIdx] = useState(0)
  const [open, setOpen] = useState(false)
  const wide = useMediaQuery('(min-width:900px)')
  const Page = NAV[idx][2]
  const drawer = (
    <Box sx={{ background: 'linear-gradient(180deg,#120a3a 0%,#0a1233 60%,#06101f 100%)', color: '#fff', height: '100%', borderRight: '1px solid rgba(124,92,255,0.3)' }}>
      <Toolbar sx={{ py: 2, gap: 1.5 }}>
        <Box sx={{ width: 40, height: 40, borderRadius: '12px', display: 'grid', placeItems: 'center', animation: 'glow 3s ease-in-out infinite',
          background: 'linear-gradient(135deg,#7c5cff,#00e5ff)' }}><SmartToyIcon /></Box>
        <Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 800, letterSpacing: 0.5, lineHeight: 1.2,
            background: 'linear-gradient(90deg,#fff,#00e5ff)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            CRED AGENT
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#2ee59d', animation: 'pulse 1.8s infinite' }} />
            <Typography variant="caption" sx={{ color: '#9fb0d9' }}>Agent online</Typography>
          </Box>
        </Box>
      </Toolbar>
      <List sx={{ px: 1 }}>
        {NAV.map(([label, Icon], i) => (
          <ListItemButton key={label} selected={i === idx} onClick={() => { setIdx(i); setOpen(false) }}
            sx={{ color: '#b7c4e6', borderRadius: '12px', mb: 0.5, transition: 'all .2s',
              '&.Mui-selected': { background: 'linear-gradient(90deg,rgba(124,92,255,0.55),rgba(0,229,255,0.2))', color: '#fff', boxShadow: '0 0 16px rgba(124,92,255,0.45)' },
              '&.Mui-selected:hover': { background: 'linear-gradient(90deg,rgba(124,92,255,0.65),rgba(0,229,255,0.3))' },
              '&:hover': { bgcolor: 'rgba(124,92,255,0.18)', transform: 'translateX(4px)' } }}>
            <ListItemIcon sx={{ color: 'inherit', minWidth: 38 }}><Icon fontSize="small" /></ListItemIcon>
            <ListItemText primary={label} primaryTypographyProps={{ fontSize: 14 }} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  )
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {!wide && (
        <AppBar position="fixed" color="primary" elevation={0}>
          <Toolbar>
            <IconButton color="inherit" onClick={() => setOpen(true)}><MenuIcon /></IconButton>
            <Typography sx={{ ml: 1 }}>{NAV[idx][0]}</Typography>
          </Toolbar>
        </AppBar>
      )}
      <Drawer variant={wide ? 'permanent' : 'temporary'} open={wide || open} onClose={() => setOpen(false)}
        sx={{ width: W, '& .MuiDrawer-paper': { width: W, border: 0 } }}>
        {drawer}
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: { xs: 2, md: 3 }, pt: { xs: 9, md: 3 }, minWidth: 0 }}>
        {wide && <Typography variant="h5" sx={{ mb: 2, background: 'linear-gradient(90deg,#fff,#00e5ff,#7c5cff)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{NAV[idx][0]}</Typography>}
        <Box key={idx} sx={{ animation: 'fadeUp .45s ease both' }}><Page /></Box>
      </Box>
    </Box>
  )
}
