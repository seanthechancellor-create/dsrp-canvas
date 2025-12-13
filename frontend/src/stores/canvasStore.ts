import { create } from 'zustand'
import { Editor } from '@tldraw/tldraw'

interface CanvasState {
  editor: Editor | null
  setEditor: (editor: Editor) => void
  selectedShapeIds: string[]
  setSelectedShapeIds: (ids: string[]) => void
}

export const useCanvasStore = create<CanvasState>((set) => ({
  editor: null,
  setEditor: (editor) => set({ editor }),
  selectedShapeIds: [],
  setSelectedShapeIds: (ids) => set({ selectedShapeIds: ids }),
}))
