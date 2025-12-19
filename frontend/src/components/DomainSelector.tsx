/**
 * DomainSelector - Editable multi-category knowledge base selector
 *
 * Allows creating custom categories (not just privacy certifications)
 * with add/edit/delete functionality.
 */

import { useState, useEffect } from 'react'
import { useCategoryStore, CATEGORY_COLORS } from '../stores/categoryStore'

interface DomainSelectorProps {
  selectedDomain: string | null
  selectedTopic: string | null
  onDomainChange: (domain: string | null) => void
  onTopicChange: (topic: string | null) => void
  onTopicAnalyze?: (topic: string) => void
  collapsed?: boolean
}

export function DomainSelector({
  selectedDomain,
  selectedTopic,
  onDomainChange,
  onTopicChange,
  onTopicAnalyze,
  collapsed = false,
}: DomainSelectorProps) {
  const {
    categories,
    isLoading,
    addCategory,
    deleteCategory,
    addTopic,
    removeTopic,
    fetchFromBackend,
  } = useCategoryStore()

  const [showAddForm, setShowAddForm] = useState(false)
  const [newCategoryName, setNewCategoryName] = useState('')
  const [newCategoryColor, setNewCategoryColor] = useState(CATEGORY_COLORS[0])
  const [editingTopic, setEditingTopic] = useState(false)
  const [newTopicName, setNewTopicName] = useState('')

  // Fetch categories on mount
  useEffect(() => {
    fetchFromBackend()
  }, [fetchFromBackend])

  const handleDomainClick = (categoryName: string) => {
    if (selectedDomain === categoryName) {
      onDomainChange(null)
      onTopicChange(null)
    } else {
      onDomainChange(categoryName)
      onTopicChange(null)
    }
  }

  const handleTopicClick = (topic: string) => {
    if (selectedTopic === topic) {
      onTopicChange(null)
    } else {
      onTopicChange(topic)
      if (onTopicAnalyze) {
        onTopicAnalyze(topic)
      }
    }
  }

  const handleAddCategory = () => {
    if (newCategoryName.trim()) {
      addCategory(newCategoryName.trim(), newCategoryColor)
      setNewCategoryName('')
      setNewCategoryColor(CATEGORY_COLORS[Math.floor(Math.random() * CATEGORY_COLORS.length)])
      setShowAddForm(false)
    }
  }

  const handleDeleteCategory = (e: React.MouseEvent, categoryId: string) => {
    e.stopPropagation()
    if (confirm('Delete this category?')) {
      deleteCategory(categoryId)
      if (selectedDomain === categories.find(c => c.id === categoryId)?.name) {
        onDomainChange(null)
        onTopicChange(null)
      }
    }
  }

  const handleAddTopic = (categoryId: string) => {
    if (newTopicName.trim()) {
      addTopic(categoryId, newTopicName.trim())
      setNewTopicName('')
      setEditingTopic(false)
    }
  }

  const handleDeleteTopic = (e: React.MouseEvent, categoryId: string, topic: string) => {
    e.stopPropagation()
    removeTopic(categoryId, topic)
    if (selectedTopic === topic) {
      onTopicChange(null)
    }
  }

  const currentCategory = categories.find((c) => c.name === selectedDomain)

  if (collapsed) {
    return (
      <div className="domain-selector collapsed">
        <div
          className="domain-icon"
          style={{
            background: currentCategory
              ? `${currentCategory.color}20`
              : 'rgba(255,255,255,0.05)',
            borderColor: currentCategory?.color || 'transparent',
          }}
          title={selectedDomain || 'All Categories'}
        >
          {selectedDomain ? selectedDomain.charAt(0).toUpperCase() : '+'}
        </div>

        <style>{collapsedStyles}</style>
      </div>
    )
  }

  return (
    <div className="domain-selector">
      <div className="domain-header">
        <span className="domain-label">Categories</span>
        <button
          className="add-btn"
          onClick={() => setShowAddForm(!showAddForm)}
          title="Add Category"
        >
          {showAddForm ? '×' : '+'}
        </button>
      </div>

      {/* Add Category Form */}
      {showAddForm && (
        <div className="add-category-form">
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
          <button className="create-btn" onClick={handleAddCategory}>
            Create
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="domain-loading">Loading...</div>
      ) : categories.length === 0 ? (
        <div className="domain-empty">
          <span>No categories yet</span>
          <p className="empty-hint">
            Click + to add categories like "Privacy", "AI", "Security", etc.
          </p>
        </div>
      ) : (
        <>
          <div className="domain-chips">
            {categories.map((category) => (
              <div
                key={category.id}
                className={`domain-chip ${selectedDomain === category.name ? 'active' : ''}`}
                style={{
                  borderColor:
                    selectedDomain === category.name ? category.color : 'transparent',
                  background:
                    selectedDomain === category.name
                      ? `${category.color}20`
                      : 'rgba(255,255,255,0.05)',
                }}
                onClick={() => handleDomainClick(category.name)}
              >
                <span
                  className="color-dot"
                  style={{ background: category.color }}
                />
                <span className="domain-name">{category.name}</span>
                <span className="domain-count">{category.count}</span>
                {category.isCustom && (
                  <button
                    className="delete-chip-btn"
                    onClick={(e) => handleDeleteCategory(e, category.id)}
                    title="Delete category"
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Topics within selected category */}
          {currentCategory && (
            <div className="topic-section">
              <div className="topic-header">
                <span className="topic-label">Topics</span>
                <button
                  className="add-topic-btn"
                  onClick={() => setEditingTopic(!editingTopic)}
                  title="Add Topic"
                >
                  {editingTopic ? '×' : '+'}
                </button>
              </div>

              {editingTopic && (
                <div className="add-topic-form">
                  <input
                    type="text"
                    placeholder="Topic name..."
                    value={newTopicName}
                    onChange={(e) => setNewTopicName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleAddTopic(currentCategory.id)
                    }}
                    autoFocus
                  />
                  <button onClick={() => handleAddTopic(currentCategory.id)}>Add</button>
                </div>
              )}

              <div className="topic-chips">
                {currentCategory.topics.length === 0 ? (
                  <span className="no-topics">No topics yet</span>
                ) : (
                  currentCategory.topics.map((topic) => (
                    <div
                      key={topic}
                      className={`topic-chip ${selectedTopic === topic ? 'active' : ''}`}
                      onClick={() => handleTopicClick(topic)}
                    >
                      <span>{topic}</span>
                      <button
                        className="delete-topic-btn"
                        onClick={(e) => handleDeleteTopic(e, currentCategory.id, topic)}
                      >
                        ×
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </>
      )}

      <style>{expandedStyles}</style>
    </div>
  )
}

const collapsedStyles = `
  .domain-selector.collapsed {
    display: flex;
    justify-content: center;
  }
  .domain-icon {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid transparent;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    color: rgba(255,255,255,0.8);
    cursor: pointer;
    transition: all 0.15s;
  }
  .domain-icon:hover {
    background: rgba(255,255,255,0.1);
  }
`

const expandedStyles = `
  .domain-selector {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .domain-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .domain-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: rgba(255,255,255,0.4);
  }
  .add-btn {
    width: 20px;
    height: 20px;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    background: transparent;
    color: rgba(255,255,255,0.6);
    cursor: pointer;
    font-size: 14px;
    line-height: 1;
    transition: all 0.15s;
  }
  .add-btn:hover {
    background: #e94560;
    border-color: #e94560;
    color: white;
  }

  .add-category-form {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 10px;
    background: rgba(0,0,0,0.3);
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.1);
  }
  .add-category-form input {
    padding: 8px 10px;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    background: rgba(0,0,0,0.3);
    color: white;
    font-size: 12px;
  }
  .add-category-form input::placeholder {
    color: rgba(255,255,255,0.4);
  }
  .color-picker {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }
  .color-swatch {
    width: 20px;
    height: 20px;
    border: 2px solid transparent;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .color-swatch:hover {
    transform: scale(1.1);
  }
  .color-swatch.selected {
    border-color: white;
    box-shadow: 0 0 0 2px rgba(0,0,0,0.3);
  }
  .create-btn {
    padding: 8px 12px;
    background: #e94560;
    border: none;
    border-radius: 4px;
    color: white;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .create-btn:hover {
    background: #d63850;
  }

  .domain-loading,
  .domain-empty {
    font-size: 12px;
    color: rgba(255,255,255,0.5);
    text-align: center;
    padding: 10px;
  }
  .domain-empty {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .empty-hint {
    font-size: 10px;
    color: rgba(255,255,255,0.3);
    margin: 0;
  }

  .domain-chips {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .domain-chip {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border: 2px solid transparent;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s;
    font-size: 12px;
  }
  .domain-chip:hover {
    background: rgba(255,255,255,0.08);
  }
  .color-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .domain-name {
    color: rgba(255,255,255,0.85);
    font-weight: 500;
    flex: 1;
  }
  .domain-count {
    font-size: 10px;
    color: rgba(255,255,255,0.4);
    background: rgba(0,0,0,0.2);
    padding: 1px 5px;
    border-radius: 3px;
  }
  .domain-chip.active .domain-count {
    background: rgba(0,0,0,0.3);
    color: rgba(255,255,255,0.7);
  }
  .delete-chip-btn {
    width: 16px;
    height: 16px;
    border: none;
    border-radius: 3px;
    background: transparent;
    color: rgba(255,255,255,0.3);
    cursor: pointer;
    font-size: 12px;
    line-height: 1;
    opacity: 0;
    transition: all 0.15s;
  }
  .domain-chip:hover .delete-chip-btn {
    opacity: 1;
  }
  .delete-chip-btn:hover {
    background: #e74c3c;
    color: white;
  }

  .topic-section {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid rgba(255,255,255,0.1);
  }
  .topic-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }
  .topic-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: rgba(255,255,255,0.3);
  }
  .add-topic-btn {
    width: 16px;
    height: 16px;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 3px;
    background: transparent;
    color: rgba(255,255,255,0.5);
    cursor: pointer;
    font-size: 12px;
    line-height: 1;
  }
  .add-topic-btn:hover {
    background: #e94560;
    border-color: #e94560;
    color: white;
  }

  .add-topic-form {
    display: flex;
    gap: 6px;
    margin-bottom: 8px;
  }
  .add-topic-form input {
    flex: 1;
    padding: 6px 8px;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    background: rgba(0,0,0,0.3);
    color: white;
    font-size: 11px;
  }
  .add-topic-form button {
    padding: 6px 10px;
    background: #e94560;
    border: none;
    border-radius: 4px;
    color: white;
    font-size: 10px;
    cursor: pointer;
  }

  .topic-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .no-topics {
    font-size: 10px;
    color: rgba(255,255,255,0.3);
    font-style: italic;
  }
  .topic-chip {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    color: rgba(255,255,255,0.6);
    font-size: 10px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .topic-chip:hover {
    background: rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.9);
  }
  .topic-chip.active {
    background: rgba(233, 69, 96, 0.2);
    border-color: #e94560;
    color: #fff;
  }
  .delete-topic-btn {
    border: none;
    background: transparent;
    color: rgba(255,255,255,0.3);
    cursor: pointer;
    font-size: 10px;
    padding: 0 2px;
    opacity: 0;
    transition: all 0.15s;
  }
  .topic-chip:hover .delete-topic-btn {
    opacity: 1;
  }
  .delete-topic-btn:hover {
    color: #e74c3c;
  }
`
