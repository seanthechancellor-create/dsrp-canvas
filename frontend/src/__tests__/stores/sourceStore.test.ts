/**
 * Tests for sourceStore
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { act } from '@testing-library/react'
import axios from 'axios'
import { useSourceStore } from '../../stores/sourceStore'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('sourceStore', () => {
  beforeEach(() => {
    // Reset store state
    useSourceStore.setState({ sources: [], isUploading: false })
    vi.clearAllMocks()
  })

  it('should initialize with empty sources', () => {
    const state = useSourceStore.getState()
    expect(state.sources).toEqual([])
    expect(state.isUploading).toBe(false)
  })

  describe('addSource', () => {
    it('should add source with uploading status', async () => {
      mockedAxios.post.mockResolvedValue({
        data: { source_id: 'server-id', file_path: '/path/to/file' },
      })
      mockedAxios.get.mockResolvedValue({ data: { status: 'ready' } })

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })

      await act(async () => {
        await useSourceStore.getState().addSource(file)
      })

      const state = useSourceStore.getState()
      expect(state.sources.length).toBe(1)
      expect(state.sources[0].name).toBe('test.pdf')
      expect(state.sources[0].type).toBe('pdf')
    })

    it('should detect audio file type', async () => {
      mockedAxios.post.mockResolvedValue({
        data: { source_id: 'server-id', file_path: '/path/to/file' },
      })
      mockedAxios.get.mockResolvedValue({ data: { status: 'ready' } })

      const file = new File(['content'], 'test.mp3', { type: 'audio/mpeg' })

      await act(async () => {
        await useSourceStore.getState().addSource(file)
      })

      const state = useSourceStore.getState()
      expect(state.sources[0].type).toBe('audio')
    })

    it('should detect video file type', async () => {
      mockedAxios.post.mockResolvedValue({
        data: { source_id: 'server-id', file_path: '/path/to/file' },
      })
      mockedAxios.get.mockResolvedValue({ data: { status: 'ready' } })

      const file = new File(['content'], 'test.mp4', { type: 'video/mp4' })

      await act(async () => {
        await useSourceStore.getState().addSource(file)
      })

      const state = useSourceStore.getState()
      expect(state.sources[0].type).toBe('video')
    })

    it('should handle upload error', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Upload failed'))

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })

      await act(async () => {
        await useSourceStore.getState().addSource(file)
      })

      const state = useSourceStore.getState()
      expect(state.sources[0].status).toBe('error')
    })
  })

  describe('updateSource', () => {
    it('should update source properties', () => {
      // Add initial source
      useSourceStore.setState({
        sources: [
          { id: 'test-id', name: 'test.pdf', type: 'pdf', status: 'uploading' },
        ],
      })

      act(() => {
        useSourceStore.getState().updateSource('test-id', { status: 'ready' })
      })

      const state = useSourceStore.getState()
      expect(state.sources[0].status).toBe('ready')
    })

    it('should not update non-existent source', () => {
      useSourceStore.setState({
        sources: [
          { id: 'test-id', name: 'test.pdf', type: 'pdf', status: 'uploading' },
        ],
      })

      act(() => {
        useSourceStore.getState().updateSource('non-existent', { status: 'ready' })
      })

      const state = useSourceStore.getState()
      expect(state.sources[0].status).toBe('uploading')
    })
  })

  describe('removeSource', () => {
    it('should remove source by id', () => {
      useSourceStore.setState({
        sources: [
          { id: 'id1', name: 'file1.pdf', type: 'pdf', status: 'ready' },
          { id: 'id2', name: 'file2.pdf', type: 'pdf', status: 'ready' },
        ],
      })

      act(() => {
        useSourceStore.getState().removeSource('id1')
      })

      const state = useSourceStore.getState()
      expect(state.sources.length).toBe(1)
      expect(state.sources[0].id).toBe('id2')
    })
  })
})
