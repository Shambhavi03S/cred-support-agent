import React from 'react'
import { createRoot } from 'react-dom/client'
import { CssBaseline, GlobalStyles, ThemeProvider, createTheme } from '@mui/material'
import App from './App.jsx'

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#7c5cff' },
    secondary: { main: '#00e5ff' },
    success: { main: '#2ee59d' },
    warning: { main: '#ffb547' },
    error: { main: '#ff5d7a' },
    background: { default: '#070b1f', paper: 'rgba(20,26,58,0.72)' },
    text: { primary: '#eaf0ff', secondary: '#9fb0d9' },
  },
  typography: { fontFamily: '"Inter","Segoe UI",Roboto,Arial,sans-serif', h5: { fontWeight: 700 } },
  shape: { borderRadius: 14 },
  components: {
    MuiCard: { styleOverrides: { root: { backgroundImage: 'none', backdropFilter: 'blur(14px)', border: '1px solid rgba(124,92,255,0.25)' } } },
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
    MuiButton: { styleOverrides: { root: { textTransform: 'none', fontWeight: 600 } } },
  },
})

const globalCss = {
  body: {
    background: 'radial-gradient(900px 600px at 10% -10%, rgba(124,92,255,0.35), transparent 60%),' +
      'radial-gradient(800px 600px at 100% 0%, rgba(0,229,255,0.22), transparent 55%),' +
      'radial-gradient(700px 500px at 50% 110%, rgba(255,93,122,0.18), transparent 60%), #070b1f',
    backgroundAttachment: 'fixed',
  },
  '@keyframes fadeUp': { from: { opacity: 0, transform: 'translateY(14px)' }, to: { opacity: 1, transform: 'none' } },
  '@keyframes pulse': { '0%,100%': { boxShadow: '0 0 0 0 rgba(46,229,157,0.7)' }, '50%': { boxShadow: '0 0 0 9px rgba(46,229,157,0)' } },
  '@keyframes glow': { '0%,100%': { boxShadow: '0 0 12px rgba(124,92,255,0.5)' }, '50%': { boxShadow: '0 0 26px rgba(0,229,255,0.7)' } },
  '@keyframes bounce': { '0%,80%,100%': { transform: 'scale(0.5)', opacity: 0.4 }, '40%': { transform: 'scale(1)', opacity: 1 } },
  '@keyframes shimmer': { from: { backgroundPosition: '0% 50%' }, to: { backgroundPosition: '200% 50%' } },
  '@keyframes pop': { from: { opacity: 0, transform: 'scale(0.6)' }, to: { opacity: 1, transform: 'scale(1)' } },
  '.recharts-text, .recharts-cartesian-axis-tick-value': { fill: '#9fb0d9' },
  '.recharts-cartesian-grid line': { stroke: 'rgba(159,176,217,0.18)' },
  '::-webkit-scrollbar': { width: 8 },
  '::-webkit-scrollbar-thumb': { background: 'rgba(124,92,255,0.5)', borderRadius: 8 },
}

createRoot(document.getElementById('root')).render(
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <GlobalStyles styles={globalCss} />
    <App />
  </ThemeProvider>,
)
