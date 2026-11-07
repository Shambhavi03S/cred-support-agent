import { Alert, Box, Card, CardContent, CircularProgress, Typography } from '@mui/material'

export function Stat({ label, value, color = 'primary.main' }) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="caption" color="text.secondary">{label}</Typography>
        <Typography variant="h4" sx={{ color, fontWeight: 600 }}>{value ?? '–'}</Typography>
      </CardContent>
    </Card>
  )
}

export function Panel({ title, children, sx }) {
  return (
    <Card variant="outlined" sx={{ height: '100%', ...sx }}>
      <CardContent>
        {title && <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1.5 }}>{title}</Typography>}
        {children}
      </CardContent>
    </Card>
  )
}

export function State({ loading, error, children }) {
  if (loading) return <Box sx={{ p: 3 }}><CircularProgress size={24} /></Box>
  if (error) return <Alert severity="error">Backend error: {error}</Alert>
  return children
}

export const money = (n) => `INR ${Number(n).toLocaleString('en-IN')}`
