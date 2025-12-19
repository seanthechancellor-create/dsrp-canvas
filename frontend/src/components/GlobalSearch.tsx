import { useState, useCallback, useRef, useEffect } from 'react'

interface SearchResult {
  id: string
  name: string | null
  content: string
  similarity: number
  type: 'concept' | 'analysis' | 'source'
  metadata?: Record<string, unknown>
}

interface SearchResponse {
  query: string
  results: SearchResult[]
  total: number
  by_type: Record<string, number>
}

interface GlobalSearchProps {
  onResultSelect?: (result: SearchResult) => void
  placeholder?: string
}

const API_URL = import.meta.env.VITE_API_URL || ''

export function GlobalSearch({ onResultSelect, placeholder = 'Search concepts, analyses...' }: GlobalSearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set(['concept', 'analysis', 'source']))
  const [byType, setByType] = useState<Record<string, number>>({})

  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Keyboard shortcut (Cmd/Ctrl + K)
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault()
        inputRef.current?.focus()
        setIsOpen(true)
      }
      if (event.key === 'Escape') {
        setIsOpen(false)
        inputRef.current?.blur()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const performSearch = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setResults([])
      setByType({})
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const types = Array.from(selectedTypes).join(',')
      const response = await fetch(
        `${API_URL}/api/search?q=${encodeURIComponent(searchQuery)}&types=${types}&limit=20&threshold=0.4`
      )

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`)
      }

      const data: SearchResponse = await response.json()
      setResults(data.results)
      setByType(data.by_type)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }, [selectedTypes])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)
    setIsOpen(true)

    // Debounce search
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }
    debounceRef.current = setTimeout(() => {
      performSearch(value)
    }, 300)
  }, [performSearch])

  const handleResultClick = useCallback((result: SearchResult) => {
    onResultSelect?.(result)
    setIsOpen(false)
    // Keep the query visible so user can see what they searched for
  }, [onResultSelect])

  const toggleType = useCallback((type: string) => {
    setSelectedTypes(prev => {
      const next = new Set(prev)
      if (next.has(type)) {
        if (next.size > 1) next.delete(type)
      } else {
        next.add(type)
      }
      return next
    })
  }, [])

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'concept': return '#4ecdc4'
      case 'analysis': return '#e94560'
      case 'source': return '#f39c12'
      default: return '#888'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'concept': return 'C'
      case 'analysis': return 'A'
      case 'source': return 'S'
      default: return '?'
    }
  }

  return (
    <div className="global-search" ref={containerRef}>
      <div className="search-input-container">
        <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className="search-input"
        />
        <span className="search-shortcut">
          <kbd>{navigator.platform.includes('Mac') ? '⌘' : 'Ctrl'}</kbd>
          <kbd>K</kbd>
        </span>
      </div>

      {isOpen && (
        <div className="search-dropdown">
          {/* Type filters */}
          <div className="type-filters">
            {['concept', 'analysis', 'source'].map(type => (
              <button
                key={type}
                className={`type-filter ${selectedTypes.has(type) ? 'active' : ''}`}
                onClick={() => toggleType(type)}
                style={{
                  borderColor: selectedTypes.has(type) ? getTypeColor(type) : 'transparent',
                  color: selectedTypes.has(type) ? getTypeColor(type) : 'rgba(255,255,255,0.5)'
                }}
              >
                {type}
                {byType[type] !== undefined && <span className="type-count">{byType[type]}</span>}
              </button>
            ))}
          </div>

          {/* Results */}
          <div className="search-results">
            {isLoading && (
              <div className="search-loading">
                <div className="spinner" />
                Searching...
              </div>
            )}

            {error && (
              <div className="search-error">{error}</div>
            )}

            {!isLoading && !error && results.length === 0 && query.length >= 2 && (
              <div className="search-empty">No results found for "{query}"</div>
            )}

            {!isLoading && results.map(result => (
              <button
                key={result.id}
                className="search-result"
                onClick={() => handleResultClick(result)}
              >
                <span
                  className="result-type-badge"
                  style={{ background: getTypeColor(result.type) }}
                >
                  {getTypeIcon(result.type)}
                </span>
                <div className="result-content">
                  <div className="result-name">
                    {result.name || result.id}
                  </div>
                  <div className="result-preview">
                    {result.content.slice(0, 120)}...
                  </div>
                </div>
                <span className="result-similarity">
                  {Math.round(result.similarity * 100)}%
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      <style>{`
        .global-search {
          position: relative;
          width: 100%;
        }

        .search-input-container {
          display: flex;
          align-items: center;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          padding: 8px 12px;
          gap: 8px;
          transition: all 0.2s;
        }

        .search-input-container:focus-within {
          border-color: #e94560;
          background: rgba(255, 255, 255, 0.08);
        }

        .search-icon {
          width: 16px;
          height: 16px;
          color: rgba(255, 255, 255, 0.4);
          flex-shrink: 0;
        }

        .search-input {
          flex: 1;
          background: none;
          border: none;
          color: white;
          font-size: 13px;
          outline: none;
          font-family: inherit;
        }

        .search-input::placeholder {
          color: rgba(255, 255, 255, 0.4);
        }

        .search-shortcut {
          display: flex;
          gap: 2px;
        }

        .search-shortcut kbd {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          padding: 2px 5px;
          font-size: 10px;
          color: rgba(255, 255, 255, 0.5);
          font-family: inherit;
        }

        .search-dropdown {
          position: absolute;
          top: calc(100% + 8px);
          left: 0;
          right: 0;
          background: rgba(22, 33, 62, 0.98);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
          z-index: 1000;
          overflow: hidden;
          backdrop-filter: blur(12px);
        }

        .type-filters {
          display: flex;
          gap: 6px;
          padding: 10px 12px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .type-filter {
          background: transparent;
          border: 1px solid transparent;
          border-radius: 4px;
          padding: 4px 10px;
          font-size: 11px;
          cursor: pointer;
          transition: all 0.15s;
          display: flex;
          align-items: center;
          gap: 6px;
          font-family: inherit;
        }

        .type-filter:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .type-count {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          padding: 1px 5px;
          font-size: 10px;
        }

        .search-results {
          max-height: 320px;
          overflow-y: auto;
        }

        .search-loading,
        .search-error,
        .search-empty {
          padding: 20px;
          text-align: center;
          color: rgba(255, 255, 255, 0.5);
          font-size: 13px;
        }

        .search-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.2);
          border-top-color: #e94560;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .search-error {
          color: #f44336;
        }

        .search-result {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 12px;
          width: 100%;
          background: transparent;
          border: none;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          cursor: pointer;
          text-align: left;
          transition: background 0.15s;
          color: white;
          font-family: inherit;
        }

        .search-result:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .search-result:last-child {
          border-bottom: none;
        }

        .result-type-badge {
          width: 22px;
          height: 22px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: 600;
          flex-shrink: 0;
          color: white;
        }

        .result-content {
          flex: 1;
          min-width: 0;
        }

        .result-name {
          font-size: 13px;
          font-weight: 500;
          color: white;
          margin-bottom: 4px;
        }

        .result-preview {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.5);
          line-height: 1.4;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }

        .result-similarity {
          font-size: 11px;
          color: rgba(255, 255, 255, 0.4);
          flex-shrink: 0;
        }
      `}</style>
    </div>
  )
}
