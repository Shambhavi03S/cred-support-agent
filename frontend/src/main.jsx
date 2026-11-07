import React from 'react'
import { createRoot } from 'react-dom/client'
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import App from './App.jsx'

const theme = createTheme({
  palette: {
    primary: { main: '#0b2545' },
    secondary: { main: '#1d6fb8' },
    background: { default: '#f3f5f8', paper: '#ffffff' },
  },
  typography: { fontFamily: '"Inter","Segoe UI",Roboto,Arial,sans-serif', h5: { fontWeight: 600 } },
  shape: { borderRadius: 6 },
})

createRoot(document.getElementById('root')).render(
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <App />
  </ThemeProvider>,
)
