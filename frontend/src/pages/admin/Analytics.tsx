import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

interface OverviewStats {
  total_students: number;
  placed_students: number;
  total_companies: number;
  placement_percentage: number;
}

interface DeptBreakdown {
  department: string;
  count: number;
  percentage: number;
}

interface CompanyBreakdown {
  company: string;
  count: number;
}

interface SkillDemand {
  skill: string;
  count: number;
}

interface PredictionEntry {
  student_id: number;
  name: string;
  cgpa: number | null;
  probability: number;
}

interface AnalyticsData {
  overview: OverviewStats;
  department_breakdown: DeptBreakdown[];
  company_breakdown: CompanyBreakdown[];
  skill_demand: SkillDemand[];
}

export default function Analytics() {
  const { logout } = useAuth();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [predictions, setPredictions] = useState<PredictionEntry[]>([]);
  const [predLoading, setPredLoading] = useState(false);
  const [predTrained, setPredTrained] = useState(false);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const params: Record<string, string> = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await api.get('/admin/analytics', { params });
      setData(res.data);
    } catch {
      setError('Failed to load analytics.');
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const handleFilter = (e: React.FormEvent) => {
    e.preventDefault();
    fetchAnalytics();
  };

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Placement Analytics</h1>
        <div className="page-header-actions">
          <Link to="/admin/dashboard" className="back-link">
            ← Dashboard
          </Link>
          <button onClick={logout} className="dash-logout-btn">
            Logout
          </button>
        </div>
      </div>

      {/* Date Filter */}
      <form onSubmit={handleFilter} className="filter-row">
        <label className="label-col">
          From
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="input"
          />
        </label>
        <label className="label-col">
          To
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="input"
          />
        </label>
        <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-end' }}>
          Apply Filter
        </button>
        {(dateFrom || dateTo) && (
          <button
            type="button"
            onClick={() => {
              setDateFrom('');
              setDateTo('');
            }}
            className="btn btn-secondary"
            style={{ alignSelf: 'flex-end' }}
          >
            Clear
          </button>
        )}
      </form>

      {loading ? (
        <p className="loading-text"><span className="spinner" /> Loading analytics...</p>
      ) : error ? (
        <p className="error-text">{error}</p>
      ) : data ? (
        <>
          {/* Overview Stats */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{data.overview.total_students}</div>
              <div className="stat-label">Total Students</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.overview.placed_students}</div>
              <div className="stat-label">Placed Students</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.overview.total_companies}</div>
              <div className="stat-label">Companies</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {data.overview.placement_percentage.toFixed(1)}%
              </div>
              <div className="stat-label">Placement Rate</div>
            </div>
          </div>

          {/* Department Breakdown */}
          <div className="page-section">
            <h2 className="section-title">Department-wise Breakdown</h2>
            {data.department_breakdown.length === 0 ? (
              <p className="muted-text">No placement records found.</p>
            ) : (
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Department</th>
                      <th>Placed</th>
                      <th>Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.department_breakdown.map((d) => (
                      <tr key={d.department}>
                        <td>{d.department}</td>
                        <td>{d.count}</td>
                        <td>{d.percentage.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Company Breakdown */}
          <div className="page-section">
            <h2 className="section-title">Company-wise Breakdown</h2>
            {data.company_breakdown.length === 0 ? (
              <p className="muted-text">No placement records found.</p>
            ) : (
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Company</th>
                      <th>Students Placed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.company_breakdown.map((c) => (
                      <tr key={c.company}>
                        <td>{c.company}</td>
                        <td>{c.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Skill Demand */}
          <div className="page-section">
            <h2 className="section-title">Skill Demand Analysis</h2>
            {data.skill_demand.length === 0 ? (
              <p className="muted-text">No active job roles found.</p>
            ) : (
              <div className="skill-demand-bars">
                {data.skill_demand.slice(0, 10).map((s) => (
                  <div key={s.skill} className="demand-bar-item">
                    <span className="demand-skill-name">{s.skill}</span>
                    <div className="demand-bar-container">
                      <div
                        className="demand-bar"
                        style={{
                          width: `${Math.min(100, (s.count / Math.max(...data.skill_demand.map(d => d.count))) * 100)}%`
                        }}
                      />
                    </div>
                    <span className="demand-count">{s.count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Placement Prediction */}
          <div className="page-section">
            <h2 className="section-title">Placement Success Prediction (AI)</h2>
            <p className="helper-text">
              Uses Random Forest ML model to predict placement probability based on CGPA, skills, projects, and certifications.
            </p>
            <div className="btn-row" style={{ marginBottom: '1rem' }}>
              <button
                onClick={async () => {
                  setPredLoading(true);
                  try {
                    await api.post('/admin/predictions/train');
                    setPredTrained(true);
                    const res = await api.get('/admin/predictions/batch');
                    setPredictions(res.data.predictions ?? []);
                  } catch {
                    // Try batch without training
                    try {
                      const res = await api.get('/admin/predictions/batch');
                      setPredictions(res.data.predictions ?? []);
                    } catch { /* ignore */ }
                  } finally {
                    setPredLoading(false);
                  }
                }}
                disabled={predLoading}
                className="btn btn-primary"
              >
                {predLoading ? 'Computing...' : 'Run Prediction'}
              </button>
              {predTrained && (
                <span className="muted-text" style={{ alignSelf: 'center' }}>
                  ✓ Model trained
                </span>
              )}
            </div>

            {predictions.length > 0 && (
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Student</th>
                      <th>CGPA</th>
                      <th>Placement Probability</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions.slice(0, 20).map((p, idx) => (
                      <tr key={p.student_id}>
                        <td>{idx + 1}</td>
                        <td>{p.name}</td>
                        <td>{p.cgpa != null ? p.cgpa.toFixed(2) : '—'}</td>
                        <td>
                          <div className="prediction-cell">
                            <div className="prediction-bar-container">
                              <div
                                className="prediction-bar"
                                style={{
                                  width: `${p.probability}%`,
                                  backgroundColor: p.probability >= 70 ? '#16a34a' : p.probability >= 40 ? '#ca8a04' : '#dc2626',
                                }}
                              />
                            </div>
                            <span className="prediction-value">{p.probability}%</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}
