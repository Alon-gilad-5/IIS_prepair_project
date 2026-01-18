import { useParams } from 'react-router-dom'
import './FeedbackPage.css'

function FeedbackPage() {
  const { sessionId } = useParams<{ sessionId: string }>()

  return (
    <div className="feedback-page">
      <div className="container">
        <h1>📊 Interview Feedback</h1>
        <p className="message">
          Thank you for completing the interview! The feedback step is next.
        </p>
        <p className="session-id">
          Session ID: {sessionId}
        </p>
        <div className="placeholder-box">
          <p>📝 Detailed feedback and analysis will be displayed here.</p>
          <p>This feature is coming soon!</p>
        </div>
      </div>
    </div>
  )
}

export default FeedbackPage
