import { useParams, useNavigate } from 'react-router-dom';
import './Done.css';

function Done() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const handleContinueToFeedback = () => {
    if (sessionId) {
      navigate(`/feedback/${sessionId}`);
    }
  };

  const handleDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <div className="done">
      <div className="container">
        <h1>✅ Interview Complete!</h1>
        <p>Thank you for completing the interview.</p>
        
        <div className="actions">
          <button className="btn btn-primary" onClick={handleContinueToFeedback}>
            Continue to Feedback
          </button>
          <button className="btn btn-secondary" onClick={handleDashboard}>
            View Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}

export default Done;
