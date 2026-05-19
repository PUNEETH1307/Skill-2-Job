import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useToast } from '../../components/Toast';

interface PlacementOverview {
  total_students: number;
  placed_students: number;
  total_companies: number;
  placement_percentage: number;
}

interface CoordinatorData {
  placement_overview: PlacementOverview;
  active_job_count: number;
  shortlisted_count: number;
  recent_shortlists: Array<{
    student_name: string;
    job_title: string;
    company_name: string;
    compatibility_score: number;
    shortlisted_at: string;
  }>;
  top_skills_demand: Array<{ skill: string; count: number }>;
}

interface AdminData {
  user_counts: {
    by_role: Record<string, number>;
    by_status: Record<string, number>;
    total: number;
  };
  taxonomy_health: {
    total_skills: number;
    deprecated_skills: number;
    uncategorized_pending: number;
  };
  placement_overview: PlacementOverview;
}

type DashboardData = CoordinatorData | AdminData;

function isAdminData(_data: DashboardData, role: string): _data is AdminData {
  return role === 'admin';
}

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isAdmin = user?.role === 'admin';
  const endpoint = isAdmin ? '/dashboard/admin' : '/dashboard/coordinator';

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(endpoint);
      setData(response.data);
    } catch {
      showToast('Failed to load dashboard', 'error');
    } finally {
      setLoading(false);
    }
  }, [endpoint, showToast]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleLogout = () => {
    logout();
    showToast('Logged out successfully', 'info');
    navigate('/');
  };

  if (loading) {
    return (
      <div className="admin-layout">
        <AdminSidebar active="dashboard" isAdmin={isAdmin} sidebarOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} onLogout={handleLogout} />
        <main className="admin-main">
          <div className="dash-loading">Loading dashboard...</div>
        </main>
      </div>
    );
  }

  return (
    <div className="admin-layout">
      <AdminSidebar active="dashboard" isAdmin={isAdmin} sidebarOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} onLogout={handleLogout} />

      <main className="admin-main">
        <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>☰</button>

        {/* Welcome */}
        <div className="welcome-section">
          <div>
            <h1 className="welcome-title">
              {isAdmin ? 'Admin Dashboard' : 'Placement Coordinator'} 🏢
            </h1>
            <p className="welcome-sub">Welcome, {user?.name}! Manage the placement ecosystem.</p>
          </div>
        </div>

        {data && isAdmin && isAdminData(data, user?.role ?? '') ? (
          <AdminView data={data} />
        ) : data ? (
          <CoordinatorView data={data as CoordinatorData} />
        ) : null}
      </main>
    </div>
  );
}

