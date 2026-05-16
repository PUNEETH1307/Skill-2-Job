import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useToast } from '../../components/Toast';

interface JobRecommendation {
  job_role_id: number;
  title: string;
  company_name: string;
  compatibility_score: number;
}

interface PredictionData {
  probability: number;
  confidence: string;
  factors: Array<{ factor: string; impact: string }>;
}

interface StudentDashboardData {
  profile_completeness: number;
  skill_count: number;
  skill_breakdown: Record<string, number>;
  matched_job_count: number;
  top_recommendations: JobRecommendation[];
}

export default function StudentDashboard() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [data, setData] = useState<StudentDashboardData | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const [dashRes, predRes] = await Promise.allSettled([
        api.get('/dashboard/student'),
        api.get('/dashboard/student/prediction'),
      ]);
      if (dashRes.status === 'fulfilled') setData(dashRes.value.data);
      if (predRes.status === 'fulfilled') setPrediction(predRes.value.data);
    } catch {
      showToast('Failed to load dashboard', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleLogout = () => {
    logout();
    showToast('Logged out successfully', 'info');
    navigate('/');
  };

  const readinessScore = prediction?.probability ?? 0;
  const profileComplete = data?.profile_completeness ?? 0;

  if (loading) {
    return (
      <div className="student-layout">
        <StudentSidebar active="dashboard" sidebarOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} onLogout={handleLogout} />
        <main className="student-main">
          <div className="dash-loading">Loading dashboard...</div>
        </main>
      </div>
    );
  }

  return (
    <div className="student-layout">
      <StudentSidebar active="dashboard" sidebarOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} onLogout={handleLogout} />

      <main className="student-main">
        {/* Mobile header */}
        <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>☰</button>

        {/* Welcome Section */}
        <div className="welcome-section">
          <div>
            <h1 className="welcome-title">Welcome back, {user?.name ?? 'Student'}! 👋</h1>
            <p className="welcome-sub">Here's your placement journey overview</p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="stats-grid-student">
          <div className="stat-widget stat-widget-primary">
            <div className="stat-widget-icon">🎯</div>
            <div className="stat-widget-value">{readinessScore.toFixed(0)}%</div>
            <div className="stat-widget-label">Placement Readiness</div>
          </div>
          <div className="stat-widget stat-widget-success">
            <div className="stat-widget-icon">📊</div>
            <div className="stat-widget-value">{profileComplete}%</div>
            <div className="stat-widget-label">Profile Complete</div>
          </div>
          <div className="stat-widget stat-widget-info">
            <div className="stat-widget-icon">💼</div>
            <div className="stat-widget-value">{data?.matched_job_count ?? 0}</div>
            <div className="stat-widget-label">Matched Jobs</div>
          </div>
          <div className="stat-widget stat-widget-accent">
            <div className="stat-widget-icon">🛠️</div>
            <div className="stat-widget-value">{data?.skill_count ?? 0}</div>
            <div className="stat-widget-label">Skills</div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="dashboard-grid-2col">
          {/* Left Column */}
          <div className="dashboard-col">
            {/* Placement Prediction */}
            {prediction && (
              <div className="dash-widget">
                <h3 className="dash-widget-title">🤖 AI Placement Prediction</h3>
                <div className="prediction-ring-container">
                  <div className="prediction-ring">
                    <svg viewBox="0 0 100 100" className="prediction-svg">
                      <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="8" />
                      <circle cx="50" cy="50" r="42" fill="none"
                        stroke={readinessScore >= 70 ? '#10b981' : readinessScore >= 40 ? '#f59e0b' : '#ef4444'}
                        strokeWidth="8" strokeLinecap="round"
                        strokeDasharray={`${readinessScore * 2.64} 264`}
                        transform="rotate(-90 50 50)" />
                    </svg>
                    <span className="prediction-ring-value">{readinessScore.toFixed(0)}%</span>
                  </div>
                  <div className="prediction-factors">
                    {prediction.factors.map((f, i) => (
                      <span key={i} className={`factor-badge factor-${f.impact}`}>
                        {f.impact === 'positive' ? '✓' : '✕'} {f.factor}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Skill Breakdown */}
            {data && data.skill_count > 0 && (
              <div className="dash-widget">
                <h3 className="dash-widget-title">📈 Skill Distribution</h3>
                <div className="skill-bars">
                  {Object.entries(data.skill_breakdown).map(([category, count]) => (
                    <div key={category} className="skill-bar-item">
                      <div className="skill-bar-header">
                        <span>{category}</span>
                        <span className="skill-bar-count">{count}</span>
                      </div>
                      <div className="skill-bar-track">
                        <div className="skill-bar-fill" style={{ width: `${Math.min(100, (count / data.skill_count) * 100)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column */}
          <div className="dashboard-col">
            {/* Top Job Recommendations */}
            <div className="dash-widget">
              <div className="dash-widget-header">
                <h3 className="dash-widget-title">💼 Top Job Matches</h3>
                <Link to="/student/jobs" className="dash-widget-link">View All →</Link>
              </div>
              {data && data.top_recommendations.length > 0 ? (
                <div className="job-rec-list">
                  {data.top_recommendations.map((rec) => (
                    <div key={rec.job_role_id} className="job-rec-item">
                      <div className="job-rec-info">
                        <span className="job-rec-title">{rec.title}</span>
                        <span className="job-rec-company">{rec.company_name}</span>
                      </div>
                      <div className="job-rec-score" style={{
                        color: rec.compatibility_score >= 70 ? '#10b981' : rec.compatibility_score >= 40 ? '#f59e0b' : '#ef4444'
                      }}>
                        {rec.compatibility_score.toFixed(0)}%
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-text">Complete your profile to get job recommendations.</p>
              )}
            </div>

            {/* Quick Actions */}
            <div className="dash-widget">
              <h3 className="dash-widget-title">⚡ Quick Actions</h3>
              <div className="quick-actions-grid">
                <Link to="/student/profile" className="quick-action">
                  <span className="quick-action-emoji">👤</span>
                  <span>Profile</span>
                </Link>
                <Link to="/student/resume" className="quick-action">
                  <span className="quick-action-emoji">📄</span>
                  <span>Resume</span>
                </Link>
                <Link to="/student/skills" className="quick-action">
                  <span className="quick-action-emoji">🧠</span>
                  <span>Skills</span>
                </Link>
                <Link to="/student/jobs" className="quick-action">
                  <span className="quick-action-emoji">🎯</span>
                  <span>Jobs</span>
                </Link>
                <Link to="/student/settings" className="quick-action">
                  <span className="quick-action-emoji">⚙️</span>
                  <span>Settings</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

/* Sidebar Component */
interface SidebarProps {
  active: string;
  sidebarOpen: boolean;
  onToggle: () => void;
  onLogout: () => void;
}

function StudentSidebar({ active, sidebarOpen, onToggle, onLogout }: SidebarProps) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '🏠', path: '/student/dashboard' },
    { id: 'profile', label: 'Profile', icon: '👤', path: '/student/profile' },
    { id: 'resume', label: 'Resume', icon: '📄', path: '/student/resume' },
    { id: 'skills', label: 'Skill Analysis', icon: '🧠', path: '/student/skills' },
    { id: 'jobs', label: 'Job Matches', icon: '💼', path: '/student/jobs' },
    { id: 'settings', label: 'Settings', icon: '⚙️', path: '/student/settings' },
  ];

  return (
    <>
      {sidebarOpen && <div className="sidebar-overlay" onClick={onToggle} />}
      <aside className={`student-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <Link to="/">Skill2Job</Link>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <Link
              key={item.id}
              to={item.path}
              className={`sidebar-link ${active === item.id ? 'active' : ''}`}
            >
              <span className="sidebar-link-icon">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <button onClick={onLogout} className="sidebar-logout-btn">
            🚪 Logout
          </button>
        </div>
      </aside>
    </>
  );
}
