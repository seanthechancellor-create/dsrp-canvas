/**
 * QuizPanel - DSRP-based quiz component for exam prep
 *
 * Generates questions from DSRP analyses for spaced repetition testing.
 * Supports pattern filtering (D, S, R, P) and provides detailed results.
 */

import { useState, useCallback } from 'react'
import { DSRP_COLORS, DSRPIcon, DSRPPattern } from './DSRPIcons'

// Use relative URL to go through Vite proxy
const API_URL = import.meta.env.VITE_API_URL || ''

interface QuizQuestion {
  id: string
  question: string
  concept: string
  pattern: string
  move: string
  options: string[]
  hint: string
  tags: string[]
}

interface QuizSession {
  session_id: string
  total_questions: number
  patterns: string[] | null
  current_question: QuizQuestion | null
  error?: string
}

interface AnswerResult {
  correct: boolean
  correct_answer: string
  correct_index: number
  explanation: string
  score: number
  answered: number
  total: number
  completed: boolean
  next_question: QuizQuestion | null
  percentage: number
}

interface QuizResults {
  session_id: string
  score: number
  total: number
  percentage: number
  pattern_scores: Record<string, { correct: number; total: number; percentage: number | null }>
  weak_concepts: Array<{
    concept: string
    pattern: string
    move: string
    question: string
    your_answer: string
    correct_answer: string
  }>
  recommendation: string
}

interface QuizPanelProps {
  conceptIds?: string[]
  domain?: string | null
  topic?: string | null
  onComplete?: (results: QuizResults) => void
}

type QuizState = 'setup' | 'active' | 'feedback' | 'results'

