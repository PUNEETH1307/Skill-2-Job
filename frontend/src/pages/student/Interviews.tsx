import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { useToast } from '../../components/Toast';
import { StudentSidebar } from './Dashboard';

interface InterviewRecord {
  id: number;
  interview_date: string;
  interview_time: string | null;
  mode: string;
  venue_or_link: string | null;
  status: string;
  feedback: string | null;
  result: string | null;
  job_title: string | null;
  company_name: string | null;
}

const statusColors: Record<string, string> = {
  scheduled: '#2563eb',
  completed: '#059669',
  cancelled: '#dc2626',
  'no-show': '#d97706',
};

export default function StudentInterviews() {
  const { logout } = useAuth();
  const { showToast } = useToast();
  const [interviews, setInterviews] = useState<InterviewRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fetchInterviews = useCallback(async () => {
    try {
      const response = await api.get('/interviews/my');
      setInterviews(response.data);
    } catch {
      showToast('Failed to load your interviews', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => { fetchInterviews(); }, [fetchInterviews]);

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="student-layout">
      <StudentSidebar
        active="interviews"
        sidebarOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onLogout={handleLogout}
      />
      <main className="student-main">
        <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>☰</button>
        <div className="welcome-section">
          <h1 className="welcome-title">🗓️ My Interviews</h1>
          <p className="welcome-sub">View interview schedules and meeting details.</p>
        </div>

        {loading ? (
          <p className="loading-text"><span className="spinner" /> Loading interviews...</p>
        ) : interviews.length === 0 ? (
          <div className="dash-widget">
            <p className="empty-text">No interviews have been scheduled for you yet.</p>
          </div>
        ) : (
          <div className="dashboard-grid-2col">
            {interviews.map((interview) => (
              <article className="dash-widget" key={interview.id}>
                <div className="dash-widget-header">
                  <h3 className="dash-widget-title">{interview.job_title || 'Interview'}</h3>
                  <span style={{
                    backgroundColor: statusColors[interview.status] || '#64748b',
                    color: 'white', padding: '0.25rem 0.6rem', borderRadius: '999px',
                    fontSize: '0.75rem', textTransform: 'capitalize',
                  }}>{interview.status}</span>
                </div>
                <p style={{ color: 'var(--text-secondary)', margin: '0 0 1rem' }}>
                  {interview.company_name || 'Company not specified'}
                </p>
                <div style={{ display: 'grid', gap: '0.5rem', color: 'var(--text-secondary)' }}>
                  <div><strong>Date:</strong> {interview.interview_date}</div>
                  <div><strong>Time:</strong> {interview.interview_time || 'To be confirmed'}</div>
                  <div><strong>Mode:</strong> <span style={{ textTransform: 'capitalize' }}>{interview.mode}</span></div>
                  {interview.venue_or_link && <div><strong>Venue / Link:</strong> {interview.venue_or_link}</div>}
                  {interview.feedback && <div><strong>Feedback:</strong> {interview.feedback}</div>}
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}