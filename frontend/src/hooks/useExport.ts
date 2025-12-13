import { useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export type ExportFormat = 'markdown' | 'obsidian' | 'remnote'

interface ExportOptions {
  conceptIds: string[]
  includeAnalyses?: boolean
  includeRelationships?: boolean
}

interface RemNoteCard {
  front: string
  back: string
  tags: string[]
}

export function useExport() {
  const [isExporting, setIsExporting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const exportToMarkdown = async (options: ExportOptions): Promise<string | null> => {
    setIsExporting(true)
    setError(null)

    try {
      const response = await axios.post(`${API_URL}/api/export/markdown`, {
        concept_ids: options.conceptIds,
        include_analyses: options.includeAnalyses ?? true,
        include_relationships: options.includeRelationships ?? true,
      })
      return response.data.content
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed'
      setError(message)
      return null
    } finally {
      setIsExporting(false)
    }
  }

  const exportToObsidian = async (options: ExportOptions): Promise<string | null> => {
    setIsExporting(true)
    setError(null)

    try {
      const response = await axios.post(`${API_URL}/api/export/obsidian`, {
        concept_ids: options.conceptIds,
        include_analyses: options.includeAnalyses ?? true,
        include_relationships: options.includeRelationships ?? true,
      })
      return response.data.content
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed'
      setError(message)
      return null
    } finally {
      setIsExporting(false)
    }
  }

  const exportToRemNote = async (options: ExportOptions): Promise<RemNoteCard[] | null> => {
    setIsExporting(true)
    setError(null)

    try {
      const response = await axios.post(`${API_URL}/api/export/remnote`, {
        concept_ids: options.conceptIds,
        include_analyses: options.includeAnalyses ?? true,
      })
      return response.data.cards
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed'
      setError(message)
      return null
    } finally {
      setIsExporting(false)
    }
  }

  const downloadFile = (content: string, filename: string, mimeType: string = 'text/markdown') => {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const downloadJSON = (data: unknown, filename: string) => {
    const content = JSON.stringify(data, null, 2)
    downloadFile(content, filename, 'application/json')
  }

  return {
    exportToMarkdown,
    exportToObsidian,
    exportToRemNote,
    downloadFile,
    downloadJSON,
    isExporting,
    error,
  }
}
