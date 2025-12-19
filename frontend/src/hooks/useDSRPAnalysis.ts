import { useState } from 'react'
import axios from 'axios'

interface DSRPResult {
  pattern: string
  elements: Record<string, string>
  move: string
  reasoning: string
  relatedConcepts: string[]
  confidence: number
}

// Use relative URL to go through Vite proxy, fallback to direct backend URL
const API_URL = import.meta.env.VITE_API_URL || ''

// Default to REAL AI mode (mock only if explicitly set VITE_USE_MOCK=true)
const DEFAULT_USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export function useDSRPAnalysis() {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState<DSRPResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [useMock, setUseMock] = useState(DEFAULT_USE_MOCK)
  const [aiProvider, setAiProvider] = useState<string | null>(null)

  const analyze = async (concept: string, move: string) => {
    setIsAnalyzing(true)
    setError(null)

    // Choose endpoint: mock for testing, dsrp for real AI analysis
    const endpoint = useMock ? '/api/analysis/mock' : '/api/analysis/dsrp'
    const fullUrl = `${API_URL}${endpoint}`

    console.log('[DSRP] Analyzing:', { concept, move, useMock, endpoint: fullUrl })

    try {
      const response = await axios.post(fullUrl, {
        concept,
        move,
      })
      console.log('[DSRP] Response:', response.data)
      setResult(response.data)
      // Capture which AI provider was used
      if (response.data?.provider) {
        setAiProvider(response.data.provider)
      }
    } catch (err: any) {
      console.error('[DSRP] Error:', err)
      // If real API fails with auth error, suggest mock mode
      const message = err?.response?.data?.detail || err?.message || 'Analysis failed'
      if (message.includes('401') || message.includes('authentication') || message.includes('API key')) {
        setError('API key not configured. Enable Mock Mode to test.')
      } else {
        setError(message)
      }
      setResult(null)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const clear = () => {
    setResult(null)
    setError(null)
  }

  const toggleMock = () => {
    setUseMock(prev => !prev)
  }

  return { analyze, isAnalyzing, result, error, clear, useMock, toggleMock, aiProvider }
}
