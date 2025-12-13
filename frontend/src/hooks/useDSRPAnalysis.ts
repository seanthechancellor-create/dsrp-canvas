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

export function useDSRPAnalysis() {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState<DSRPResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const analyze = async (concept: string, move: string) => {
    setIsAnalyzing(true)
    setError(null)

    try {
      const response = await axios.post(`${API_URL}/api/analysis/dsrp`, {
        concept,
        move,
      })
      setResult(response.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
      setResult(null)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const clear = () => {
    setResult(null)
    setError(null)
  }

  return { analyze, isAnalyzing, result, error, clear }
}
