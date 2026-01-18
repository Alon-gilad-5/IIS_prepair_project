import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './Dashboard.css';

function Dashboard() {
  const navigate = useNavigate();
  const [overview, setOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProgress = async () => {
      const userId = localStorage.getItem('userId');
      const jobSpecId = localStorage.getItem('jobSpecId');

      if (!userId) {
        navigate('/');
        return;
      }

      try {
        const result = await api.getProgressOverview(userId, jobSpecId || undefined);
        setOverview(result);
      } catch (error: any) {
        alert(`Error loading progress: ${error.message}`);
      } finally {
        setLoading(false);
      }
    };

    loadProgress();
  }, [navigate]);

  if (loading) {
    return <div className="dashboard loading">Loading dashboard...</div>;
  }

  const snapshot = overview?.latest_snapshot;

  const handleOCEANTest = () => {
    // Navigate to OCEAN test page or open in new tab
    window.open('/ocean-test', '_blank');
    // Or use navigate if you have an OCEAN test route
    // navigate('/ocean-test');
  };

  return (
    <div className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <div>
            <h1>Dashboard</h1>
            <p>Your readiness progress</p>
          </div>
          <div className="dashboard-actions">
            <button className="btn btn-secondary" onClick={() => navigate('/')}>
              History
            </button>
            <button className="btn btn-secondary" onClick={() => window.location.reload()}>
              Self-Progress
            </button>
            <button className="btn btn-ocean" onClick={handleOCEANTest}>
              OCEAN Test
            </button>
          </div>
        </div>

        {snapshot ? (
          <>
            <div className="readiness-section">
              <h2>Readiness Score: {snapshot.readiness_score.toFixed(1)}%</h2>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${snapshot.readiness_score}%` }}
                />
              </div>
            </div>

            <div className="breakdown">
              <h3>Breakdown</h3>
              <div className="breakdown-grid">
                <div className="breakdown-item">
                  <label>CV Score</label>
                  <span>{snapshot.cv_score.toFixed(1)}%</span>
                </div>
                <div className="breakdown-item">
                  <label>Interview Score</label>
                  <span>{snapshot.interview_score.toFixed(1)}%</span>
                </div>
                <div className="breakdown-item">
                  <label>Practice Score</label>
                  <span>{snapshot.practice_score.toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {overview.trend && overview.trend.length > 0 && (
              <div className="trend">
                <h3>Trend</h3>
                <p>Showing last {overview.trend.length} snapshots</p>
              </div>
            )}
          </>
        ) : (
          <div className="no-data">
            <p>No progress data available yet.</p>
            <p>Complete a CV analysis or interview to see your readiness score.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
