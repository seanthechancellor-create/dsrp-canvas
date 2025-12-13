/**
 * Tests for conceptStore
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { act } from '@testing-library/react'
import axios from 'axios'
import { useConceptStore } from '../../stores/conceptStore'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('conceptStore', () => {
  beforeEach(() => {
    // Reset store state
    useConceptStore.setState({
      concepts: [],
      selectedConceptId: null,
      isLoading: false,
      error: null,
    })
    vi.clearAllMocks()
  })

  it('should initialize with empty state', () => {
    const state = useConceptStore.getState()
    expect(state.concepts).toEqual([])
    expect(state.selectedConceptId).toBeNull()
    expect(state.isLoading).toBe(false)
    expect(state.error).toBeNull()
  })

  describe('fetchConcepts', () => {
    it('should fetch and store concepts', async () => {
      const mockConcepts = [
        {
          id: 'id1',
          name: 'Concept 1',
          description: 'Description 1',
          source_ids: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'id2',
          name: 'Concept 2',
          description: null,
          source_ids: [],
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      ]

      mockedAxios.get.mockResolvedValue({ data: mockConcepts })

      await act(async () => {
        await useConceptStore.getState().fetchConcepts()
      })

      const state = useConceptStore.getState()
      expect(state.concepts.length).toBe(2)
      expect(state.concepts[0].name).toBe('Concept 1')
      expect(state.isLoading).toBe(false)
    })

    it('should handle fetch error', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'))

      await act(async () => {
        await useConceptStore.getState().fetchConcepts()
      })

      const state = useConceptStore.getState()
      expect(state.error).toBe('Network error')
      expect(state.isLoading).toBe(false)
    })
  })

  describe('createConcept', () => {
    it('should create and add concept', async () => {
      const mockResponse = {
        id: 'new-id',
        name: 'New Concept',
        description: 'New description',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      mockedAxios.post.mockResolvedValue({ data: mockResponse })

      let newConcept = null
      await act(async () => {
        newConcept = await useConceptStore.getState().createConcept('New Concept', 'New description')
      })

      const state = useConceptStore.getState()
      expect(state.concepts.length).toBe(1)
      expect(state.concepts[0].name).toBe('New Concept')
      expect(newConcept).not.toBeNull()
    })

    it('should handle create error', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Create failed'))

      let result = null
      await act(async () => {
        result = await useConceptStore.getState().createConcept('Test', 'Desc')
      })

      expect(result).toBeNull()
      const state = useConceptStore.getState()
      expect(state.error).toBe('Create failed')
    })
  })

  describe('deleteConcept', () => {
    it('should delete concept from store', async () => {
      useConceptStore.setState({
        concepts: [
          { id: 'id1', name: 'C1', sourceIds: [], analyses: [], createdAt: new Date(), updatedAt: new Date() },
          { id: 'id2', name: 'C2', sourceIds: [], analyses: [], createdAt: new Date(), updatedAt: new Date() },
        ],
      })

      mockedAxios.delete.mockResolvedValue({})

      await act(async () => {
        await useConceptStore.getState().deleteConcept('id1')
      })

      const state = useConceptStore.getState()
      expect(state.concepts.length).toBe(1)
      expect(state.concepts[0].id).toBe('id2')
    })

    it('should clear selection if deleted concept was selected', async () => {
      useConceptStore.setState({
        concepts: [
          { id: 'id1', name: 'C1', sourceIds: [], analyses: [], createdAt: new Date(), updatedAt: new Date() },
        ],
        selectedConceptId: 'id1',
      })

      mockedAxios.delete.mockResolvedValue({})

      await act(async () => {
        await useConceptStore.getState().deleteConcept('id1')
      })

      const state = useConceptStore.getState()
      expect(state.selectedConceptId).toBeNull()
    })
  })

  describe('selectConcept', () => {
    it('should select concept by id', () => {
      act(() => {
        useConceptStore.getState().selectConcept('test-id')
      })

      expect(useConceptStore.getState().selectedConceptId).toBe('test-id')
    })

    it('should clear selection with null', () => {
      useConceptStore.setState({ selectedConceptId: 'some-id' })

      act(() => {
        useConceptStore.getState().selectConcept(null)
      })

      expect(useConceptStore.getState().selectedConceptId).toBeNull()
    })
  })

  describe('getConceptById', () => {
    it('should return concept by id', () => {
      useConceptStore.setState({
        concepts: [
          { id: 'id1', name: 'C1', sourceIds: [], analyses: [], createdAt: new Date(), updatedAt: new Date() },
          { id: 'id2', name: 'C2', sourceIds: [], analyses: [], createdAt: new Date(), updatedAt: new Date() },
        ],
      })

      const concept = useConceptStore.getState().getConceptById('id1')
      expect(concept?.name).toBe('C1')
    })

    it('should return undefined for non-existent id', () => {
      const concept = useConceptStore.getState().getConceptById('non-existent')
      expect(concept).toBeUndefined()
    })
  })

  describe('addAnalysisResult', () => {
    it('should add analysis to correct concept', () => {
      useConceptStore.setState({
        concepts: [
          { id: 'id1', name: 'C1', sourceIds: [], analyses: [], createdAt: new Date(), updatedAt: new Date() },
        ],
      })

      const analysis = {
        id: 'analysis-1',
        conceptId: 'id1',
        pattern: 'D' as const,
        elementType: 'identity' as const,
        move: 'is-is-not' as const,
        reasoning: 'Test reasoning',
        confidenceScore: 0.85,
        createdAt: new Date(),
      }

      act(() => {
        useConceptStore.getState().addAnalysisResult('id1', analysis)
      })

      const state = useConceptStore.getState()
      expect(state.concepts[0].analyses.length).toBe(1)
      expect(state.concepts[0].analyses[0].move).toBe('is-is-not')
    })
  })
})
