import { create } from 'zustand'
import axios from 'axios'

export interface ExtractedConcept {
  name: string
  description: string
  suggested_move: string
  importance: string
}

export interface Source {
  id: string
  remoteId?: string
  name: string
  type: 'pdf' | 'audio' | 'video'
  status: 'uploading' | 'processing' | 'ready' | 'error'
  filePath?: string
  extractedText?: string
  concepts?: ExtractedConcept[]
  sourceSummary?: string
  mainTheme?: string
}

interface SourceState {
  sources: Source[]
  isUploading: boolean
  onConceptsExtracted?: (sourceId: string, concepts: ExtractedConcept[]) => void
  addSource: (file: File) => Promise<void>
  updateSource: (id: string, updates: Partial<Source>) => void
  removeSource: (id: string) => void
  setOnConceptsExtracted: (callback: (sourceId: string, concepts: ExtractedConcept[]) => void) => void
}

const API_URL = import.meta.env.VITE_API_URL || ''

export const useSourceStore = create<SourceState>((set, get) => ({
  sources: [],
  isUploading: false,
  onConceptsExtracted: undefined,

  addSource: async (file: File) => {
    const id = crypto.randomUUID()
    const type = getFileType(file.name)

    // Add source with uploading status
    set((state) => ({
      sources: [...state.sources, { id, name: file.name, type, status: 'uploading' }],
      isUploading: true,
    }))

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`${API_URL}/api/sources/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      get().updateSource(id, {
        status: 'processing',
        filePath: response.data.file_path,
        remoteId: response.data.source_id,
      })

      // Poll for processing completion
      pollProcessingStatus(id, response.data.source_id, get().updateSource, get)
    } catch (error) {
      console.error('Upload failed:', error)
      get().updateSource(id, { status: 'error' })
    } finally {
      set({ isUploading: false })
    }
  },

  updateSource: (id, updates) => {
    set((state) => ({
      sources: state.sources.map((s) => (s.id === id ? { ...s, ...updates } : s)),
    }))
  },

  removeSource: (id) => {
    set((state) => ({
      sources: state.sources.filter((s) => s.id !== id),
    }))
  },

  setOnConceptsExtracted: (callback) => {
    set({ onConceptsExtracted: callback })
  },
}))

function getFileType(filename: string): Source['type'] {
  const ext = filename.split('.').pop()?.toLowerCase()
  if (ext === 'pdf') return 'pdf'
  if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext || '')) return 'audio'
  if (['mp4', 'webm', 'mov', 'avi'].includes(ext || '')) return 'video'
  return 'pdf' // default
}

async function pollProcessingStatus(
  localId: string,
  remoteId: string,
  updateSource: (id: string, updates: Partial<Source>) => void,
  getState: () => SourceState
) {
  const maxAttempts = 60
  let attempts = 0

  const poll = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/sources/${remoteId}/status`)

      if (response.data.status === 'ready') {
        updateSource(localId, {
          status: 'ready',
          extractedText: response.data.extracted_text,
        })

        // Fetch extracted concepts
        try {
          const conceptsResponse = await axios.get(`${API_URL}/api/sources/${remoteId}/concepts`)
          if (conceptsResponse.data.status === 'ready' && conceptsResponse.data.concepts?.length > 0) {
            updateSource(localId, {
              concepts: conceptsResponse.data.concepts,
              sourceSummary: conceptsResponse.data.source_summary,
              mainTheme: conceptsResponse.data.main_theme,
            })

            // Notify callback
            const callback = getState().onConceptsExtracted
            if (callback) {
              callback(localId, conceptsResponse.data.concepts)
            }
          }
        } catch (err) {
          console.log('Concepts not yet available, will retry...')
          // Retry fetching concepts a few more times
          setTimeout(() => fetchConceptsWithRetry(localId, remoteId, updateSource, getState, 5), 3000)
        }
        return
      }

      if (response.data.status === 'error') {
        updateSource(localId, { status: 'error' })
        return
      }
    } catch (error) {
      console.error('Status poll failed:', error)
    }

    attempts++
    if (attempts < maxAttempts) {
      setTimeout(poll, 2000)
    } else {
      updateSource(localId, { status: 'error' })
    }
  }

  poll()
}

async function fetchConceptsWithRetry(
  localId: string,
  remoteId: string,
  updateSource: (id: string, updates: Partial<Source>) => void,
  getState: () => SourceState,
  retriesLeft: number
) {
  if (retriesLeft <= 0) return

  try {
    const conceptsResponse = await axios.get(`${API_URL}/api/sources/${remoteId}/concepts`)
    if (conceptsResponse.data.status === 'ready' && conceptsResponse.data.concepts?.length > 0) {
      updateSource(localId, {
        concepts: conceptsResponse.data.concepts,
        sourceSummary: conceptsResponse.data.source_summary,
        mainTheme: conceptsResponse.data.main_theme,
      })

      // Notify callback
      const callback = getState().onConceptsExtracted
      if (callback) {
        callback(localId, conceptsResponse.data.concepts)
      }
    }
  } catch (err) {
    setTimeout(() => fetchConceptsWithRetry(localId, remoteId, updateSource, getState, retriesLeft - 1), 3000)
  }
}
