import { useParams } from 'react-router-dom';
import './FeedbackPlaceholder.css';

function FeedbackPlaceholder() {
  const { sessionId } = useParams<{ sessionId: string }>();

  return (
    <div className="feedback-placeholder">
      <div className="container">
        <h1>Feedback</h1>
        <p>Feedback feature is not yet implemented.</p>
        <p>Session ID: {sessionId}</p>
        <p>This is a placeholder page. The feedback system will be implemented in a future update.</p>
      </div>
    </div>
  );
}

export default FeedbackPlaceholder;
