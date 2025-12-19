/**
 * SplashPage - Landing page with category tree hierarchy
 */

import { useEffect } from 'react'
import { CategoryTree } from './CategoryTree'
import { useCategoryStore } from '../stores/categoryStore'

interface SplashPageProps {
  onEnterCanvas: (category?: string, topic?: string) => void
}

export function SplashPage({ onEnterCanvas }: SplashPageProps) {
  const { categories, fetchFromBackend } = useCategoryStore()

  useEffect(() => {
    fetchFromBackend()
  }, [fetchFromBackend])

  const totalTopics = categories.reduce((sum, cat) => sum + cat.topics.length, 0)

  return (
    <div className="splash-page">
      {/* Compact header bar */}
      <header className="splash-header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-d">D</span>
            <span className="logo-s">S</span>
            <span className="logo-r">R</span>
            <span className="logo-p">P</span>
          </div>
          <div className="title-group">
            <h1>DSRP Canvas</h1>
            <p className="tagline">4-8-3 Systems Thinking</p>
          </div>
        </div>

        <div className="header-right">
          <div className="stats-row">
            <div className="stat">
              <span className="stat-value">{categories.length}</span>
              <span className="stat-label">Categories</span>
            </div>
            <div className="stat">
              <span className="stat-value">{totalTopics}</span>
              <span className="stat-label">Topics</span>
            </div>
          </div>
          <button className="enter-canvas-btn" onClick={() => onEnterCanvas()}>
            Enter Canvas
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
      </header>

      {/* Knowledge Map Tree - Main content area */}
      <main className="splash-content">
        <CategoryTree
          onTopicSelect={(category, topic) => onEnterCanvas(category, topic)}
          onCategorySelect={(category) => onEnterCanvas(category)}
          editable={true}
        />
      </main>

      {/* Footer with DSRP legend */}
      <footer className="splash-footer">
        <div className="dsrp-legend">
          <div className="legend-item">
            <span className="legend-icon d">D</span>
            <span>Distinctions</span>
          </div>
          <div className="legend-item">
            <span className="legend-icon s">S</span>
            <span>Systems</span>
          </div>
          <div className="legend-item">
            <span className="legend-icon r">R</span>
            <span>Relationships</span>
          </div>
          <div className="legend-item">
            <span className="legend-icon p">P</span>
            <span>Perspectives</span>
          </div>
        </div>
      </footer>

      <style>{`
        .splash-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
          display: flex;
          flex-direction: column;
          font-family: 'IBM Plex Sans', -apple-system, sans-serif;
          position: relative;
        }

        .splash-page::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-image: url('https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=1920&q=80');
          background-size: cover;
          background-position: center;
          background-repeat: no-repeat;
          filter: grayscale(100%) brightness(0.3);
          opacity: 0.4;
          z-index: 0;
          pointer-events: none;
        }

        .splash-page > * {
          position: relative;
          z-index: 1;
        }

        .splash-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          background: rgba(0,0,0,0.3);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .logo {
          display: flex;
          gap: 4px;
        }

        .logo span {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          font-weight: 700;
          border-radius: 8px;
          color: white;
        }

        .logo-d { background: linear-gradient(135deg, #1976D2, #1565C0); }
        .logo-s { background: linear-gradient(135deg, #388E3C, #2E7D32); }
        .logo-r { background: linear-gradient(135deg, #F57C00, #EF6C00); }
        .logo-p { background: linear-gradient(135deg, #7B1FA2, #6A1B9A); }

        .title-group {
          display: flex;
          flex-direction: column;
        }

        .splash-header h1 {
          font-size: 1.5rem;
          font-weight: 600;
          color: white;
          margin: 0;
          line-height: 1.2;
        }

        .tagline {
          color: rgba(255,255,255,0.5);
          font-size: 0.85rem;
          margin: 0;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 24px;
        }

        .stats-row {
          display: flex;
          gap: 20px;
        }

        .stat {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .stat-value {
          font-size: 1.5rem;
          font-weight: 700;
          color: #e94560;
          line-height: 1;
        }

        .stat-label {
          font-size: 0.7rem;
          color: rgba(255,255,255,0.4);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .enter-canvas-btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
          background: linear-gradient(135deg, #e94560, #d63850);
          border: none;
          border-radius: 8px;
          color: white;
          font-size: 0.9rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          box-shadow: 0 4px 15px rgba(233, 69, 96, 0.3);
        }

        .enter-canvas-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 25px rgba(233, 69, 96, 0.4);
        }

        .splash-content {
          flex: 1;
          max-width: 900px;
          width: 100%;
          margin: 0 auto;
          padding: 20px;
          overflow-y: auto;
        }

        .splash-footer {
          padding: 20px;
          background: rgba(0,0,0,0.2);
          border-top: 1px solid rgba(255,255,255,0.1);
        }

        .dsrp-legend {
          display: flex;
          justify-content: center;
          gap: 24px;
          flex-wrap: wrap;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          color: rgba(255,255,255,0.5);
          font-size: 0.8rem;
        }

        .legend-icon {
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: 600;
          border-radius: 5px;
          color: white;
        }

        .legend-icon.d { background: #1976D2; }
        .legend-icon.s { background: #388E3C; }
        .legend-icon.r { background: #F57C00; }
        .legend-icon.p { background: #7B1FA2; }

        @media (max-width: 768px) {
          .splash-header {
            flex-direction: column;
            gap: 16px;
            padding: 16px;
          }

          .header-left {
            width: 100%;
            justify-content: center;
          }

          .header-right {
            width: 100%;
            justify-content: center;
            flex-wrap: wrap;
          }

          .splash-header h1 {
            font-size: 1.3rem;
          }

          .stats-row {
            gap: 16px;
          }

          .stat-value {
            font-size: 1.2rem;
          }

          .dsrp-legend {
            gap: 12px;
          }
        }
      `}</style>
    </div>
  )
}
