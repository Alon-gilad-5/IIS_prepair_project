import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './StartPage.css'

const API_BASE = '/api'

interface StartInterviewRequest {
  mode: 'direct' | 'after_cv'
  cv_text: string
  jd_text: string
  cv_version_id?: string
  settings?: {
    num_open?: number
    num_code?: number
    duration_minutes?: number
  }
}

function StartPage() {
  const navigate = useNavigate()
  const [cvText, setCvText] = useState('')
  const [jdText, setJdText] = useState('')
  const [mode, setMode] = useState<'direct' | 'after_cv'>('direct')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStartInterview = async () => {
    if (!jdText.trim()) {
      setError('Please provide a Job Description')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const request: StartInterviewRequest = {
        mode,
        cv_text: cvText,
        jd_text: jdText,
        settings: {
          num_open: 5,
          num_code: 3,
          duration_minutes: 30,
        },
      }

      const response = await fetch(`${API_BASE}/interview/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to start interview')
      }

      const data = await response.json()
      navigate(`/interview/${data.session_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start interview')
      setLoading(false)
    }
  }

  return (
    <div className="start-page">
      <div className="container">
        <h1>🎤 PrepAIr Interview Simulator</h1>
        <p className="subtitle">Practice your interview skills with AI-powered questions</p>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        <div className="form-section">
          <div className="mode-selector">
            <label>
              <input
                type="radio"
                value="direct"
                checked={mode === 'direct'}
                onChange={(e) => setMode(e.target.value as 'direct' | 'after_cv')}
              />
              Direct Mode (Skip CV improvement)
            </label>
            <label>
              <input
                type="radio"
                value="after_cv"
                checked={mode === 'after_cv'}
                onChange={(e) => setMode(e.target.value as 'direct' | 'after_cv')}
              />
              After CV Mode (Use improved CV)
            </label>
          </div>

          <div className="input-group">
            <label htmlFor="cv-text">CV Text (Optional for direct mode)</label>
            <textarea
              id="cv-text"
              value={cvText}
              onChange={(e) => setCvText(e.target.value)}
              placeholder="Paste your CV text here..."
              rows={8}
            />
          </div>

          <div className="input-group">
            <label htmlFor="jd-text">Job Description *</label>
            <textarea
              id="jd-text"
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the job description here..."
              rows={10}
              required
            />
          </div>

          <button
            onClick={handleStartInterview}
            disabled={loading || !jdText.trim()}
            className="start-button"
          >
            {loading ? 'Starting...' : '🚀 Start Interview'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default StartPage
