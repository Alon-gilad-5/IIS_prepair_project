import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './Landing.css';

function Landing() {
  const navigate = useNavigate();

  const handleStartInterview = async () => {
    // Ensure user exists
    const { user_id } = await api.ensureUser();
    localStorage.setItem('userId', user_id);
    navigate('/setup');
  };

  const handleImproveCV = async () => {
    // Ensure user exists
    const { user_id } = await api.ensureUser();
    localStorage.setItem('userId', user_id);
    navigate('/setup');
  };

  const handleDashboard = async () => {
    const userId = localStorage.getItem('userId');
    if (!userId) {
      const { user_id } = await api.ensureUser();
      localStorage.setItem('userId', user_id);
      navigate('/dashboard');
    } else {
      navigate('/dashboard');
    }
  };

  return (
    <div className="landing">
      <div className="landing-container">
        <h1>PrepAIr</h1>
        <p className="subtitle">AI-Powered Career Preparation Platform</p>
        
        <div className="action-buttons">
          <button className="btn btn-primary" onClick={handleStartInterview}>
            Start Interview Now
          </button>
          <button className="btn btn-secondary" onClick={handleImproveCV}>
            Improve CV First
          </button>
          <button className="btn btn-tertiary" onClick={handleDashboard}>
            Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}

export default Landing;
