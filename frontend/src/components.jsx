import { useEffect, useState } from 'react'
import { Alert, Box, Card, CardContent, CircularProgress, Typography } from '@mui/material'

// Animated count-up for numeric stat values.
function useCountUp(target, ms = 900) {
  const [v, setV] = useState(0)
  useEffect(() => {
    if (typeof target !== 'number') return
    let raf, t0
    const step = (t) => {
      t0 ??= t
      const p = Math.min((t - t0) / ms, 1)
      setV(Math.round(target * (1 - Math.pow(1 - p, 3))))
      if (p < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [target, ms])
  return typeof target === 'number' ? v : target
}

export function Stat({ label, value, color = 'secondary.main' }) {
  const shown = useCountUp(value)
  return (
    <Card sx={{
      height: '100%', animation: 'fadeUp .6s ease both', transition: 'transform .25s, box-shadow .25s',
      '&:hover': { transform: 'translateY(-5px)', boxShadow: '0 12px 34px rgba(124,92,255,0.45)' },
      position: 'relative', overflow: 'hidden',
      '&::before': { content: '""', position: 'absolute', inset: '0 0 auto 0', height: 3,
        background: 'linear-gradient(90deg,#7c5cff,#00e5ff,#ff5d7a)', backgroundSize: '200% 100%', animation: 'shimmer 3s linear infinite' },
    }}>
      <CardContent>
        <Typography variant="caption" color="text.secondary">{label}</Typography>
        <Typography variant="h3" sx={{ color, fontWeight: 800, textShadow: '0 0 18px currentColor' }}>{shown ?? '–'}</Typography>
      </CardContent>
    </Card>
  )
}

export function Panel({ title, children, sx }) {
  return (
    <Card sx={{ height: '100%', animation: 'fadeUp .6s ease both', ...sx }}>
      <CardContent>
        {title && <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1.5, color: 'secondary.main' }}>{title}</Typography>}
        {children}
      </CardContent>
    </Card>
  )
}

export function State({ loading, error, children }) {
  if (loading) return <Box sx={{ p: 3 }}><CircularProgress size={28} color="secondary" /></Box>
  if (error) return <Alert severity="error">Backend error: {error}</Alert>
  return children
}

export const money = (n) => `INR ${Number(n).toLocaleString('en-IN')}`
