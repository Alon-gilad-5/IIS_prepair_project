import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import './PreInterview.css';

function PreInterview() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('sessionId');
  const [voiceOn, setVoiceOn] = useState(true);
  const [captionsOn, setCaptionsOn] = useState(true);
  const [realismMode, setRealismMode] = useState('realistic');

  const handleStart = () => {
    if (!sessionId) {
      alert('Session ID missing');
      return;
    }
    navigate(`/interview/${sessionId}`);
  };

  return (
    <div className="pre-interview">
      <div className="container">
        <h1>Interview Setup</h1>
        <p>Review your session plan and adjust settings</p>

        <div className="plan-summary">
          <h2>Session Plan</h2>
          <p>You'll be asked behavioral and technical questions tailored to your CV and job description.</p>
        </div>

        <div className="settings">
          <h2>Settings</h2>
          
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={voiceOn}
                onChange={(e) => setVoiceOn(e.target.checked)}
              />
              Voice On/Off
            </label>
          </div>

          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={captionsOn}
                onChange={(e) => setCaptionsOn(e.target.checked)}
              />
              Captions On/Off
              <span className="tooltip">⚠️ Captions may reduce realism</span>
            </label>
          </div>

          <div className="setting-item">
            <label>
              Realism Mode:
              <select value={realismMode} onChange={(e) => setRealismMode(e.target.value)}>
                <option value="realistic">Realistic</option>
                <option value="practice">Practice Mode</option>
              </select>
            </label>
          </div>
        </div>

        <button className="btn btn-primary" onClick={handleStart}>
          Start Interview
        </button>
      </div>
    </div>
  );
}

export default PreInterview;
