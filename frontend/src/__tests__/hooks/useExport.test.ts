/**
 * Tests for useExport hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import axios from 'axios'
import { useExport } from '../../hooks/useExport'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

// Mock URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = vi.fn(() => 'blob:test-url')
global.URL.revokeObjectURL = vi.fn()

describe('useExport', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useExport())

    expect(result.current.isExporting).toBe(false)
    expect(result.current.error).toBeNull()
  })

  describe('exportToMarkdown', () => {
    it('should export markdown successfully', async () => {
      const mockContent = '# DSRP Export\n\nContent here'
      mockedAxios.post.mockResolvedValue({ data: { content: mockContent } })

      const { result } = renderHook(() => useExport())

      let content: string | null = null
      await act(async () => {
        content = await result.current.exportToMarkdown({ conceptIds: ['id1'] })
      })

      expect(content).toBe(mockContent)
      expect(result.current.isExporting).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('should handle export error', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Export failed'))

      const { result } = renderHook(() => useExport())

      let content: string | null = null
      await act(async () => {
        content = await result.current.exportToMarkdown({ conceptIds: ['id1'] })
      })

      expect(content).toBeNull()
      expect(result.current.error).toBe('Export failed')
    })

    it('should call correct API endpoint', async () => {
      mockedAxios.post.mockResolvedValue({ data: { content: '' } })

      const { result } = renderHook(() => useExport())

      await act(async () => {
        await result.current.exportToMarkdown({
          conceptIds: ['id1', 'id2'],
          includeAnalyses: true,
          includeRelationships: false,
        })
      })

      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/export/markdown',
        {
          concept_ids: ['id1', 'id2'],
          include_analyses: true,
          include_relationships: false,
        }
      )
    })
  })

  describe('exportToObsidian', () => {
    it('should export obsidian format successfully', async () => {
      const mockContent = '# DSRP Export\n\n[[Concept1]]'
      mockedAxios.post.mockResolvedValue({ data: { content: mockContent } })

      const { result } = renderHook(() => useExport())

      let content: string | null = null
      await act(async () => {
        content = await result.current.exportToObsidian({ conceptIds: ['id1'] })
      })

      expect(content).toBe(mockContent)
    })
  })

  describe('exportToRemNote', () => {
    it('should export remnote cards successfully', async () => {
      const mockCards = [
        { front: 'Q1', back: 'A1', tags: ['dsrp'] },
        { front: 'Q2', back: 'A2', tags: ['dsrp'] },
      ]
      mockedAxios.post.mockResolvedValue({ data: { cards: mockCards } })

      const { result } = renderHook(() => useExport())

      let cards = null
      await act(async () => {
        cards = await result.current.exportToRemNote({ conceptIds: ['id1'] })
      })

      expect(cards).toEqual(mockCards)
    })
  })

  describe('downloadFile', () => {
    it('should create and trigger download link', () => {
      const { result } = renderHook(() => useExport())

      // Mock document methods
      const mockLink = {
        href: '',
        download: '',
        click: vi.fn(),
      }
      const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any)
      const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any)
      const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any)

      act(() => {
        result.current.downloadFile('test content', 'test.md')
      })

      expect(createElementSpy).toHaveBeenCalledWith('a')
      expect(mockLink.download).toBe('test.md')
      expect(mockLink.click).toHaveBeenCalled()
      expect(global.URL.revokeObjectURL).toHaveBeenCalled()

      createElementSpy.mockRestore()
      appendChildSpy.mockRestore()
      removeChildSpy.mockRestore()
    })
  })

  describe('downloadJSON', () => {
    it('should download JSON data', () => {
      const { result } = renderHook(() => useExport())

      const mockLink = {
        href: '',
        download: '',
        click: vi.fn(),
      }
      const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any)
      const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any)
      const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any)

      act(() => {
        result.current.downloadJSON({ test: 'data' }, 'test.json')
      })

      expect(mockLink.download).toBe('test.json')
      expect(mockLink.click).toHaveBeenCalled()

      createElementSpy.mockRestore()
      appendChildSpy.mockRestore()
      removeChildSpy.mockRestore()
    })
  })
})
