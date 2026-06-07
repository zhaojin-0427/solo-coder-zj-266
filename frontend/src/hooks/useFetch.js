import { useState, useEffect, useCallback } from 'react'
import { useApiRequest } from './useApiRequest.js'

export function useFetch(apiFn, deps = [], options = {}) {
  const [data, setData] = useState(null)
  const { loading, error, request } = useApiRequest()

  const fetchData = useCallback(async () => {
    const result = await request(apiFn(), {
      showErrorToast: options.showErrorToast ?? false,
      ...options,
    })
    if (result.success) {
      const payload = result.data.results || result.data
      setData(payload)
      if (options.onSuccess) {
        options.onSuccess(payload)
      }
    }
    return result
  }, [apiFn, request, options])

  useEffect(() => {
    fetchData()
  }, deps)

  return { data, loading, error, refresh: fetchData, setData }
}

export default useFetch
