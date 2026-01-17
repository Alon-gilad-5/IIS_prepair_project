import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import './InterviewPage.css'

const API_BASE = '/api'

interface Question {
  question_id: number
  question_text: string
  question_type: 'open' | 'code'
  topics?: string[]
  difficulty?: string
}

interface InterviewState {
  currentQuestion: Question | null
  transcript: string
  isRecording: boolean
  isDone: boolean
  progress: { current: number; total: number }
  interviewerMessage: string
}

function InterviewPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  
  const [state, setState] = useState<InterviewState>({
    currentQuestion: null,
    transcript: '',
    isRecording: false,
    isDone: false,
    progress: { current: 0, total: 0 },
    interviewerMessage: '',
  })
  
  const [showSubtitles, setShowSubtitles] = useState(false)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [userTranscript, setUserTranscript] = useState('')
  
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const synthRef = useRef<SpeechSynthesis | null>(null)
  const timerIntervalRef = useRef<number | null>(null)

  // Initialize interview
  useEffect(() => {
    if (!sessionId) return

    const fetchSession = async () => {
      try {
        const response = await fetch(`${API_BASE}/interview/session/${sessionId}`)
        if (!response.ok) throw new Error('Failed to fetch session')
        
        const data = await response.json()
        if (data.plan && data.plan.items && data.plan.items.length > 0) {
          // Get first question from plan
          const firstItem = data.plan.items[0]
          setState(prev => ({
            ...prev,
            currentQuestion: {
              question_id: firstItem.question_id,
              question_text: firstItem.question_text,
              question_type: firstItem.question_type,
              topics: firstItem.topics,
              difficulty: firstItem.difficulty,
            },
            progress: { current: 1, total: data.plan.items.length },
          }))
          
          // Speak first question (optional)
          speakQuestion(firstItem.question_text)
        }
      } catch (error) {
        console.error('Error fetching session:', error)
      }
    }

    fetchSession()
    startTimer()

    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current)
      }
    }
  }, [sessionId])

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      const recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let transcript = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript
        }
        setUserTranscript(transcript)
      }

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error)
        if (event.error === 'no-speech') {
          // Auto-restart if no speech detected
          if (state.isRecording) {
            setTimeout(() => {
              if (state.isRecording && recognitionRef.current) {
                recognitionRef.current.start()
              }
            }, 1000)
          }
        }
      }

      recognitionRef.current = recognition
    }

    synthRef.current = window.speechSynthesis
  }, [])

  const startTimer = () => {
    timerIntervalRef.current = window.setInterval(() => {
      setElapsedTime(prev => prev + 1)
    }, 1000)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const speakQuestion = (text: string) => {
    if (synthRef.current && showSubtitles) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 0.9
      utterance.pitch = 1.0
      synthRef.current.speak(utterance)
    }
  }

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      // Fallback: STT not supported, use text input
      return
    }

    if (state.isRecording) {
      // Stop recording
      recognitionRef.current.stop()
      setState(prev => ({ ...prev, isRecording: false }))
      
      // Submit answer
      submitAnswer(userTranscript)
      setUserTranscript('')
    } else {
      // Start recording
      setUserTranscript('')
      recognitionRef.current.start()
      setState(prev => ({ ...prev, isRecording: true }))
    }
  }

  const submitAnswer = async (transcript: string) => {
    if (!sessionId || !transcript.trim()) return

    try {
      const response = await fetch(`${API_BASE}/interview/next`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: parseInt(sessionId),
          user_transcript: transcript,
          client_metrics: {
            seconds_spoken: elapsedTime,
          },
        }),
      })

      if (!response.ok) throw new Error('Failed to submit answer')

      const data = await response.json()
      
      setState(prev => ({
        ...prev,
        interviewerMessage: data.interviewer_message || '',
        isDone: data.is_done || false,
        progress: data.progress || prev.progress,
        currentQuestion: data.next_question || null,
      }))

      if (data.is_done) {
        navigate(`/feedback/${sessionId}`)
      } else if (data.next_question) {
        speakQuestion(data.next_question.question_text)
      }
    } catch (error) {
      console.error('Error submitting answer:', error)
      alert('Failed to submit answer. Please try again.')
    }
  }

  const handleTextSubmit = () => {
    if (userTranscript.trim()) {
      submitAnswer(userTranscript)
      setUserTranscript('')
    }
  }

  const repeatQuestion = () => {
    if (state.currentQuestion) {
      speakQuestion(state.currentQuestion.question_text)
    }
  }

  const endInterview = () => {
    if (recognitionRef.current && state.isRecording) {
      recognitionRef.current.stop()
    }
    navigate(`/feedback/${sessionId}`)
  }

  const isSTTSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
  const progressPercent = state.progress.total > 0 
    ? (state.progress.current / state.progress.total) * 100 
    : 0

  return (
    <div className="interview-page">
      <div className="interview-header">
        <div className="timer">⏱️ {formatTime(elapsedTime)}</div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
        </div>
        <div className="progress-text">
          Question {state.progress.current} of {state.progress.total}
        </div>
      </div>

      <div className="interview-container">
        <div className="avatar-section">
          <div className="avatar">🤖</div>
          {state.isRecording && (
            <div className="wave-animation">
              <span></span>
              <span></span>
              <span></span>
            </div>
          )}
        </div>

        <div className="question-section">
          {state.currentQuestion && (
            <>
              <div className="question-text">
                {state.currentQuestion.question_text}
              </div>
              {state.currentQuestion.difficulty && (
                <div className="difficulty-badge">
                  {state.currentQuestion.difficulty}
                </div>
              )}
              <div className="question-controls">
                <label className="subtitle-toggle">
                  <input
                    type="checkbox"
                    checked={showSubtitles}
                    onChange={(e) => setShowSubtitles(e.target.checked)}
                  />
                  Show subtitles (May reduce realism)
                </label>
                <button onClick={repeatQuestion} className="repeat-button">
                  🔁 Repeat Question
                </button>
              </div>
            </>
          )}
          
          {state.interviewerMessage && (
            <div className="interviewer-message">
              {state.interviewerMessage}
            </div>
          )}
        </div>

        <div className="transcript-section">
          <h3>Your Answer</h3>
          {isSTTSupported ? (
            <div className="transcript-box">
              {userTranscript || state.transcript || 'Click mic to start recording...'}
            </div>
          ) : (
            <textarea
              className="transcript-input"
              value={userTranscript}
              onChange={(e) => setUserTranscript(e.target.value)}
              placeholder="Type your answer here..."
              rows={6}
            />
          )}
        </div>

        <div className="controls-section">
          {isSTTSupported ? (
            <button
              onClick={toggleRecording}
              className={`mic-button ${state.isRecording ? 'recording' : ''}`}
            >
              {state.isRecording ? '⏹️ Stop' : '🎤 Start Recording'}
            </button>
          ) : (
            <button onClick={handleTextSubmit} className="submit-button">
              Submit Answer
            </button>
          )}
          
          <button onClick={endInterview} className="end-button">
            End Interview
          </button>
        </div>
      </div>
    </div>
  )
}

export default InterviewPage
