import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Category {
  id: string
  name: string
  color: string
  topics: string[]
  count: number
  isCustom: boolean
}

interface CategoryState {
  categories: Category[]
  isLoading: boolean
  error: string | null

  // Actions
  addCategory: (name: string, color: string) => Category
  updateCategory: (id: string, updates: Partial<Omit<Category, 'id'>>) => void
  deleteCategory: (id: string) => void
  addTopic: (categoryId: string, topic: string) => void
  removeTopic: (categoryId: string, topic: string) => void
  incrementCount: (categoryId: string) => void
  fetchFromBackend: () => Promise<void>
  syncToBackend: () => Promise<void>
}

// Default color palette for new categories
export const CATEGORY_COLORS = [
  '#1976D2', // Blue
  '#D32F2F', // Red
  '#388E3C', // Green
  '#7B1FA2', // Purple
  '#F57C00', // Orange
  '#00796B', // Teal
  '#C2185B', // Pink
  '#5D4037', // Brown
  '#455A64', // Blue Grey
  '#FBC02D', // Yellow
]

const API_URL = import.meta.env.VITE_API_URL || ''

export const useCategoryStore = create<CategoryState>()(
  persist(
    (set, get) => ({
      categories: [],
      isLoading: false,
      error: null,

      addCategory: (name: string, color: string) => {
        const id = `cat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        const newCategory: Category = {
          id,
          name,
          color,
          topics: [],
          count: 0,
          isCustom: true,
        }

        set((state) => ({
          categories: [...state.categories, newCategory],
        }))

        // Sync to backend
        get().syncToBackend()

        return newCategory
      },

      updateCategory: (id: string, updates: Partial<Omit<Category, 'id'>>) => {
        set((state) => ({
          categories: state.categories.map((cat) =>
            cat.id === id ? { ...cat, ...updates } : cat
          ),
        }))
        get().syncToBackend()
      },

      deleteCategory: (id: string) => {
        set((state) => ({
          categories: state.categories.filter((cat) => cat.id !== id),
        }))
        get().syncToBackend()
      },

      addTopic: (categoryId: string, topic: string) => {
        set((state) => ({
          categories: state.categories.map((cat) =>
            cat.id === categoryId && !cat.topics.includes(topic)
              ? { ...cat, topics: [...cat.topics, topic] }
              : cat
          ),
        }))
        get().syncToBackend()
      },

      removeTopic: (categoryId: string, topic: string) => {
        set((state) => ({
          categories: state.categories.map((cat) =>
            cat.id === categoryId
              ? { ...cat, topics: cat.topics.filter((t) => t !== topic) }
              : cat
          ),
        }))
        get().syncToBackend()
      },

      incrementCount: (categoryId: string) => {
        set((state) => ({
          categories: state.categories.map((cat) =>
            cat.id === categoryId ? { ...cat, count: cat.count + 1 } : cat
          ),
        }))
      },

      fetchFromBackend: async () => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${API_URL}/api/categories/`)
          if (response.ok) {
            const data = await response.json()
            if (data.categories && data.categories.length > 0) {
              set({ categories: data.categories, isLoading: false })
            } else {
              set({ isLoading: false })
            }
          } else {
            set({ isLoading: false })
          }
        } catch (err) {
          console.log('Backend categories not available, using local storage')
          set({ isLoading: false })
        }
      },

      syncToBackend: async () => {
        try {
          const { categories } = get()
          await fetch(`${API_URL}/api/categories/`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ categories }),
          })
        } catch (err) {
          // Silently fail - local storage is the primary store
          console.log('Backend sync skipped')
        }
      },
    }),
    {
      name: 'dsrp-categories',
      partialize: (state) => ({ categories: state.categories }),
    }
  )
)
