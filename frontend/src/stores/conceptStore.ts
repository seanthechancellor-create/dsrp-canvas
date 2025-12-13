import { create } from 'zustand'
import axios from 'axios'
import { Concept, DSRPAnalysis } from '../types/dsrp'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ConceptState {
  concepts: Concept[]
  selectedConceptId: string | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchConcepts: () => Promise<void>
  createConcept: (name: string, description?: string) => Promise<Concept | null>
  deleteConcept: (id: string) => Promise<boolean>
  selectConcept: (id: string | null) => void
  getConceptById: (id: string) => Concept | undefined
  addAnalysisResult: (conceptId: string, analysis: DSRPAnalysis) => void
}

export const useConceptStore = create<ConceptState>((set, get) => ({
  concepts: [],
  selectedConceptId: null,
  isLoading: false,
  error: null,

  fetchConcepts: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await axios.get(`${API_URL}/api/concepts/`)
      const concepts = response.data.map((c: Record<string, unknown>) => ({
        id: c.id,
        name: c.name,
        description: c.description,
        sourceIds: c.source_ids || [],
        analyses: [],
        createdAt: new Date(c.created_at as string),
        updatedAt: new Date(c.updated_at as string),
      }))
      set({ concepts, isLoading: false })
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch concepts',
        isLoading: false,
      })
    }
  },

  createConcept: async (name: string, description?: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await axios.post(`${API_URL}/api/concepts/`, {
        name,
        description,
        source_ids: [],
      })

      const newConcept: Concept = {
        id: response.data.id,
        name: response.data.name,
        description: response.data.description,
        sourceIds: [],
        analyses: [],
        createdAt: new Date(response.data.created_at),
        updatedAt: new Date(response.data.updated_at),
      }

      set((state) => ({
        concepts: [...state.concepts, newConcept],
        isLoading: false,
      }))

      return newConcept
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to create concept',
        isLoading: false,
      })
      return null
    }
  },

  deleteConcept: async (id: string) => {
    try {
      await axios.delete(`${API_URL}/api/concepts/${id}`)
      set((state) => ({
        concepts: state.concepts.filter((c) => c.id !== id),
        selectedConceptId:
          state.selectedConceptId === id ? null : state.selectedConceptId,
      }))
      return true
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to delete concept',
      })
      return false
    }
  },

  selectConcept: (id: string | null) => {
    set({ selectedConceptId: id })
  },

  getConceptById: (id: string) => {
    return get().concepts.find((c) => c.id === id)
  },

  addAnalysisResult: (conceptId: string, analysis: DSRPAnalysis) => {
    set((state) => ({
      concepts: state.concepts.map((c) =>
        c.id === conceptId ? { ...c, analyses: [...c.analyses, analysis] } : c
      ),
    }))
  },
}))
