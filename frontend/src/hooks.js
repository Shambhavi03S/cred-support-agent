import { useCallback, useEffect, useState } from 'react'
import { api, errMsg } from './api'

/** GET helper with loading / error state. Data always comes from the live backend. */
export function useGet(url, params, deps = []) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const load = useCallback(() => {
    setLoading(true)
    api.get(url, { params })
      .then((r) => { setData(r.data); setError(null) })
      .catch((e) => setError(errMsg(e)))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, JSON.stringify(params), ...deps])
  useEffect(() => { load() }, [load])
  return { data, error, loading, reload: load }
}
