import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import SummaryCard from '../../components/SummaryCard';

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
  top_skills_demand: Array<{
    skill: string;
    count: number;
  }>;
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
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAdmin = user?.role === 'admin';
  const endpoint = isAdmin ? '/dashboard/admin' : '/dashboard/coordinator';

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(endpoint);
      setData(response.data);
    } catch {
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  if (loading) {
    return (
      <div className="dash-container">
        <div className="dash-loading">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dash-container">
        <div className="dash-error">
          <p>{error}</p>
          <button onClick={fetchDashboard}>Retry</button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="dash-container">
      <div className="dash-header">
        <h1 className="dash-title">
          {isAdmin ? 'Admin Dashboard' : 'Coordinator Dashboard'}
        </h1>
        <button onClick={logout} className="dash-logout-btn">
          Logout
        </button>
      </div>
      <p className="dash-welcome">
        Welcome, {user?.name ?? 'User'}! Role: {user?.role}
      </p>

      {isAdmin && data && isAdminData(data, user?.role ?? '')
        ? renderAdminView(data)
        : renderCoordinatorView(data as CoordinatorData)}
    </div>
  );
}

function renderCoordinatorView(data: CoordinatorData) {
  return (
    <>
      {/* Placement Overview */}
      <section className="dash-section">
        <h2>Placement Overview</h2>
        <div className="dash-grid">
          <SummaryCard label="Total Students" value={data.placement_overview.total_students} />
          <SummaryCard label="Placed Students" value={data.placement_overview.placed_students} />
          <SummaryCard label="Total Companies" value={data.placement_overview.total_companies} />
          <SummaryCard
            label="Placement %"
            value={`${data.placement_overview.placement_percentage}%`}
            highlight
          />
          <SummaryCard label="Active Jobs" value={data.active_job_count} />
          <SummaryCard label="Shortlisted" value={data.shortlisted_count} />
        </div>
      </section>

      {/* Recent Shortlists */}
      <section className="dash-section">
        <h2>Recent Shortlists</h2>
        {data.recent_shortlists.length === 0 ? (
          <div className="dash-empty-state">
            <p>No recent activity</p>
          </div>
        ) : (
          <table className="dash-recent-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Job Title</th>
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
                  <td>{item.compatibility_score}%</td>
                  <td>{new Date(item.shortlisted_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* Top In-Demand Skills */}
      <section className="dash-section">
        <h2>Top In-Demand Skills</h2>
        <ul>
          {data.top_skills_demand.map((skill, idx) => (
            <li key={idx}>
              {skill.skill} — {skill.count} occurrence{skill.count !== 1 ? 's' : ''}
            </li>
          ))}
        </ul>
      </section>

      {/* Quick Actions */}
      <section className="dash-section">
        <h2>Quick Actions</h2>
        <div className="dash-grid">
          <Link to="/admin/companies" className="dash-card">
            <h3 className="dash-card-title">Companies</h3>
            <p className="dash-card-desc">
              Manage company profiles — add, edit, and view registered companies.
            </p>
          </Link>
          <Link to="/admin/jobs" className="dash-card">
            <h3 className="dash-card-title">Job Roles</h3>
            <p className="dash-card-desc">
              Create and manage job roles with skill requirements and eligibility criteria.
            </p>
          </Link>
          <Link to="/admin/shortlist" className="dash-card">
            <h3 className="dash-card-title">Candidate Shortlisting</h3>
            <p className="dash-card-desc">
              View eligible candidates for job roles and mark them as shortlisted.
            </p>
          </Link>
          <Link to="/admin/analytics" className="dash-card">
            <h3 className="dash-card-title">Placement Analytics</h3>
            <p className="dash-card-desc">
              View placement statistics, department breakdowns, and skill demand analysis.
            </p>
          </Link>
          <Link to="/admin/courses" className="dash-card">
            <h3 className="dash-card-title">Course Recommendations</h3>
            <p className="dash-card-desc">
              Add course recommendations mapped to skills for student skill gap guidance.
            </p>
          </Link>
        </div>
      </section>
    </>
  );
}

function renderAdminView(data: AdminData) {
  return (
    <>
      {/* User Counts */}
      <section className="dash-section">
        <h2>User Overview</h2>
        <div className="dash-grid">
          <SummaryCard label="Students" value={data.user_counts.by_role['student'] ?? 0} />
          <SummaryCard label="Placement Officers" value={data.user_counts.by_role['placement_officer'] ?? 0} />
          <SummaryCard label="Admins" value={data.user_counts.by_role['admin'] ?? 0} />
          <SummaryCard label="Active Users" value={data.user_counts.by_status['active'] ?? 0} />
          <SummaryCard label="Inactive Users" value={data.user_counts.by_status['inactive'] ?? 0} />
          <SummaryCard label="Total Users" value={data.user_counts.total} highlight />
        </div>
      </section>

      {/* Taxonomy Health */}
      <section className="dash-section">
        <h2>Taxonomy Health</h2>
        <div className="dash-grid">
          <SummaryCard label="Total Skills" value={data.taxonomy_health.total_skills} />
          <SummaryCard label="Deprecated Skills" value={data.taxonomy_health.deprecated_skills} />
          <SummaryCard
            label="Uncategorized Pending"
            value={data.taxonomy_health.uncategorized_pending}
            highlight={data.taxonomy_health.uncategorized_pending > 0}
          />
        </div>
      </section>

      {/* Placement Overview */}
      <section className="dash-section">
        <h2>Placement Overview</h2>
        <div className="dash-grid">
          <SummaryCard label="Total Students" value={data.placement_overview.total_students} />
          <SummaryCard label="Placed Students" value={data.placement_overview.placed_students} />
          <SummaryCard label="Total Companies" value={data.placement_overview.total_companies} />
          <SummaryCard
            label="Placement %"
            value={`${data.placement_overview.placement_percentage}%`}
            highlight
          />
        </div>
      </section>

      {/* Quick Actions */}
      <section className="dash-section">
        <h2>Quick Actions</h2>
        <div className="dash-grid">
          <Link to="/admin/companies" className="dash-card">
            <h3 className="dash-card-title">Companies</h3>
            <p className="dash-card-desc">
              Manage company profiles — add, edit, and view registered companies.
            </p>
          </Link>
          <Link to="/admin/jobs" className="dash-card">
            <h3 className="dash-card-title">Job Roles</h3>
            <p className="dash-card-desc">
              Create and manage job roles with skill requirements and eligibility criteria.
            </p>
          </Link>
          <Link to="/admin/shortlist" className="dash-card">
            <h3 className="dash-card-title">Candidate Shortlisting</h3>
            <p className="dash-card-desc">
              View eligible candidates for job roles and mark them as shortlisted.
            </p>
          </Link>
          <Link to="/admin/analytics" className="dash-card">
            <h3 className="dash-card-title">Placement Analytics</h3>
            <p className="dash-card-desc">
              View placement statistics, department breakdowns, and skill demand analysis.
            </p>
          </Link>
          <Link to="/admin/courses" className="dash-card">
            <h3 className="dash-card-title">Course Recommendations</h3>
            <p className="dash-card-desc">
              Add course recommendations mapped to skills for student skill gap guidance.
            </p>
          </Link>
          <Link to="/admin/users" className="dash-card-admin">
            <h3 className="dash-card-title">User Management</h3>
            <p className="dash-card-desc">
              Create accounts, search users, and activate or deactivate user accounts.
            </p>
            <span className="dash-admin-badge">Admin Only</span>
          </Link>
          <Link to="/admin/skills" className="dash-card-admin">
            <h3 className="dash-card-title">Skill Taxonomy</h3>
            <p className="dash-card-desc">
              Manage the skill taxonomy — add, edit, deprecate skills and review uncategorized terms.
            </p>
            <span className="dash-admin-badge">Admin Only</span>
          </Link>
        </div>
      </section>
    </>
  );
}
