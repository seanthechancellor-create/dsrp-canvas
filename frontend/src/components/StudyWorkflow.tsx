/**
 * StudyWorkflow - 5-Step Study System with Stepper Navigation
 *
 * A clean, focused interface that guides users through:
 * 1. GATHER - Upload and process source materials
 * 2. REFLECTION - Apply DSRP 4-8-3 analysis
 * 3. METACOGNITION - Visualize knowledge graph
 * 4. FIX/PRESENT - Review and correct
 * 5. ACTIVE RECALL - Generate questions
 */

import { useState, useCallback } from 'react'

// Step components will be imported here
import { GatherStep } from './steps/GatherStep'
import { ReflectionStep } from './steps/ReflectionStep'
import { MetacognitionStep } from './steps/MetacognitionStep'
import { FixPresentStep } from './steps/FixPresentStep'
import { ActiveRecallStep } from './steps/ActiveRecallStep'

export interface StudySession {
  id: string
  sourceName: string
  sourceType: string
  text: string
  currentStep: number
  // Step results
  gatherResult?: {
    textLength: number
    chunks: number
  }
  reflectionResult?: {
    summary: any
    concepts: string[]
    dsrpAnalyses: any[]
  }
  metacognitionResult?: {
    nodes: any[]
    edges: any[]
    crossReferences: any[]
  }
  fixPresentResult?: {
    corrections: any[]
    presentationReady: boolean
  }
  activeRecallResult?: {
    questions: any[]
    questionCount: number
  }
}

const STEPS = [
  {
    number: 1,
    id: 'gather',
    name: 'Gather',
    description: 'Upload sources',
    icon: '📥',
  },
  {
    number: 2,
    id: 'reflection',
    name: 'Reflection',
    description: 'DSRP analysis',
    icon: '🔍',
  },
  {
    number: 3,
    id: 'metacognition',
    name: 'Metacognition',
    description: 'Knowledge graph',
    icon: '🧠',
  },
  {
    number: 4,
    id: 'fix',
    name: 'Fix/Present',
    description: 'Review & correct',
    icon: '✏️',
  },
  {
    number: 5,
    id: 'recall',
    name: 'Active Recall',
    description: 'Generate questions',
    icon: '❓',
  },
]

interface StudyWorkflowProps {
  onBack?: () => void
}

