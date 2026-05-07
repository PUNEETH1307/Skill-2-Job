import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { AxiosError } from 'axios';

interface JobRecommendation {
  job_role_id: number;
  title: string;
  company: string;
  compatibility_score: number;
  required_skills: string[];
}

export default function JobRecommendations() {
  const [jobs, setJobs] = useState<JobRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const res = await api.get('/jobs/recommendations');
        const data = res.data;
        setJobs(Array.isArray(data) ? data : data.recommendations ?? []);
      } catch (err) {
        if (err instanceof AxiosError && err.response) {
          setError(err.response.data?.error?.message ?? 'Failed to load recommendations.');
        } else {
          setError('Unable to connect to the server.');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchRecommendations();
  }, []);

  if (loading) {
    return (
      <div className="page-container">
        <p className="loading-text"><span className="spinner" /> Loading job recommendations...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Job Recommendations</h1>
        <Link to="/student/dashboard" className="back-link">Back to Dashboard</Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {!error && jobs.length === 0 && (
        <div className="empty-state">
          <p>No job roles currently available.</p>
          <p className="text-muted" style={{ fontSize: '0.85rem' }}>
            Check back later or update your profile to improve matches.
          </p>
        </div>
      )}

      {!error && jobs.length > 0 && (
        <div className="job-list">
          {jobs.map((job) => (
            <div key={job.job_role_id} className="job-card">
              <div className="job-card-header">
                <div>
                  <h3 className="job-title">{job.title}</h3>
                  <p className="job-company">{job.company}</p>
                </div>
                <div className="score-badge">
                  {Math.round(job.compatibility_score * 100)}%
                </div>
              </div>
              <div className="skills-row">
                <span className="skills-label">Required Skills:</span>
                <div className="tags-container">
                  {job.required_skills.map((skill, idx) => (
                    <span key={idx} className="tag">{skill}</span>
                  ))}
                </div>
              </div>
              <Link
                to={`/student/jobs/${job.job_role_id}/gap`}
                className="gap-link"
              >
                View Skill Gap &rarr;
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
