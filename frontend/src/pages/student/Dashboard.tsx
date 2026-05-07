import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import SummaryCard from '../../components/SummaryCard';

interface JobRecommendation {
  job_role_id: number;
  title: string;
  company_name: string;
  compatibility_score: number;
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
  const [data, setData] = useState<StudentDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/dashboard/student');
      setData(response.data);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to load dashboard data';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return (
    <div className="dash-container">
      <div className="dash-header">
        <h1 className="dash-title">Student Dashboard</h1>
        <button onClick={logout} className="dash-logout-btn">
          Logout
        </button>
      </div>
      <p className="dash-welcome">Welcome, {user?.name ?? 'Student'}!</p>

      {loading && (
        <div className="dash-loading">Loading dashboard...</div>
      )}

      {error && (
        <div className="dash-error">
          <p>{error}</p>
          <button onClick={fetchDashboard}>Retry</button>
        </div>
      )}

      {!loading && !error && data && (
        <>
          {/* Empty state: profile completeness is 0 */}
          {data.profile_completeness === 0 && (
            <div className="dash-empty-state">
              <p>Your profile is not set up yet. Complete your profile to get personalized job recommendations and skill analysis.</p>
              <Link to="/student/profile" className="dash-card">
                Complete Your Profile
              </Link>
            </div>
          )}

          {/* Summary Cards */}
          <section className="dash-section">
            <h2>Overview</h2>
            <div className="dash-grid">
              <SummaryCard
                label="Profile Completeness"
                value={`${data.profile_completeness}%`}
                highlight={data.profile_completeness < 100}
              />
              <SummaryCard
                label="Skills"
                value={data.skill_count}
              />
              <SummaryCard
                label="Matched Jobs"
                value={data.matched_job_count}
              />
            </div>
          </section>

          {/* Skill Breakdown */}
          <section className="dash-section">
            <h2>Skill Breakdown</h2>
            {data.skill_count === 0 ? (
              <div className="dash-empty-state">
                <p>No skills have been added yet. Update your profile to add skills and see your skill breakdown.</p>
              </div>
            ) : (
              <ul className="dash-grid">
                {Object.entries(data.skill_breakdown).map(([category, count]) => (
                  <li key={category} className="dash-card">
                    <h3 className="dash-card-title">{category}</h3>
                    <p className="dash-card-desc">{count} skill{count !== 1 ? 's' : ''}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Top Job Recommendations */}
          <section className="dash-section">
            <h2>Top Job Recommendations</h2>
            {data.matched_job_count === 0 ? (
              <div className="dash-empty-state">
                <p>No job roles are currently available. Check back later for new opportunities.</p>
              </div>
            ) : data.top_recommendations.length === 0 ? (
              <div className="dash-empty-state">
                <p>No recommendations available yet. Complete your profile to get matched with jobs.</p>
              </div>
            ) : (
              <ul className="dash-grid">
                {data.top_recommendations.map((rec) => (
                  <li key={rec.job_role_id} className="dash-card">
                    <h3 className="dash-card-title">{rec.title}</h3>
                    <p className="dash-card-desc">{rec.company_name}</p>
                    <p className="dash-card-desc">
                      Compatibility: {rec.compatibility_score.toFixed(1)}%
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Quick Actions */}
          <section className="dash-section">
            <h2>Quick Actions</h2>
            <div className="dash-grid">
              <Link
                to="/student/profile"
                className={`dash-card${data.profile_completeness < 100 ? ' dash-card-highlight' : ''}`}
              >
                <h3 className="dash-card-title">My Profile</h3>
                <p className="dash-card-desc">
                  Manage your academic details, skills, projects, and certifications.
                </p>
              </Link>

              <Link to="/student/skills" className="dash-card">
                <h3 className="dash-card-title">Skill Analysis</h3>
                <p className="dash-card-desc">
                  View your categorized skill breakdown and analysis.
                </p>
              </Link>

              <Link to="/student/jobs" className="dash-card">
                <h3 className="dash-card-title">Job Recommendations</h3>
                <p className="dash-card-desc">
                  Browse job roles matched to your skills with compatibility scores.
                </p>
              </Link>

              <Link to="/student/resume" className="dash-card">
                <h3 className="dash-card-title">Resume</h3>
                <p className="dash-card-desc">
                  Generate and download your professional resume as PDF.
                </p>
              </Link>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
