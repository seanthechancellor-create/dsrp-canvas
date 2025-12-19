/**
 * CategoryTree - Interactive tree hierarchy visualization of categories and topics
 */

import { useState } from 'react'
import { useCategoryStore, CATEGORY_COLORS } from '../stores/categoryStore'

interface CategoryTreeProps {
  onTopicSelect?: (category: string, topic: string) => void
  onCategorySelect?: (category: string) => void
  editable?: boolean
}

export function CategoryTree({ onTopicSelect, onCategorySelect, editable = true }: CategoryTreeProps) {
  const {
    categories,
    addCategory,
    deleteCategory,
    addTopic,
    removeTopic,
  } = useCategoryStore()

  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())
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
      // Auto-expand the new category
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
      {/* Root node */}
      <div className="tree-root">
        <div className="root-node">
          <span className="root-icon">🧠</span>
          <span className="root-label">Knowledge Map</span>
          {editable && (
            <button
              className="add-root-btn"
              onClick={() => setShowAddCategory(!showAddCategory)}
              title="Add Category"
            >
              {showAddCategory ? '×' : '+'}
            </button>
          )}
        </div>

        {/* Add Category Form */}
        {showAddCategory && (
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
              Create Category
            </button>
          </div>
        )}

        {/* Tree branches */}
        <div className="tree-branches">
          {categories.length === 0 ? (
            <div className="empty-state">
              <p>No categories yet</p>
              <p className="hint">Click + to create your first category</p>
            </div>
          ) : (
            categories.map((category, catIndex) => (
              <div key={category.id} className="category-branch">
                {/* Branch connector */}
                <div className="branch-connector">
                  <div className={`vertical-line ${catIndex === categories.length - 1 ? 'last' : ''}`} />
                  <div className="horizontal-line" />
                </div>

                {/* Category node */}
                <div className="category-node-wrapper">
                  <div
                    className={`category-node ${expandedCategories.has(category.id) ? 'expanded' : ''}`}
                    style={{ '--cat-color': category.color } as React.CSSProperties}
                    onClick={() => {
                      toggleExpand(category.id)
                      onCategorySelect?.(category.name)
                    }}
                  >
                    <span className="expand-icon">
                      {category.topics.length > 0 ? (expandedCategories.has(category.id) ? '▼' : '▶') : '•'}
                    </span>
                    <span className="color-indicator" style={{ background: category.color }} />
                    <span className="category-name">{category.name}</span>
                    <span className="topic-count">{category.topics.length}</span>
                    {editable && (
                      <div className="category-actions">
                        <button
                          className="add-topic-btn"
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
                          className="delete-btn"
                          onClick={(e) => handleDeleteCategory(e, category.id)}
                          title="Delete Category"
                        >
                          ×
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Add Topic Form */}
                  {addingTopicTo === category.id && (
                    <div className="add-topic-form">
                      <input
                        type="text"
                        placeholder="Topic name..."
                        value={newTopicName}
                        onChange={(e) => setNewTopicName(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddTopic(category.id)}
                        autoFocus
                      />
                      <button onClick={() => handleAddTopic(category.id)}>Add</button>
                    </div>
                  )}

                  {/* Topics (children) */}
                  {expandedCategories.has(category.id) && category.topics.length > 0 && (
                    <div className="topics-branch">
                      {category.topics.map((topic, topicIndex) => (
                        <div key={topic} className="topic-branch">
                          {/* Topic connector */}
                          <div className="branch-connector topic-connector">
                            <div className={`vertical-line ${topicIndex === category.topics.length - 1 ? 'last' : ''}`} />
                            <div className="horizontal-line" />
                          </div>

                          {/* Topic node */}
                          <div
                            className="topic-node"
                            onClick={() => onTopicSelect?.(category.name, topic)}
                          >
                            <span className="topic-icon">◦</span>
                            <span className="topic-name">{topic}</span>
                            {editable && (
                              <button
                                className="delete-topic-btn"
                                onClick={(e) => handleDeleteTopic(e, category.id, topic)}
                                title="Delete Topic"
                              >
                                ×
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <style>{`
        .category-tree {
          font-family: 'IBM Plex Sans', -apple-system, sans-serif;
          color: rgba(255,255,255,0.9);
          user-select: none;
        }

        .tree-root {
          padding: 20px;
        }

        .root-node {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px 20px;
          background: linear-gradient(135deg, rgba(233, 69, 96, 0.2), rgba(233, 69, 96, 0.05));
          border: 2px solid #e94560;
          border-radius: 12px;
          margin-bottom: 20px;
        }

        .root-icon {
          font-size: 28px;
        }

        .root-label {
          font-size: 1.4rem;
          font-weight: 600;
          flex: 1;
        }

        .add-root-btn {
          width: 32px;
          height: 32px;
          border: 2px solid rgba(255,255,255,0.3);
          border-radius: 8px;
          background: transparent;
          color: rgba(255,255,255,0.7);
          font-size: 20px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .add-root-btn:hover {
          background: #e94560;
          border-color: #e94560;
          color: white;
        }

        .add-category-form {
          display: flex;
          flex-direction: column;
          gap: 12px;
          padding: 16px;
          background: rgba(0,0,0,0.3);
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.1);
          margin-bottom: 20px;
          margin-left: 40px;
        }

        .add-category-form input {
          padding: 12px 14px;
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 6px;
          background: rgba(0,0,0,0.3);
          color: white;
          font-size: 14px;
        }

        .add-category-form input::placeholder {
          color: rgba(255,255,255,0.4);
        }

        .color-picker {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }

        .color-swatch {
          width: 28px;
          height: 28px;
          border: 2px solid transparent;
          border-radius: 6px;
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
          padding: 10px 16px;
          background: #e94560;
          border: none;
          border-radius: 6px;
          color: white;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
        }

        .create-btn:hover {
          background: #d63850;
        }

        .tree-branches {
          margin-left: 20px;
        }

        .empty-state {
          text-align: center;
          padding: 40px;
          color: rgba(255,255,255,0.4);
        }

        .empty-state p {
          margin: 0;
        }

        .empty-state .hint {
          font-size: 12px;
          margin-top: 8px;
        }

        .category-branch {
          display: flex;
          margin-bottom: 8px;
        }

        .branch-connector {
          display: flex;
          align-items: flex-start;
          width: 30px;
          flex-shrink: 0;
        }

        .vertical-line {
          width: 2px;
          background: rgba(255,255,255,0.2);
          height: 100%;
          min-height: 50px;
        }

        .vertical-line.last {
          height: 25px;
        }

        .horizontal-line {
          width: 20px;
          height: 2px;
          background: rgba(255,255,255,0.2);
          margin-top: 23px;
        }

        .category-node-wrapper {
          flex: 1;
        }

        .category-node {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 16px;
          background: rgba(255,255,255,0.05);
          border: 2px solid transparent;
          border-radius: 10px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .category-node:hover {
          background: rgba(255,255,255,0.1);
          border-color: var(--cat-color);
        }

        .category-node.expanded {
          border-color: var(--cat-color);
          background: color-mix(in srgb, var(--cat-color) 10%, transparent);
        }

        .expand-icon {
          font-size: 10px;
          color: rgba(255,255,255,0.5);
          width: 14px;
        }

        .color-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .category-name {
          font-size: 15px;
          font-weight: 500;
          flex: 1;
        }

        .topic-count {
          font-size: 11px;
          color: rgba(255,255,255,0.4);
          background: rgba(0,0,0,0.3);
          padding: 2px 8px;
          border-radius: 10px;
        }

        .category-actions {
          display: flex;
          gap: 4px;
          opacity: 0;
          transition: opacity 0.15s;
        }

        .category-node:hover .category-actions {
          opacity: 1;
        }

        .add-topic-btn,
        .delete-btn {
          width: 24px;
          height: 24px;
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 4px;
          background: transparent;
          color: rgba(255,255,255,0.6);
          font-size: 14px;
          cursor: pointer;
          transition: all 0.15s;
        }

        .add-topic-btn:hover {
          background: #4CAF50;
          border-color: #4CAF50;
          color: white;
        }

        .delete-btn:hover {
          background: #e74c3c;
          border-color: #e74c3c;
          color: white;
        }

        .add-topic-form {
          display: flex;
          gap: 8px;
          margin-top: 8px;
          margin-left: 36px;
        }

        .add-topic-form input {
          flex: 1;
          padding: 8px 12px;
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 6px;
          background: rgba(0,0,0,0.3);
          color: white;
          font-size: 13px;
        }

        .add-topic-form button {
          padding: 8px 16px;
          background: #4CAF50;
          border: none;
          border-radius: 6px;
          color: white;
          font-size: 12px;
          cursor: pointer;
        }

        .topics-branch {
          margin-left: 36px;
          margin-top: 8px;
        }

        .topic-branch {
          display: flex;
          margin-bottom: 4px;
        }

        .topic-connector {
          width: 24px;
        }

        .topic-connector .vertical-line {
          min-height: 36px;
        }

        .topic-connector .vertical-line.last {
          height: 18px;
        }

        .topic-connector .horizontal-line {
          width: 16px;
          margin-top: 17px;
        }

        .topic-node {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.15s;
          flex: 1;
        }

        .topic-node:hover {
          background: rgba(233, 69, 96, 0.15);
          border-color: #e94560;
        }

        .topic-icon {
          color: rgba(255,255,255,0.4);
        }

        .topic-name {
          font-size: 13px;
          flex: 1;
        }

        .delete-topic-btn {
          width: 20px;
          height: 20px;
          border: none;
          border-radius: 3px;
          background: transparent;
          color: rgba(255,255,255,0.3);
          font-size: 12px;
          cursor: pointer;
          opacity: 0;
          transition: all 0.15s;
        }

        .topic-node:hover .delete-topic-btn {
          opacity: 1;
        }

        .delete-topic-btn:hover {
          background: #e74c3c;
          color: white;
        }
      `}</style>
    </div>
  )
}
