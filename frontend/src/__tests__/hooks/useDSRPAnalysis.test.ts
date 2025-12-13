/**
 * Tests for useDSRPAnalysis hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import axios from 'axios'
import { useDSRPAnalysis } from '../../hooks/useDSRPAnalysis'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('useDSRPAnalysis', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useDSRPAnalysis())

    expect(result.current.isAnalyzing).toBe(false)
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('should set isAnalyzing to true during analysis', async () => {
    mockedAxios.post.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ data: {} }), 100))
    )

    const { result } = renderHook(() => useDSRPAnalysis())

    act(() => {
      result.current.analyze('Democracy', 'is-is-not')
    })

    expect(result.current.isAnalyzing).toBe(true)
  })

  it('should set result on successful analysis', async () => {
    const mockResult = {
      pattern: 'D',
      elements: { identity: 'test', other: 'test' },
      move: 'is-is-not',
      reasoning: 'Test reasoning',
      relatedConcepts: [],
      confidence: 0.85,
    }

    mockedAxios.post.mockResolvedValue({ data: mockResult })

    const { result } = renderHook(() => useDSRPAnalysis())

    await act(async () => {
      await result.current.analyze('Democracy', 'is-is-not')
    })

    expect(result.current.result).toEqual(mockResult)
    expect(result.current.isAnalyzing).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should set error on failed analysis', async () => {
    mockedAxios.post.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useDSRPAnalysis())

    await act(async () => {
      await result.current.analyze('Democracy', 'is-is-not')
    })

    expect(result.current.error).toBe('Network error')
    expect(result.current.result).toBeNull()
    expect(result.current.isAnalyzing).toBe(false)
  })

  it('should call correct API endpoint', async () => {
    mockedAxios.post.mockResolvedValue({ data: {} })

    const { result } = renderHook(() => useDSRPAnalysis())

    await act(async () => {
      await result.current.analyze('Test Concept', 'zoom-in')
    })

    expect(mockedAxios.post).toHaveBeenCalledWith(
      'http://localhost:8000/api/analysis/dsrp',
      { concept: 'Test Concept', move: 'zoom-in' }
    )
  })

  it('should clear results and error', async () => {
    mockedAxios.post.mockResolvedValue({
      data: { pattern: 'D', elements: {}, move: 'is-is-not', reasoning: '' },
    })

    const { result } = renderHook(() => useDSRPAnalysis())

    // First, analyze something
    await act(async () => {
      await result.current.analyze('Democracy', 'is-is-not')
    })

    expect(result.current.result).not.toBeNull()

    // Then clear
    act(() => {
      result.current.clear()
    })

    expect(result.current.result).toBeNull()
    expect(result.current.error).toBeNull()
  })
})