export function StudyWorkflow({ onBack }: StudyWorkflowProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [session, setSession] = useState<StudySession | null>(null)

  const canGoNext = useCallback(() => {
    if (!session) return currentStep === 1 // Can proceed from gather without session
    switch (currentStep) {
      case 1: return session.gatherResult !== undefined
      case 2: return session.reflectionResult !== undefined
      case 3: return session.metacognitionResult !== undefined
      case 4: return session.fixPresentResult !== undefined
      case 5: return true
      default: return false
    }
  }, [currentStep, session])

  const goToStep = useCallback((step: number) => {
    if (step >= 1 && step <= 5 && step <= currentStep + 1) {
      setCurrentStep(step)
    }
  }, [currentStep])

  const handleGatherComplete = useCallback((result: {
    sessionId: string
    sourceName: string
    sourceType: string
    text: string
    textLength: number
    chunks: number
  }) => {
    setSession({
      id: result.sessionId,
      sourceName: result.sourceName,
      sourceType: result.sourceType,
      text: result.text,
      currentStep: 1,
      gatherResult: {
        textLength: result.textLength,
        chunks: result.chunks,
      }
    })
    setCurrentStep(2)
  }, [])

  const handleReflectionComplete = useCallback((result: any) => {
    if (session) {
      setSession({
        ...session,
        currentStep: 2,
        reflectionResult: {
          summary: result.summary,
          concepts: result.concepts,
          dsrpAnalyses: result.dsrp_analyses || result.dsrpAnalyses,
        }
      })
      setCurrentStep(3)
    }
  }, [session])

  const handleMetacognitionComplete = useCallback((result: any) => {
    if (session) {
      setSession({
        ...session,
        currentStep: 3,
        metacognitionResult: {
          nodes: result.knowledge_graph?.nodes || [],
          edges: result.knowledge_graph?.edges || [],
          crossReferences: result.cross_references || [],
        }
      })
      setCurrentStep(4)
    }
  }, [session])

  const handleFixPresentComplete = useCallback((result: any) => {
    if (session) {
      setSession({
        ...session,
        currentStep: 4,
        fixPresentResult: {
          corrections: result.corrections || [],
          presentationReady: result.presentation_ready || true,
        }
      })
      setCurrentStep(5)
    }
  }, [session])

  const handleActiveRecallComplete = useCallback((result: any) => {
    if (session) {
      setSession({
        ...session,
        currentStep: 5,
        activeRecallResult: {
          questions: result.question_bank || [],
          questionCount: result.questions_generated || 0,
        }
      })
    }
  }, [session])

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return <GatherStep onComplete={handleGatherComplete} />
      case 2:
        return session ? (
          <ReflectionStep
            sessionId={session.id}
            text={session.text}
            sourceName={session.sourceName}
            onComplete={handleReflectionComplete}
          />
        ) : null
      case 3:
        return session ? (
          <MetacognitionStep
            sessionId={session.id}
            reflectionResult={session.reflectionResult}
            onComplete={handleMetacognitionComplete}
          />
        ) : null
      case 4:
        return session ? (
          <FixPresentStep
            sessionId={session.id}
            metacognitionResult={session.metacognitionResult}
            onComplete={handleFixPresentComplete}
          />
        ) : null
      case 5:
        return session ? (
          <ActiveRecallStep
            sessionId={session.id}
            onComplete={handleActiveRecallComplete}
          />
        ) : null
      default:
        return null
    }
  }

  return (
    <div className="study-workflow">
      {/* Header */}
      <header className="workflow-header">
        <button className="back-btn" onClick={onBack} title="Back to Library">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>
        <div className="header-title">
          <h1>DSRP Study System</h1>
          {session && <span className="source-name">{session.sourceName}</span>}
        </div>
        <div className="header-actions">
          {session && (
            <span className="session-info">
              Session: {session.id.slice(0, 8)}...
            </span>
          )}
        </div>
      </header>

      {/* Stepper */}
      <nav className="stepper">
        {STEPS.map((step, index) => {
          const isActive = step.number === currentStep
          const isCompleted = step.number < currentStep
          const isClickable = step.number <= currentStep + 1

          return (
            <div key={step.id} className="step-wrapper">
              <button
                className={`step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''} ${isClickable ? 'clickable' : ''}`}
                onClick={() => isClickable && goToStep(step.number)}
                disabled={!isClickable}
              >
                <div className="step-indicator">
                  {isCompleted ? (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  ) : (
                    <span>{step.number}</span>
                  )}
                </div>
                <div className="step-content">
                  <span className="step-name">{step.name}</span>
                  <span className="step-desc">{step.description}</span>
                </div>
              </button>
              {index < STEPS.length - 1 && (
                <div className={`step-connector ${isCompleted ? 'completed' : ''}`} />
              )}
            </div>
          )
        })}
      </nav>

      {/* Main Content */}
      <main className="workflow-content" tabIndex={0}>
        {renderCurrentStep()}
      </main>

      {/* Footer Navigation */}
      <footer className="workflow-footer">
        <button
          className="nav-btn prev"
          onClick={() => goToStep(currentStep - 1)}
          disabled={currentStep === 1}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 18l-6-6 6-6"/>
          </svg>
          Previous
        </button>

        <div className="step-dots">
          {STEPS.map((step) => (
            <button
              key={step.id}
              className={`dot ${step.number === currentStep ? 'active' : ''} ${step.number < currentStep ? 'completed' : ''}`}
              onClick={() => goToStep(step.number)}
              disabled={step.number > currentStep + 1}
              title={step.name}
            />
          ))}
        </div>

        <button
          className="nav-btn next"
          onClick={() => goToStep(currentStep + 1)}
          disabled={currentStep === 5 || !canGoNext()}
        >
          {currentStep === 5 ? 'Complete' : 'Next'}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 18l6-6-6-6"/>
          </svg>
        </button>
      </footer>

      <style>{`
        .study-workflow {
          display: flex;
          flex-direction: column;
          height: 100vh;
          max-height: 100vh;
          overflow: hidden;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
          color: white;
          font-family: 'IBM Plex Sans', -apple-system, sans-serif;
        }

        /* Header */
        .workflow-header {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px 24px;
          background: rgba(0, 0, 0, 0.3);
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          flex-shrink: 0;
        }

        .back-btn {
          width: 40px;
          height: 40px;
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 8px;
          background: transparent;
          color: rgba(255, 255, 255, 0.7);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }

        .back-btn:hover {
          background: #e94560;
          border-color: #e94560;
          color: white;
        }

        .header-title {
          flex: 1;
        }

        .header-title h1 {
          font-size: 1.25rem;
          font-weight: 600;
          margin: 0;
        }

        .source-name {
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.5);
        }

        .session-info {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.4);
          background: rgba(255, 255, 255, 0.1);
          padding: 4px 10px;
          border-radius: 4px;
        }

        /* Stepper */
        .stepper {
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 24px;
          background: rgba(0, 0, 0, 0.2);
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          flex-shrink: 0;
        }

        .step-wrapper {
          display: flex;
          align-items: center;
        }

        .step {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          background: transparent;
          border: 2px solid rgba(255, 255, 255, 0.15);
          border-radius: 12px;
          color: rgba(255, 255, 255, 0.5);
          cursor: default;
          transition: all 0.2s;
        }

        .step.clickable {
          cursor: pointer;
        }

        .step.clickable:hover {
          border-color: rgba(255, 255, 255, 0.3);
          background: rgba(255, 255, 255, 0.05);
        }

        .step.active {
          border-color: #e94560;
          background: rgba(233, 69, 96, 0.15);
          color: white;
        }

        .step.completed {
          border-color: #4caf50;
          color: rgba(255, 255, 255, 0.8);
        }

        .step-indicator {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.1);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 14px;
        }

        .step.active .step-indicator {
          background: #e94560;
          color: white;
        }

        .step.completed .step-indicator {
          background: #4caf50;
          color: white;
        }

        .step-content {
          display: flex;
          flex-direction: column;
        }

        .step-name {
          font-weight: 600;
          font-size: 0.9rem;
        }

        .step-desc {
          font-size: 0.7rem;
          opacity: 0.7;
        }

        .step-connector {
          width: 40px;
          height: 2px;
          background: rgba(255, 255, 255, 0.15);
          margin: 0 8px;
        }

        .step-connector.completed {
          background: #4caf50;
        }

        /* Content */
        .workflow-content {
          flex: 1;
          min-height: 0;
          padding: 24px;
          overflow-y: auto;
          overflow-x: hidden;
          -webkit-overflow-scrolling: touch;
          outline: none;
          scroll-behavior: smooth;
        }

        .workflow-content:focus {
          outline: none;
        }

        .workflow-content:focus-visible {
          outline: 2px solid rgba(233, 69, 96, 0.5);
          outline-offset: -2px;
        }

        /* Footer */
        .workflow-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          background: rgba(0, 0, 0, 0.3);
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          flex-shrink: 0;
        }

        .nav-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 8px;
          background: transparent;
          color: rgba(255, 255, 255, 0.7);
          font-size: 0.9rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .nav-btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.3);
          color: white;
        }

        .nav-btn.next:not(:disabled) {
          background: #e94560;
          border-color: #e94560;
          color: white;
        }

        .nav-btn.next:hover:not(:disabled) {
          background: #d63850;
        }

        .nav-btn:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .step-dots {
          display: flex;
          gap: 8px;
        }

        .dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          border: 2px solid rgba(255, 255, 255, 0.3);
          background: transparent;
          cursor: pointer;
          transition: all 0.2s;
          padding: 0;
        }

        .dot:disabled {
          cursor: not-allowed;
          opacity: 0.3;
        }

        .dot.active {
          background: #e94560;
          border-color: #e94560;
        }

        .dot.completed {
          background: #4caf50;
          border-color: #4caf50;
        }

        /* Responsive */
        @media (max-width: 900px) {
          .stepper {
            overflow-x: auto;
            justify-content: flex-start;
            padding: 16px;
          }

          .step {
            padding: 8px 12px;
          }

          .step-content {
            display: none;
          }

          .step-connector {
            width: 24px;
          }
        }
      `}</style>
    </div>
  )
}
