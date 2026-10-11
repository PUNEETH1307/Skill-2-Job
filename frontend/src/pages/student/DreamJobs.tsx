import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

interface JobRole {
  id: number;
  company_id: number;
  company_name: string;
  title: string;
  required_skills: string[];
}

interface DreamJob {
  id: number;
  job_role_id: number;
  company_name: string;
  title: string;
  required_skills: string[];
  skill_gaps: Array<{ skill: string; reason: string }>;
  recommended_skills: string[];
  analysis_status: string;
}

interface HiringUpdate {
  dream_job_id: number;
  job_role_id: number;
  company_name: string;
  role_title: string;
  last_checked_at: string;
  live_jobs: Array<{ title: string; company_name: string; apply_url: string; source: string; location?: string | null }>;
  preparation_resources: Array<{ title: string; provider: string; url: string }>;
}

interface Company { id: number; name: string; }

export default function DreamJobs() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [roles, setRoles] = useState<JobRole[]>([]);
  const [dreamJobs, setDreamJobs] = useState<DreamJob[]>([]);
  const [updates, setUpdates] = useState<HiringUpdate[]>([]);
  const [updateRoleId, setUpdateRoleId] = useState('all');
  const [companyId, setCompanyId] = useState('');
  const [roleId, setRoleId] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const [options, saved] = await Promise.all([
        api.get('/jobs/options'),
        api.get('/jobs/dream-jobs'),
      ]);
      setCompanies(options.data.companies ?? []);
      setRoles(options.data.job_roles ?? []);
      setDreamJobs(saved.data ?? []);
      const updateResponse = await api.get('/jobs/dream-jobs/updates');
      setUpdates(updateResponse.data ?? []);
    } catch (err: any) {
      setError(err.response?.data?.error?.message ?? 'Unable to load Dream Jobs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const addDreamJob = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!roleId) return;
    setSaving(true);
    setError('');
    try {
      const response = await api.post('/jobs/dream-jobs', { job_role_id: Number(roleId) });
      setDreamJobs((current) => [...current, response.data]);
      setCompanyId('');
      setRoleId('');
    } catch (err: any) {
      setError(err.response?.data?.error?.message ?? 'Unable to save Dream Job.');
    } finally {
      setSaving(false);
    }
  };

  const removeDreamJob = async (id: number) => {
    try {
      await api.delete(`/jobs/dream-jobs/${id}`);
      setDreamJobs((current) => current.filter((job) => job.id !== id));
      setUpdates((current) => current.filter((update) => update.dream_job_id !== id));
    } catch (err: any) {
      setError(err.response?.data?.error?.message ?? 'Unable to remove Dream Job.');
    }
  };

  const loadUpdates = async (roleIdFilter: string) => {
    setUpdateRoleId(roleIdFilter);
    try {
      const response = await api.get('/jobs/dream-jobs/updates', {
        params: roleIdFilter === 'all' ? {} : { role_id: Number(roleIdFilter) },
      });
      setUpdates(response.data ?? []);
    } catch (err: any) {
      setError(err.response?.data?.error?.message ?? 'Unable to refresh hiring updates.');
    }
  };

  const filteredRoles = companyId
    ? roles.filter((role) => role.company_id === Number(companyId))
    : [];

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dream Jobs</h1>
          <p className="text-muted">Choose up to 3 company-specific roles. AI compares each role with your current skills.</p>
        </div>
        <Link to="/student/dashboard" className="back-link">Back to Dashboard</Link>
      </div>

      <div className="alert alert-warning">
        <strong>Placement registration rule:</strong> if you are eligible for a drive and do not register, you will be blocked from the next 2 placement drives. Register before the deadline.
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="form-card">
        <h2 className="form-title">Add a Dream Job ({dreamJobs.length}/3)</h2>
        <form onSubmit={addDreamJob}>
          <div className="form-grid">
            <label className="label-col">
              Company
              <select className="input" value={companyId} onChange={(event) => { setCompanyId(event.target.value); setRoleId(''); }} required>
                <option value="">Select company</option>
                {companies.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}
              </select>
            </label>
            <label className="label-col">
              Job Role
              <select className="input" value={roleId} onChange={(event) => setRoleId(event.target.value)} disabled={!companyId} required>
                <option value="">Select role</option>
                {filteredRoles.map((role) => <option key={role.id} value={role.id}>{role.title}</option>)}
              </select>
            </label>
          </div>
          <button className="btn btn-primary" type="submit" disabled={saving || dreamJobs.length >= 3 || !roleId}>
            {saving ? 'Analysing...' : dreamJobs.length >= 3 ? 'Three Dream Jobs Saved' : 'Add Dream Job'}
          </button>
        </form>
      </div>

      {loading ? <p className="loading-text"><span className="spinner" /> Loading Dream Jobs...</p> : (
        <div className="job-list">
          {dreamJobs.map((job) => (
            <article className="job-card" key={job.id}>
              <div className="job-card-header">
                <div><h3 className="job-title">{job.title}</h3><p className="job-company">{job.company_name}</p></div>
                <button className="btn btn-danger btn-sm" type="button" onClick={() => void removeDreamJob(job.id)}>Remove</button>
              </div>
              <p className="text-muted">AI skill analysis</p>
              {job.skill_gaps.length ? (
                <div className="skills-row"><span className="skills-label">Skill gaps:</span><div className="tags-container">{job.skill_gaps.map((gap) => <span className="tag" key={gap.skill}>{gap.skill}</span>)}</div></div>
              ) : <p className="text-success">Your current skills cover this role's listed requirements.</p>}
              {job.recommended_skills.length > 0 && <p className="helper-text">Recommended next skills: {job.recommended_skills.join(', ')}</p>}
            </article>
          ))}
          {!dreamJobs.length && <p className="empty-text">No Dream Jobs saved yet.</p>}
        </div>
      )}

      {!!dreamJobs.length && <section className="form-card">
        <div className="job-card-header">
          <div>
            <h2 className="form-title">Hiring updates and preparation</h2>
            <p className="text-muted">Current apply links and previous-year question resources for your saved roles.</p>
          </div>
          <label className="label-col">Filter by role
            <select className="input" value={updateRoleId} onChange={(event) => void loadUpdates(event.target.value)}>
              <option value="all">All saved roles</option>
              {dreamJobs.map((job) => <option key={job.job_role_id} value={job.job_role_id}>{job.title} at {job.company_name}</option>)}
            </select>
          </label>
        </div>
        {updates.map((update) => <article className="job-card" key={update.dream_job_id}>
          <div className="job-card-header"><div><h3 className="job-title">{update.role_title}</h3><p className="job-company">{update.company_name}</p></div><span className="text-muted">Checked {new Date(update.last_checked_at).toLocaleString()}</span></div>
          <h4>Current openings</h4>
          {update.live_jobs.map((opening) => <p key={opening.apply_url}><a href={opening.apply_url} target="_blank" rel="noreferrer">{opening.title}</a> <span className="text-muted">({opening.source}{opening.location ? `, ${opening.location}` : ''})</span></p>)}
          <h4>Previous-year questions and preparation</h4>
          {update.preparation_resources.map((resource) => <p key={resource.url}><a href={resource.url} target="_blank" rel="noreferrer">{resource.title}</a> <span className="text-muted">via {resource.provider}</span></p>)}
        </article>)}
      </section>}
    </div>
  );
}