function CoordinatorView({ data }: { data: CoordinatorData }) {
  return (
    <>
      {/* Stats */}
      <div className="stats-grid-student">
        <div className="stat-widget stat-widget-primary">
          <div className="stat-widget-icon">👨‍🎓</div>
          <div className="stat-widget-value">{data.placement_overview.total_students}</div>
          <div className="stat-widget-label">Total Students</div>
        </div>
        <div className="stat-widget stat-widget-success">
          <div className="stat-widget-icon">✅</div>
          <div className="stat-widget-value">{data.placement_overview.placed_students}</div>
          <div className="stat-widget-label">Placed</div>
        </div>
        <div className="stat-widget stat-widget-info">
          <div className="stat-widget-icon">🏢</div>
          <div className="stat-widget-value">{data.placement_overview.total_companies}</div>
          <div className="stat-widget-label">Companies</div>
        </div>
        <div className="stat-widget stat-widget-accent">
          <div className="stat-widget-icon">📈</div>
          <div className="stat-widget-value">{data.placement_overview.placement_percentage}%</div>
          <div className="stat-widget-label">Placement Rate</div>
        </div>
      </div>

      <div className="stats-grid-student" style={{ marginTop: '1rem' }}>
        <div className="stat-widget">
          <div className="stat-widget-icon">💼</div>
          <div className="stat-widget-value">{data.active_job_count}</div>
          <div className="stat-widget-label">Active Jobs</div>
        </div>
        <div className="stat-widget">
          <div className="stat-widget-icon">📋</div>
          <div className="stat-widget-value">{data.shortlisted_count}</div>
          <div className="stat-widget-label">Shortlisted</div>
        </div>
      </div>

      {/* Recent Shortlists */}
      <div className="dash-widget" style={{ marginTop: '1.5rem' }}>
        <h3 className="dash-widget-title">📋 Recent Shortlists</h3>
        {data.recent_shortlists.length === 0 ? (
          <p className="empty-text">No recent activity</p>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Job</th>
                  <th>Company</th>
                  <th>Score</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_shortlists.map((item, idx) => (
                  <tr key={idx}>
                    <td>{item.student_name}</td>
                    <td>{item.job_title}</td>
                    <td>{item.company_name}</td>
                    <td><strong>{item.compatibility_score}%</strong></td>
                    <td>{new Date(item.shortlisted_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Top Skills */}
      <div className="dash-widget" style={{ marginTop: '1.5rem' }}>
        <h3 className="dash-widget-title">🔥 Top In-Demand Skills</h3>
        <div className="skill-bars">
          {data.top_skills_demand.slice(0, 8).map((s, idx) => (
            <div key={idx} className="skill-bar-item">
              <div className="skill-bar-header">
                <span>{s.skill}</span>
                <span className="skill-bar-count">{s.count}</span>
              </div>
              <div className="skill-bar-track">
                <div className="skill-bar-fill" style={{
                  width: `${Math.min(100, (s.count / Math.max(...data.top_skills_demand.map(d => d.count))) * 100)}%`
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function AdminView({ data }: { data: AdminData }) {
  return (
    <>
      {/* Stats */}
      <div className="stats-grid-student">
        <div className="stat-widget stat-widget-primary">
          <div className="stat-widget-icon">👥</div>
          <div className="stat-widget-value">{data.user_counts.total}</div>
          <div className="stat-widget-label">Total Users</div>
        </div>
        <div className="stat-widget stat-widget-success">
          <div className="stat-widget-icon">✅</div>
          <div className="stat-widget-value">{data.placement_overview.placed_students}</div>
          <div className="stat-widget-label">Placed</div>
        </div>
        <div className="stat-widget stat-widget-info">
          <div className="stat-widget-icon">🧠</div>
          <div className="stat-widget-value">{data.taxonomy_health.total_skills}</div>
          <div className="stat-widget-label">Skills in Taxonomy</div>
        </div>
        <div className="stat-widget stat-widget-accent">
          <div className="stat-widget-icon">📈</div>
          <div className="stat-widget-value">{data.placement_overview.placement_percentage}%</div>
          <div className="stat-widget-label">Placement Rate</div>
        </div>
      </div>

      {/* User Breakdown */}
      <div className="dashboard-grid-2col" style={{ marginTop: '1.5rem' }}>
        <div className="dash-widget">
          <h3 className="dash-widget-title">👥 Users by Role</h3>
          <div className="admin-stat-list">
            {Object.entries(data.user_counts.by_role).map(([role, count]) => (
              <div key={role} className="admin-stat-row">
                <span className="admin-stat-label">{role.replace('_', ' ')}</span>
                <span className="admin-stat-value">{count}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="dash-widget">
          <h3 className="dash-widget-title">🛡️ System Health</h3>
          <div className="admin-stat-list">
            <div className="admin-stat-row">
              <span className="admin-stat-label">Active Skills</span>
              <span className="admin-stat-value">{data.taxonomy_health.total_skills}</span>
            </div>
            <div className="admin-stat-row">
              <span className="admin-stat-label">Deprecated Skills</span>
              <span className="admin-stat-value">{data.taxonomy_health.deprecated_skills}</span>
            </div>
            <div className="admin-stat-row">
              <span className="admin-stat-label">Pending Review</span>
              <span className="admin-stat-value" style={{ color: data.taxonomy_health.uncategorized_pending > 0 ? 'var(--warning)' : 'inherit' }}>
                {data.taxonomy_health.uncategorized_pending}
              </span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

/* Admin Sidebar */
interface SidebarProps {
  active: string;
  isAdmin: boolean;
  sidebarOpen: boolean;
  onToggle: () => void;
  onLogout: () => void;
}

function AdminSidebar({ active, isAdmin, sidebarOpen, onToggle, onLogout }: SidebarProps) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '🏠', path: '/admin/dashboard' },
    { id: 'companies', label: 'Companies', icon: '🏢', path: '/admin/companies' },
    { id: 'jobs', label: 'Job Roles', icon: '💼', path: '/admin/jobs' },
    { id: 'shortlist', label: 'Shortlist', icon: '📋', path: '/admin/shortlist' },
    { id: 'interviews', label: 'Interviews', icon: '🗓️', path: '/admin/interviews' },
    { id: 'placements', label: 'Placements', icon: '🎓', path: '/admin/placements' },
    { id: 'analytics', label: 'Analytics', icon: '📊', path: '/admin/analytics' },
    { id: 'courses', label: 'Courses', icon: '📚', path: '/admin/courses' },
    { id: 'notifications', label: 'Notifications', icon: '🔔', path: '/admin/notifications' },
    ...(isAdmin ? [
      { id: 'users', label: 'User Management', icon: '👥', path: '/admin/users' },
      { id: 'skills', label: 'Skill Taxonomy', icon: '🧠', path: '/admin/skills' },
    ] : []),
  ];

  return (
    <>
      {sidebarOpen && <div className="sidebar-overlay" onClick={onToggle} />}
      <aside className={`admin-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <Link to="/">Skill2Job</Link>
          <span className="sidebar-role-badge">{isAdmin ? 'Admin' : 'Officer'}</span>
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
