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
    <Box sx={{ bgcolor: '#0b2545', color: '#fff', height: '100%' }}>
      <Toolbar sx={{ py: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, letterSpacing: 0.5, lineHeight: 1.25 }}>
          CRED DOMAIN<br />SUPPORT AGENT
        </Typography>
      </Toolbar>
      <List>
        {NAV.map(([label, Icon], i) => (
          <ListItemButton key={label} selected={i === idx} onClick={() => { setIdx(i); setOpen(false) }}
            sx={{ color: '#c9d6e8', '&.Mui-selected': { bgcolor: '#173a6a', color: '#fff' }, '&:hover': { bgcolor: '#14335c' } }}>
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
        {wide && <Typography variant="h5" sx={{ mb: 2, color: 'primary.main' }}>{NAV[idx][0]}</Typography>}
        <Page />
      </Box>
    </Box>
  )
}
