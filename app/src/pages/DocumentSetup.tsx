import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './DocumentSetup.css';

function DocumentSetup() {
  const navigate = useNavigate();
  const [cvText, setCvText] = useState('');
  const [jdText, setJdText] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAnalyzeAndImprove = async () => {
    const userId = localStorage.getItem('userId');
    if (!userId || !cvText || !jdText) {
      alert('Please provide both CV and JD text');
      return;
    }

    setLoading(true);
    try {
      // Ingest CV and JD
      const cvResult = await api.ingestCV(userId, cvText);
      const jdResult = await api.ingestJD(userId, jdText);

      // Analyze CV
      await api.analyzeCV(userId, cvResult.cv_version_id, jdResult.job_spec_id);

      // Store IDs for CV improve page
      localStorage.setItem('cvVersionId', cvResult.cv_version_id);
      localStorage.setItem('jobSpecId', jdResult.job_spec_id);
      localStorage.setItem('cvText', cvText);

      navigate('/cv-improve');
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSkipToInterview = async () => {
    const userId = localStorage.getItem('userId');
    if (!userId || !cvText || !jdText) {
      alert('Please provide both CV and JD text');
      return;
    }

    setLoading(true);
    try {
      // Ingest CV and JD
      const cvResult = await api.ingestCV(userId, cvText);
      const jdResult = await api.ingestJD(userId, jdText);

      // Start interview
      const sessionResult = await api.startInterview(
        userId,
        jdResult.job_spec_id,
        cvResult.cv_version_id,
        'direct',
        { num_open: 4, num_code: 2, duration_minutes: 12 }
      );

      navigate(`/pre-interview?sessionId=${sessionResult.session_id}`);
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="document-setup">
      <div className="container">
        <h1>Document Setup</h1>
        <p>Paste your CV and Job Description below</p>

        <div className="input-group">
          <label>CV Text</label>
          <textarea
            value={cvText}
            onChange={(e) => setCvText(e.target.value)}
            placeholder="Paste your CV text here..."
            rows={15}
          />
        </div>

        <div className="input-group">
          <label>Job Description</label>
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="Paste the job description here..."
            rows={15}
          />
        </div>

        <div className="action-buttons">
          <button
            className="btn btn-primary"
            onClick={handleAnalyzeAndImprove}
            disabled={loading || !cvText || !jdText}
          >
            {loading ? 'Processing...' : 'Analyze & Improve CV'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleSkipToInterview}
            disabled={loading || !cvText || !jdText}
          >
            {loading ? 'Starting...' : 'Skip to Interview'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default DocumentSetup;