export function QuizPanel({ conceptIds, domain, topic, onComplete }: QuizPanelProps) {
  const [quizState, setQuizState] = useState<QuizState>('setup')
  const [session, setSession] = useState<QuizSession | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<QuizQuestion | null>(null)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [lastResult, setLastResult] = useState<AnswerResult | null>(null)
  const [results, setResults] = useState<QuizResults | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Setup options
  const [questionCount, setQuestionCount] = useState(10)
  const [selectedPatterns, setSelectedPatterns] = useState<string[]>([])

  const startQuiz = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/quiz/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          concept_ids: conceptIds && conceptIds.length > 0 ? conceptIds : null,
          patterns: selectedPatterns.length > 0 ? selectedPatterns : null,
          domain: domain || null,
          topic: topic || null,
          question_count: questionCount,
        }),
      })

      const data: QuizSession = await response.json()

      if (data.error) {
        setError(data.error)
        return
      }

      setSession(data)
      setCurrentQuestion(data.current_question)
      setQuizState('active')
    } catch (err) {
      setError('Failed to start quiz. Make sure you have analyzed some concepts first.')
    } finally {
      setLoading(false)
    }
  }, [conceptIds, questionCount, selectedPatterns, domain, topic])

  const submitAnswer = useCallback(async () => {
    if (!session || !currentQuestion || selectedAnswer === null) return

    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/quiz/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.session_id,
          question_id: currentQuestion.id,
          answer_index: selectedAnswer,
        }),
      })

      const data: AnswerResult = await response.json()
      setLastResult(data)
      setQuizState('feedback')

      if (data.completed) {
        // Fetch final results
        const resultsResponse = await fetch(`${API_URL}/api/quiz/results/${session.session_id}`)
        const resultsData: QuizResults = await resultsResponse.json()
        setResults(resultsData)
      }
    } catch (err) {
      setError('Failed to submit answer')
    } finally {
      setLoading(false)
    }
  }, [session, currentQuestion, selectedAnswer])

  const nextQuestion = useCallback(() => {
    if (lastResult?.next_question) {
      setCurrentQuestion(lastResult.next_question)
      setSelectedAnswer(null)
      setLastResult(null)
      setQuizState('active')
    } else if (lastResult?.completed) {
      setQuizState('results')
      if (results && onComplete) {
        onComplete(results)
      }
    }
  }, [lastResult, results, onComplete])

  const resetQuiz = useCallback(() => {
    setQuizState('setup')
    setSession(null)
    setCurrentQuestion(null)
    setSelectedAnswer(null)
    setLastResult(null)
    setResults(null)
    setError(null)
  }, [])

  const togglePattern = (pattern: string) => {
    setSelectedPatterns(prev =>
      prev.includes(pattern)
        ? prev.filter(p => p !== pattern)
        : [...prev, pattern]
    )
  }

  const patternKey = (currentQuestion?.pattern || 'D') as DSRPPattern

  return (
    <div className="quiz-panel">
      {error && (
        <div className="quiz-error">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Setup Screen */}
      {quizState === 'setup' && (
        <div className="quiz-setup">
          <div className="setup-header">
            <h3>DSRP Quiz</h3>
            <p>Test your knowledge of analyzed concepts</p>
            {domain && (
              <div className="domain-badge">
                <span className="domain-label">Domain:</span>
                <span className="domain-value">{domain}</span>
                {topic && <span className="topic-value"> &gt; {topic}</span>}
              </div>
            )}
          </div>

          <div className="setup-option">
            <label>Number of Questions</label>
            <div className="count-selector">
              {[5, 10, 15, 20].map(count => (
                <button
                  key={count}
                  className={`count-btn ${questionCount === count ? 'active' : ''}`}
                  onClick={() => setQuestionCount(count)}
                >
                  {count}
                </button>
              ))}
            </div>
          </div>

          <div className="setup-option">
            <label>Filter by Pattern (optional)</label>
            <div className="pattern-selector">
              {(['D', 'S', 'R', 'P'] as DSRPPattern[]).map(pattern => (
                <button
                  key={pattern}
                  className={`pattern-btn ${selectedPatterns.includes(pattern) ? 'active' : ''}`}
                  style={{
                    borderColor: selectedPatterns.includes(pattern) ? DSRP_COLORS[pattern] : 'rgba(255,255,255,0.2)',
                    background: selectedPatterns.includes(pattern) ? `${DSRP_COLORS[pattern]}20` : 'transparent',
                  }}
                  onClick={() => togglePattern(pattern)}
                >
                  <DSRPIcon pattern={pattern} size={20} color={DSRP_COLORS[pattern]} />
                  <span>{pattern}</span>
                </button>
              ))}
            </div>
            <span className="pattern-hint">Leave empty to quiz on all patterns</span>
          </div>

          <button
            className="start-quiz-btn"
            onClick={startQuiz}
            disabled={loading}
          >
            {loading ? 'Starting...' : 'Start Quiz'}
          </button>
        </div>
      )}

      {/* Active Question */}
      {quizState === 'active' && currentQuestion && (
        <div className="quiz-active">
          <div className="quiz-progress">
            <div className="progress-text">
              Question {(lastResult?.answered || 0) + 1} of {session?.total_questions || 0}
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${((lastResult?.answered || 0) / (session?.total_questions || 1)) * 100}%`
                }}
              />
            </div>
            {lastResult && (
              <div className="score-display">
                Score: {lastResult.score}/{lastResult.answered} ({lastResult.percentage}%)
              </div>
            )}
          </div>

          <div className="question-card">
            <div className="question-meta">
              <span
                className="pattern-tag"
                style={{ background: DSRP_COLORS[patternKey] }}
              >
                <DSRPIcon pattern={patternKey} size={14} color="#fff" />
                {currentQuestion.pattern}
              </span>
              <span className="concept-tag">{currentQuestion.concept}</span>
            </div>

            <h4 className="question-text">{currentQuestion.question}</h4>

            <div className="options-list">
              {currentQuestion.options.map((option, idx) => (
                <button
                  key={idx}
                  className={`option-btn ${selectedAnswer === idx ? 'selected' : ''}`}
                  onClick={() => setSelectedAnswer(idx)}
                >
                  <span className="option-letter">{String.fromCharCode(65 + idx)}</span>
                  <span className="option-text">{option}</span>
                </button>
              ))}
            </div>

            <div className="question-actions">
              <button
                className="hint-btn"
                onClick={() => alert(currentQuestion.hint)}
                title="Show hint"
              >
                Hint
              </button>
              <button
                className="submit-btn"
                onClick={submitAnswer}
                disabled={selectedAnswer === null || loading}
              >
                {loading ? 'Checking...' : 'Check Answer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Feedback Screen */}
      {quizState === 'feedback' && lastResult && currentQuestion && (
        <div className="quiz-feedback">
          <div className={`feedback-header ${lastResult.correct ? 'correct' : 'incorrect'}`}>
            <span className="feedback-icon">
              {lastResult.correct ? '✓' : '✗'}
            </span>
            <span className="feedback-text">
              {lastResult.correct ? 'Correct!' : 'Incorrect'}
            </span>
          </div>

          <div className="feedback-details">
            <div className="your-answer">
              <label>Your Answer:</label>
              <span className={lastResult.correct ? 'correct' : 'incorrect'}>
                {currentQuestion.options[selectedAnswer!]}
              </span>
            </div>

            {!lastResult.correct && (
              <div className="correct-answer">
                <label>Correct Answer:</label>
                <span>{lastResult.correct_answer}</span>
              </div>
            )}

            <div className="explanation">
              <label>Explanation:</label>
              <span>{lastResult.explanation}</span>
            </div>
          </div>

          <div className="feedback-score">
            Score: {lastResult.score}/{lastResult.answered} ({lastResult.percentage}%)
          </div>

          <button className="next-btn" onClick={nextQuestion}>
            {lastResult.completed ? 'See Results' : 'Next Question'}
          </button>
        </div>
      )}

      {/* Results Screen */}
      {quizState === 'results' && results && (
        <div className="quiz-results">
          <div className="results-header">
            <h3>Quiz Complete!</h3>
            <div className="final-score">
              <span className="score-number">{results.percentage}%</span>
              <span className="score-label">{results.score}/{results.total} correct</span>
            </div>
          </div>

          <div className="pattern-breakdown">
            <h4>Performance by Pattern</h4>
            <div className="pattern-scores">
              {Object.entries(results.pattern_scores).map(([pattern, scores]) => (
                scores.total > 0 && (
                  <div key={pattern} className="pattern-score-item">
                    <div className="pattern-info">
                      <DSRPIcon pattern={pattern as DSRPPattern} size={18} color={DSRP_COLORS[pattern as DSRPPattern]} />
                      <span>{pattern}</span>
                    </div>
                    <div className="pattern-bar-container">
                      <div
                        className="pattern-bar"
                        style={{
                          width: `${scores.percentage || 0}%`,
                          background: DSRP_COLORS[pattern as DSRPPattern],
                        }}
                      />
                    </div>
                    <span className="pattern-pct">{scores.percentage || 0}%</span>
                  </div>
                )
              ))}
            </div>
          </div>

          {results.weak_concepts.length > 0 && (
            <div className="weak-concepts">
              <h4>Concepts to Review</h4>
              <ul>
                {results.weak_concepts.slice(0, 5).map((wc, idx) => (
                  <li key={idx} className="weak-item">
                    <span className="weak-concept">{wc.concept}</span>
                    <span className="weak-pattern">[{wc.pattern}] {wc.move}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="recommendation">
            <h4>Recommendation</h4>
            <p>{results.recommendation}</p>
          </div>

          <div className="results-actions">
            <button className="retry-btn" onClick={resetQuiz}>
              Take Another Quiz
            </button>
          </div>
        </div>
      )}

      <style>{`
        .quiz-panel {
          display: flex;
          flex-direction: column;
          gap: 16px;
          min-height: 200px;
        }

        .quiz-error {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 16px;
          background: rgba(244, 67, 54, 0.15);
          border: 1px solid rgba(244, 67, 54, 0.4);
          border-radius: 8px;
          color: #ff6b6b;
          font-size: 13px;
        }
        .quiz-error .error-icon {
          width: 20px;
          height: 20px;
          background: #f44336;
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: 12px;
        }
        .quiz-error button {
          margin-left: auto;
          padding: 4px 10px;
          background: transparent;
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 4px;
          color: rgba(255,255,255,0.7);
          cursor: pointer;
          font-size: 12px;
        }

        /* Setup Screen */
        .quiz-setup {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        .setup-header h3 {
          margin: 0 0 4px 0;
          font-size: 18px;
          color: #fff;
        }
        .setup-header p {
          margin: 0;
          font-size: 13px;
          color: rgba(255,255,255,0.6);
        }
        .domain-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          margin-top: 8px;
          padding: 6px 12px;
          background: rgba(233, 69, 96, 0.15);
          border: 1px solid rgba(233, 69, 96, 0.3);
          border-radius: 6px;
          font-size: 12px;
        }
        .domain-label {
          color: rgba(255,255,255,0.5);
        }
        .domain-value {
          color: #e94560;
          font-weight: 600;
        }
        .topic-value {
          color: rgba(255,255,255,0.7);
        }

        .setup-option {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .setup-option label {
          font-size: 13px;
          font-weight: 600;
          color: rgba(255,255,255,0.8);
        }

        .count-selector {
          display: flex;
          gap: 8px;
        }
        .count-btn {
          padding: 8px 16px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 6px;
          color: rgba(255,255,255,0.7);
          cursor: pointer;
          transition: all 0.15s;
        }
        .count-btn:hover {
          background: rgba(255,255,255,0.1);
        }
        .count-btn.active {
          background: #e94560;
          border-color: #e94560;
          color: white;
        }

        .pattern-selector {
          display: flex;
          gap: 10px;
        }
        .pattern-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 10px 16px;
          background: transparent;
          border: 2px solid rgba(255,255,255,0.2);
          border-radius: 8px;
          color: rgba(255,255,255,0.8);
          cursor: pointer;
          transition: all 0.15s;
        }
        .pattern-btn:hover {
          border-color: rgba(255,255,255,0.4);
        }
        .pattern-hint {
          font-size: 11px;
          color: rgba(255,255,255,0.4);
        }

        .start-quiz-btn {
          padding: 14px 24px;
          background: linear-gradient(135deg, #e94560 0%, #c73e54 100%);
          border: none;
          border-radius: 8px;
          color: white;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }
        .start-quiz-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(233, 69, 96, 0.4);
        }
        .start-quiz-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        /* Active Quiz */
        .quiz-active {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .quiz-progress {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .progress-text {
          font-size: 12px;
          color: rgba(255,255,255,0.6);
        }
        .progress-bar {
          height: 4px;
          background: rgba(255,255,255,0.1);
          border-radius: 2px;
          overflow: hidden;
        }
        .progress-fill {
          height: 100%;
          background: #e94560;
          transition: width 0.3s ease;
        }
        .score-display {
          font-size: 12px;
          color: rgba(255,255,255,0.5);
          text-align: right;
        }

        .question-card {
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 12px;
          padding: 20px;
        }

        .question-meta {
          display: flex;
          gap: 10px;
          margin-bottom: 12px;
        }
        .pattern-tag {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
          color: white;
        }
        .concept-tag {
          padding: 4px 10px;
          background: rgba(255,255,255,0.1);
          border-radius: 4px;
          font-size: 12px;
          color: rgba(255,255,255,0.7);
        }

        .question-text {
          margin: 0 0 20px 0;
          font-size: 16px;
          font-weight: 500;
          color: #fff;
          line-height: 1.5;
        }

        .options-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .option-btn {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 14px 16px;
          background: rgba(255,255,255,0.03);
          border: 2px solid rgba(255,255,255,0.1);
          border-radius: 10px;
          color: rgba(255,255,255,0.85);
          cursor: pointer;
          transition: all 0.15s;
          text-align: left;
        }
        .option-btn:hover {
          background: rgba(255,255,255,0.06);
          border-color: rgba(255,255,255,0.2);
        }
        .option-btn.selected {
          background: rgba(233, 69, 96, 0.15);
          border-color: #e94560;
        }
        .option-letter {
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255,255,255,0.1);
          border-radius: 50%;
          font-size: 12px;
          font-weight: 600;
          flex-shrink: 0;
        }
        .option-btn.selected .option-letter {
          background: #e94560;
          color: white;
        }
        .option-text {
          font-size: 14px;
          line-height: 1.4;
        }

        .question-actions {
          display: flex;
          justify-content: space-between;
          margin-top: 20px;
        }
        .hint-btn {
          padding: 10px 20px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 6px;
          color: rgba(255,255,255,0.7);
          cursor: pointer;
          font-size: 13px;
        }
        .hint-btn:hover {
          background: rgba(255,255,255,0.1);
        }
        .submit-btn {
          padding: 10px 24px;
          background: #e94560;
          border: none;
          border-radius: 6px;
          color: white;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.15s;
        }
        .submit-btn:hover:not(:disabled) {
          background: #d13a52;
        }
        .submit-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        /* Feedback Screen */
        .quiz-feedback {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .feedback-header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px 20px;
          border-radius: 10px;
        }
        .feedback-header.correct {
          background: rgba(76, 175, 80, 0.15);
          border: 1px solid rgba(76, 175, 80, 0.4);
        }
        .feedback-header.incorrect {
          background: rgba(244, 67, 54, 0.15);
          border: 1px solid rgba(244, 67, 54, 0.4);
        }
        .feedback-icon {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          font-size: 18px;
          font-weight: bold;
        }
        .feedback-header.correct .feedback-icon {
          background: #4CAF50;
          color: white;
        }
        .feedback-header.incorrect .feedback-icon {
          background: #f44336;
          color: white;
        }
        .feedback-text {
          font-size: 18px;
          font-weight: 600;
          color: #fff;
        }

        .feedback-details {
          display: flex;
          flex-direction: column;
          gap: 12px;
          padding: 16px;
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
        }
        .feedback-details label {
          font-size: 11px;
          text-transform: uppercase;
          color: rgba(255,255,255,0.5);
          display: block;
          margin-bottom: 4px;
        }
        .feedback-details span {
          font-size: 14px;
          color: rgba(255,255,255,0.85);
        }
        .feedback-details span.correct {
          color: #4CAF50;
        }
        .feedback-details span.incorrect {
          color: #f44336;
        }
        .correct-answer span {
          color: #4CAF50 !important;
          font-weight: 500;
        }

        .feedback-score {
          text-align: center;
          font-size: 14px;
          color: rgba(255,255,255,0.6);
        }

        .next-btn {
          padding: 14px 24px;
          background: #e94560;
          border: none;
          border-radius: 8px;
          color: white;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.15s;
        }
        .next-btn:hover {
          background: #d13a52;
        }

        /* Results Screen */
        .quiz-results {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .results-header {
          text-align: center;
          padding-bottom: 16px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .results-header h3 {
          margin: 0 0 12px 0;
          font-size: 20px;
          color: #fff;
        }
        .final-score {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .score-number {
          font-size: 48px;
          font-weight: 700;
          color: #e94560;
        }
        .score-label {
          font-size: 14px;
          color: rgba(255,255,255,0.6);
        }

        .pattern-breakdown h4,
        .weak-concepts h4,
        .recommendation h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          color: rgba(255,255,255,0.7);
        }

        .pattern-scores {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .pattern-score-item {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .pattern-info {
          display: flex;
          align-items: center;
          gap: 6px;
          width: 40px;
        }
        .pattern-bar-container {
          flex: 1;
          height: 8px;
          background: rgba(255,255,255,0.1);
          border-radius: 4px;
          overflow: hidden;
        }
        .pattern-bar {
          height: 100%;
          border-radius: 4px;
          transition: width 0.5s ease;
        }
        .pattern-pct {
          width: 40px;
          text-align: right;
          font-size: 13px;
          color: rgba(255,255,255,0.7);
        }

        .weak-concepts ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .weak-item {
          display: flex;
          justify-content: space-between;
          padding: 10px 12px;
          background: rgba(244, 67, 54, 0.1);
          border-radius: 6px;
          margin-bottom: 8px;
        }
        .weak-concept {
          font-size: 13px;
          color: #fff;
        }
        .weak-pattern {
          font-size: 12px;
          color: rgba(255,255,255,0.5);
        }

        .recommendation {
          padding: 16px;
          background: rgba(233, 69, 96, 0.1);
          border: 1px solid rgba(233, 69, 96, 0.3);
          border-radius: 8px;
        }
        .recommendation p {
          margin: 0;
          font-size: 14px;
          color: rgba(255,255,255,0.85);
          line-height: 1.5;
        }

        .results-actions {
          display: flex;
          gap: 12px;
        }
        .retry-btn {
          flex: 1;
          padding: 14px 24px;
          background: #e94560;
          border: none;
          border-radius: 8px;
          color: white;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.15s;
        }
        .retry-btn:hover {
          background: #d13a52;
        }
      `}</style>
    </div>
  )
}
