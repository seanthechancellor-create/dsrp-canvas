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
      <header className="splash-header">
        <div className="logo-section">
          <div className="logo">
            <span className="logo-d">D</span>
            <span className="logo-s">S</span>
            <span className="logo-r">R</span>
            <span className="logo-p">P</span>
          </div>
          <h1>DSRP Canvas</h1>
          <p className="tagline">4-8-3 Systems Thinking Knowledge Map</p>
        </div>

        <div className="stats-row">
          <div className="stat">
            <span className="stat-value">{categories.length}</span>
            <span className="stat-label">Categories</span>
          </div>
          <div className="stat">
            <span className="stat-value">{totalTopics}</span>
            <span className="stat-label">Topics</span>
          </div>
          <div className="stat">
            <span className="stat-value">8</span>
            <span className="stat-label">DSRP Moves</span>
          </div>
        </div>

        <button className="enter-canvas-btn" onClick={() => onEnterCanvas()}>
          Enter Canvas
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
      </header>

      <main className="splash-content">
        <CategoryTree
          onTopicSelect={(category, topic) => onEnterCanvas(category, topic)}
          onCategorySelect={(category) => onEnterCanvas(category)}
          editable={true}
        />
      </main>

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
        }

        .splash-header {
          text-align: center;
          padding: 60px 20px 40px;
          background: linear-gradient(180deg, rgba(0,0,0,0.3) 0%, transparent 100%);
        }

        .logo-section {
          margin-bottom: 30px;
        }

        .logo {
          display: flex;
          justify-content: center;
          gap: 8px;
          margin-bottom: 16px;
        }

        .logo span {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          font-weight: 700;
          border-radius: 10px;
          color: white;
        }

        .logo-d { background: linear-gradient(135deg, #1976D2, #1565C0); }
        .logo-s { background: linear-gradient(135deg, #388E3C, #2E7D32); }
        .logo-r { background: linear-gradient(135deg, #F57C00, #EF6C00); }
        .logo-p { background: linear-gradient(135deg, #7B1FA2, #6A1B9A); }

        .splash-header h1 {
          font-size: 2.5rem;
          font-weight: 600;
          color: white;
          margin: 0 0 8px 0;
        }

        .tagline {
          color: rgba(255,255,255,0.6);
          font-size: 1.1rem;
          margin: 0;
        }

        .stats-row {
          display: flex;
          justify-content: center;
          gap: 40px;
          margin: 30px 0;
        }

        .stat {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .stat-value {
          font-size: 2rem;
          font-weight: 700;
          color: #e94560;
        }

        .stat-label {
          font-size: 0.85rem;
          color: rgba(255,255,255,0.5);
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .enter-canvas-btn {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding: 14px 28px;
          background: linear-gradient(135deg, #e94560, #d63850);
          border: none;
          border-radius: 10px;
          color: white;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          box-shadow: 0 4px 20px rgba(233, 69, 96, 0.3);
        }

        .enter-canvas-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 30px rgba(233, 69, 96, 0.4);
        }

        .splash-content {
          flex: 1;
          max-width: 800px;
          width: 100%;
          margin: 0 auto;
          padding: 20px;
        }

        .splash-footer {
          padding: 30px 20px;
          background: rgba(0,0,0,0.2);
          border-top: 1px solid rgba(255,255,255,0.1);
        }

        .dsrp-legend {
          display: flex;
          justify-content: center;
          gap: 30px;
          flex-wrap: wrap;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 8px;
          color: rgba(255,255,255,0.6);
          font-size: 0.9rem;
        }

        .legend-icon {
          width: 28px;
          height: 28px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          font-weight: 600;
          border-radius: 6px;
          color: white;
        }

        .legend-icon.d { background: #1976D2; }
        .legend-icon.s { background: #388E3C; }
        .legend-icon.r { background: #F57C00; }
        .legend-icon.p { background: #7B1FA2; }

        @media (max-width: 600px) {
          .splash-header h1 {
            font-size: 1.8rem;
          }

          .stats-row {
            gap: 20px;
          }

          .stat-value {
            font-size: 1.5rem;
          }

          .dsrp-legend {
            gap: 15px;
          }
        }
      `}</style>
    </div>
  )
}
