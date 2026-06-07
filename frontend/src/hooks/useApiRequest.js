import { useState, useCallback } from 'react'
import { useToast } from '../components/Toast.jsx'

export function useApiRequest() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const toast = useToast()

  const request = useCallback(
    async (apiFn, options = {}) => {
      const {
        showErrorToast = true,
        showSuccessToast = false,
        successMessage = '操作成功',
        errorMessage = '操作失败',
      } = options

      setLoading(true)
      setError(null)

      try {
        const result = await apiFn
        setLoading(false)
        if (showSuccessToast) {
          toast.success(successMessage)
        }
        return { data: result.data, success: true, error: null }
      } catch (err) {
        setLoading(false)
        const errMsg =
          err?.response?.data?.detail ||
          err?.response?.data?.error ||
          err?.response?.data?.message ||
          err?.message ||
          errorMessage
        setError(errMsg)
        if (showErrorToast) {
          toast.error(errMsg)
        }
        return { data: null, success: false, error: errMsg }
      }
    },
    [toast]
  )

  const reset = useCallback(() => {
    setLoading(false)
    setError(null)
  }, [])

  return { loading, error, request, reset }
}

export default useApiRequest
