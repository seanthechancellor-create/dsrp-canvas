/**
 * CategoryTree - Interactive tree hierarchy visualization of categories and topics
 * Shows clear parent-child relationships with visual connecting lines
 *
 * Scale optimizations for large knowledge maps:
 * - Search/filter across categories and topics
 * - Lazy expansion of topic lists
 * - Virtualized rendering for 100+ topics per category
 */

import { useState, useEffect, useMemo } from 'react'
import { useCategoryStore, CATEGORY_COLORS } from '../stores/categoryStore'

interface CategoryTreeProps {
  onTopicSelect?: (category: string, topic: string) => void
  onCategorySelect?: (category: string) => void
  editable?: boolean
  searchQuery?: string
}

// Maximum topics to show initially (for performance with large lists)
const INITIAL_TOPICS_LIMIT = 20
const TOPICS_LOAD_MORE = 20

export function CategoryTree({ onTopicSelect, onCategorySelect, editable = true, searchQuery = '' }: CategoryTreeProps) {
  const {
    categories,
    addCategory,
    deleteCategory,
    addTopic,
    removeTopic,
  } = useCategoryStore()

  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())
  // Track how many topics to show per category (for lazy loading)
  const [topicsLimit, setTopicsLimit] = useState<Record<string, number>>({})

  // Filter categories and topics based on search query
  const filteredCategories = useMemo(() => {
    if (!searchQuery.trim()) return categories

    const query = searchQuery.toLowerCase()
    return categories
      .map(cat => {
        const categoryMatches = cat.name.toLowerCase().includes(query)
        const matchingTopics = cat.topics.filter(topic =>
          topic.toLowerCase().includes(query)
        )

        // Include category if name matches OR has matching topics
        if (categoryMatches || matchingTopics.length > 0) {
          return {
            ...cat,
            // If searching, show all matching topics
            topics: categoryMatches ? cat.topics : matchingTopics,
          }
        }
        return null
      })
      .filter((cat): cat is NonNullable<typeof cat> => cat !== null)
  }, [categories, searchQuery])

  // Auto-expand categories when searching
  useEffect(() => {
    if (searchQuery.trim()) {
      const matchingIds = new Set(filteredCategories.map(cat => cat.id))
      setExpandedCategories(matchingIds)
    }
  }, [searchQuery, filteredCategories])

  // Auto-expand categories that have topics
  useEffect(() => {
    const withTopics = categories.filter(cat => cat.topics.length > 0)
    if (withTopics.length > 0) {
      setExpandedCategories(prev => {
        const next = new Set(prev)
        withTopics.forEach(cat => next.add(cat.id))
        return next
      })
    }
  }, [categories])
  const [showAddCategory, setShowAddCategory] = useState(false)
  const [newCategoryName, setNewCategoryName] = useState('')
  const [newCategoryColor, setNewCategoryColor] = useState(CATEGORY_COLORS[0])
  const [addingTopicTo, setAddingTopicTo] = useState<string | null>(null)
  const [newTopicName, setNewTopicName] = useState('')

  const toggleExpand = (categoryId: string) => {
    const newExpanded = new Set(expandedCategories)
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId)
    } else {
      newExpanded.add(categoryId)
    }
    setExpandedCategories(newExpanded)
  }

  const handleAddCategory = () => {
    if (newCategoryName.trim()) {
      const cat = addCategory(newCategoryName.trim(), newCategoryColor)
      setNewCategoryName('')
      setNewCategoryColor(CATEGORY_COLORS[Math.floor(Math.random() * CATEGORY_COLORS.length)])
      setShowAddCategory(false)
      setExpandedCategories(prev => new Set([...prev, cat.id]))
    }
  }

  const handleAddTopic = (categoryId: string) => {
    if (newTopicName.trim()) {
      addTopic(categoryId, newTopicName.trim())
      setNewTopicName('')
      setAddingTopicTo(null)
    }
  }

  const handleDeleteCategory = (e: React.MouseEvent, categoryId: string) => {
    e.stopPropagation()
    if (confirm('Delete this category and all its topics?')) {
      deleteCategory(categoryId)
    }
  }

  const handleDeleteTopic = (e: React.MouseEvent, categoryId: string, topic: string) => {
    e.stopPropagation()
    removeTopic(categoryId, topic)
  }

  return (
    <div className="category-tree">
      {/* Root node - Knowledge Map */}
      <div className="tree-container">
        <div className="root-node">
          <div className="node-content root">
            <span className="node-icon">🧠</span>
            <span className="node-label">Knowledge Map</span>
            {editable && (
              <button
                className="add-btn"
                onClick={() => setShowAddCategory(!showAddCategory)}
                title="Add Category"
              >
                {showAddCategory ? '×' : '+'}
              </button>
            )}
          </div>
        </div>

        {/* Add Category Form */}
        {showAddCategory && (
          <div className="add-form root-add-form">
            <div className="form-connector" />
            <div className="form-content">
              <input
                type="text"
                placeholder="Category name..."
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddCategory()}
                autoFocus
              />
              <div className="color-picker">
                {CATEGORY_COLORS.map((color) => (
                  <button
                    key={color}
                    className={`color-swatch ${newCategoryColor === color ? 'selected' : ''}`}
                    style={{ background: color }}
                    onClick={() => setNewCategoryColor(color)}
                  />
                ))}
              </div>
              <button className="submit-btn" onClick={handleAddCategory}>
                Create
              </button>
            </div>
          </div>
        )}

        {/* Categories - Children of root */}
        {filteredCategories.length === 0 ? (
          <div className="empty-state">
            <div className="empty-connector" />
            <p>No categories yet. Click <strong>+</strong> above to create one.</p>
          </div>
        ) : (
          <div className="children-container">
            {filteredCategories.map((category, catIndex) => {
              const isExpanded = expandedCategories.has(category.id)
              const isLast = catIndex === filteredCategories.length - 1
              const currentTopicsLimit = topicsLimit[category.id] || INITIAL_TOPICS_LIMIT
              const visibleTopics = category.topics.slice(0, currentTopicsLimit)
              const hasMoreTopics = category.topics.length > currentTopicsLimit

              return (
                <div key={category.id} className="tree-node category-node">
                  {/* Visual connector line */}
                  <div className={`node-connector ${isLast ? 'last' : ''}`}>
                    <svg className="connector-svg" viewBox="0 0 30 50" preserveAspectRatio="none">
                      <path
                        d="M0,0 L0,25 Q0,25 10,25 L30,25"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      />
                      {!isLast && <line x1="0" y1="25" x2="0" y2="50" stroke="currentColor" strokeWidth="2" />}
                    </svg>
                  </div>

                  <div className="node-body">
                    {/* Category header */}
                    <div
                      className={`node-content category ${isExpanded ? 'expanded' : ''}`}
                      style={{ '--node-color': category.color } as React.CSSProperties}
                      onClick={() => {
                        toggleExpand(category.id)
                        onCategorySelect?.(category.name)
                      }}
                    >
                      <span className="expand-arrow">
                        {category.topics.length > 0 ? (isExpanded ? '▾' : '▸') : '○'}
                      </span>
                      <span className="color-dot" style={{ background: category.color }} />
                      <span className="node-label">{category.name}</span>
                      <span className="child-count">{category.topics.length} topics</span>
                      {editable && (
                        <div className="node-actions">
                          <button
                            className="action-btn add"
                            onClick={(e) => {
                              e.stopPropagation()
                              setAddingTopicTo(addingTopicTo === category.id ? null : category.id)
                              setExpandedCategories(prev => new Set([...prev, category.id]))
                            }}
                            title="Add Topic"
                          >
                            +
                          </button>
                          <button
                            className="action-btn delete"
                            onClick={(e) => handleDeleteCategory(e, category.id)}
                            title="Delete"
                          >
                            ×
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Add Topic Form */}
                    {addingTopicTo === category.id && (
                      <div className="add-form topic-add-form">
                        <div className="form-connector child" />
                        <div className="form-content small">
                          <input
                            type="text"
                            placeholder="Topic name..."
                            value={newTopicName}
                            onChange={(e) => setNewTopicName(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleAddTopic(category.id)}
                            autoFocus
                          />
                          <button className="submit-btn small" onClick={() => handleAddTopic(category.id)}>
                            Add
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Topics - Children of category */}
                    {isExpanded && category.topics.length > 0 && (
                      <div className="children-container topics">
                        {visibleTopics.map((topic, topicIndex) => {
                          const isLastTopic = topicIndex === visibleTopics.length - 1 && !hasMoreTopics

                          return (
                            <div key={topic} className="tree-node topic-node">
                              {/* Topic connector */}
                              <div className={`node-connector child ${isLastTopic ? 'last' : ''}`}>
                                <svg className="connector-svg small" viewBox="0 0 24 40" preserveAspectRatio="none">
                                  <path
                                    d="M0,0 L0,20 Q0,20 8,20 L24,20"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                  />
                                  {!isLastTopic && <line x1="0" y1="20" x2="0" y2="40" stroke="currentColor" strokeWidth="2" />}
                                </svg>
                              </div>

                              <div
                                className="node-content topic"
                                style={{ '--node-color': category.color } as React.CSSProperties}
                                onClick={() => onTopicSelect?.(category.name, topic)}
                              >
                                <span className="topic-bullet">•</span>
                                <span className="node-label">{topic}</span>
                                {editable && (
                                  <button
                                    className="action-btn delete small"
                                    onClick={(e) => handleDeleteTopic(e, category.id, topic)}
                                    title="Delete"
                                  >
                                    ×
                                  </button>
                                )}
                              </div>
                            </div>
                          )
                        })}

                        {/* Load More button for large topic lists */}
                        {hasMoreTopics && (
                          <div className="load-more-container">
                            <div className="node-connector child last">
                              <svg className="connector-svg small" viewBox="0 0 24 40" preserveAspectRatio="none">
                                <path d="M0,0 L0,20 Q0,20 8,20 L24,20" fill="none" stroke="currentColor" strokeWidth="2" />
                              </svg>
                            </div>
                            <button
                              className="load-more-btn"
                              onClick={() => setTopicsLimit(prev => ({
                                ...prev,
                                [category.id]: (prev[category.id] || INITIAL_TOPICS_LIMIT) + TOPICS_LOAD_MORE
                              }))}
                            >
                              Load {Math.min(TOPICS_LOAD_MORE, category.topics.length - currentTopicsLimit)} more
                              ({category.topics.length - currentTopicsLimit} remaining)
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <style>{`
        .category-tree {
          font-family: 'IBM Plex Sans', -apple-system, sans-serif;
          color: rgba(255,255,255,0.9);
          user-select: none;
          padding: 20px;
        }

        .tree-container {
          position: relative;
        }

        /* Root Node */
        .root-node {
          margin-bottom: 16px;
        }

        .node-content {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 14px 18px;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .node-content.root {
          background: linear-gradient(135deg, rgba(233, 69, 96, 0.25), rgba(233, 69, 96, 0.1));
          border: 2px solid #e94560;
          box-shadow: 0 4px 20px rgba(233, 69, 96, 0.2);
        }

        .node-icon {
          font-size: 26px;
        }

        .node-label {
          font-size: 1.1rem;
          font-weight: 600;
          flex: 1;
        }

        .root .node-label {
          font-size: 1.3rem;
        }

        .add-btn {
          width: 32px;
          height: 32px;
          border: 2px solid rgba(255,255,255,0.3);
          border-radius: 8px;
          background: transparent;
          color: rgba(255,255,255,0.7);
          font-size: 20px;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .add-btn:hover {
          background: #e94560;
          border-color: #e94560;
          color: white;
        }

        /* Tree structure */
        .children-container {
          margin-left: 24px;
          position: relative;
        }

        .children-container.topics {
          margin-left: 20px;
          margin-top: 8px;
        }

        .tree-node {
          display: flex;
          position: relative;
        }

        /* Connector lines */
        .node-connector {
          width: 30px;
          flex-shrink: 0;
          position: relative;
          color: rgba(255,255,255,0.25);
        }

        .node-connector.child {
          width: 24px;
        }

        .connector-svg {
          width: 100%;
          height: 50px;
          position: absolute;
          top: 0;
          left: 0;
        }

        .connector-svg.small {
          height: 40px;
        }

        .node-body {
          flex: 1;
          padding-bottom: 8px;
        }

        /* Category nodes */
        .node-content.category {
          background: rgba(255,255,255,0.05);
          border: 2px solid transparent;
          padding: 12px 16px;
        }

        .node-content.category:hover {
          background: rgba(255,255,255,0.1);
          border-color: var(--node-color);
          box-shadow: 0 2px 12px color-mix(in srgb, var(--node-color) 20%, transparent);
        }

        .node-content.category.expanded {
          background: color-mix(in srgb, var(--node-color) 15%, transparent);
          border-color: var(--node-color);
          box-shadow: 0 4px 16px color-mix(in srgb, var(--node-color) 25%, transparent);
        }

        .expand-arrow {
          font-size: 14px;
          color: rgba(255,255,255,0.5);
          width: 16px;
          transition: transform 0.2s;
        }

        .color-dot {
          width: 14px;
          height: 14px;
          border-radius: 50%;
          flex-shrink: 0;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }

        .child-count {
          font-size: 11px;
          color: rgba(255,255,255,0.4);
          background: rgba(0,0,0,0.25);
          padding: 3px 10px;
          border-radius: 12px;
        }

        .node-actions {
          display: flex;
          gap: 4px;
          opacity: 0;
          transition: opacity 0.15s;
        }

        .node-content:hover .node-actions {
          opacity: 1;
        }

        .action-btn {
          width: 26px;
          height: 26px;
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 6px;
          background: rgba(0,0,0,0.2);
          color: rgba(255,255,255,0.6);
          font-size: 16px;
          cursor: pointer;
          transition: all 0.15s;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .action-btn.small {
          width: 22px;
          height: 22px;
          font-size: 14px;
        }

        .action-btn.add:hover {
          background: #4CAF50;
          border-color: #4CAF50;
          color: white;
        }

        .action-btn.delete:hover {
          background: #e74c3c;
          border-color: #e74c3c;
          color: white;
        }

        /* Topic nodes */
        .node-content.topic {
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.1);
          padding: 10px 14px;
          border-radius: 8px;
        }

        .node-content.topic:hover {
          background: color-mix(in srgb, var(--node-color) 15%, transparent);
          border-color: var(--node-color);
        }

        .topic-bullet {
          color: var(--node-color);
          font-size: 18px;
        }

        .topic .node-label {
          font-size: 0.95rem;
          font-weight: 500;
        }

        /* Add forms */
        .add-form {
          display: flex;
          align-items: flex-start;
          margin-top: 12px;
        }

        .root-add-form {
          margin-left: 24px;
          margin-bottom: 16px;
        }

        .topic-add-form {
          margin-left: 20px;
        }

        .form-connector {
          width: 30px;
          height: 40px;
          position: relative;
          flex-shrink: 0;
        }

        .form-connector::before {
          content: '';
          position: absolute;
          left: 0;
          top: 0;
          width: 2px;
          height: 20px;
          background: rgba(255,255,255,0.2);
        }

        .form-connector::after {
          content: '';
          position: absolute;
          left: 0;
          top: 20px;
          width: 20px;
          height: 2px;
          background: rgba(255,255,255,0.2);
        }

        .form-connector.child {
          width: 24px;
        }

        .form-connector.child::after {
          width: 16px;
        }

        .form-content {
          display: flex;
          flex-direction: column;
          gap: 10px;
          padding: 14px;
          background: rgba(0,0,0,0.35);
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.1);
          flex: 1;
        }

        .form-content.small {
          flex-direction: row;
          padding: 8px;
          align-items: center;
        }

        .form-content input {
          padding: 10px 12px;
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 6px;
          background: rgba(0,0,0,0.3);
          color: white;
          font-size: 14px;
          flex: 1;
        }

        .form-content.small input {
          padding: 8px 10px;
          font-size: 13px;
        }

        .form-content input::placeholder {
          color: rgba(255,255,255,0.4);
        }

        .color-picker {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }

        .color-swatch {
          width: 26px;
          height: 26px;
          border: 2px solid transparent;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.15s;
        }

        .color-swatch:hover {
          transform: scale(1.15);
        }

        .color-swatch.selected {
          border-color: white;
          box-shadow: 0 0 0 2px rgba(0,0,0,0.4);
        }

        .submit-btn {
          padding: 10px 18px;
          background: linear-gradient(135deg, #e94560, #d63850);
          border: none;
          border-radius: 6px;
          color: white;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.15s;
        }

        .submit-btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(233, 69, 96, 0.3);
        }

        .submit-btn.small {
          padding: 8px 14px;
          font-size: 12px;
        }

        /* Empty state */
        .empty-state {
          display: flex;
          align-items: center;
          margin-left: 24px;
          color: rgba(255,255,255,0.4);
          padding: 20px 0;
        }

        .empty-connector {
          width: 30px;
          height: 30px;
          position: relative;
          flex-shrink: 0;
        }

        .empty-connector::before {
          content: '';
          position: absolute;
          left: 0;
          top: 0;
          width: 2px;
          height: 15px;
          background: rgba(255,255,255,0.15);
        }

        .empty-connector::after {
          content: '';
          position: absolute;
          left: 0;
          top: 15px;
          width: 20px;
          height: 2px;
          background: rgba(255,255,255,0.15);
        }

        .empty-state p {
          margin: 0;
          font-size: 14px;
        }

        /* Load More button for large topic lists */
        .load-more-container {
          display: flex;
          align-items: center;
        }

        .load-more-btn {
          padding: 8px 14px;
          background: rgba(255,255,255,0.05);
          border: 1px dashed rgba(255,255,255,0.3);
          border-radius: 8px;
          color: rgba(255,255,255,0.6);
          font-size: 12px;
          cursor: pointer;
          transition: all 0.15s;
          font-family: inherit;
        }

        .load-more-btn:hover {
          background: rgba(233, 69, 96, 0.15);
          border-color: #e94560;
          color: #e94560;
        }

        /* Animations */
        .children-container {
          animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  )
}
