import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

interface Candidate {
  profile_id: number;
  name: string;
  cgpa: number;
  compatibility_score: number;
  matched_skills: string[];
  missing_skills: string[];
}

interface NamedShortlist {
  name: string;
  job_role_id: number;
  job_title: string | null;
  students: Array<{ profile_id: number; name: string; cgpa: number | null; score: number | null; status: string }>;
}

interface StudentProfileView {
  student: { name: string; email: string; phone?: string | null } | null;
  institution?: string | null;
  degree?: string | null;
  branch?: string | null;
  cgpa?: number | null;
  graduation_year?: number | null;
  backlogs_count?: number;
  dream_job?: string | null;
  expected_lpa?: number | null;
  skills_json?: string | string[] | null;
  projects: Array<{ title: string; description?: string; technologies?: string; project_url?: string }>;
  certifications: Array<{ name: string; issuer?: string; issue_date?: string; certificate_url?: string | null; certificate_original_filename?: string | null }>;
  resume_uploads: Array<{ id: number; original_filename: string; resume_variant: string; source: string; download_url: string }>;
}

interface JobRole {
  id: number;
  title: string;
  company_name: string | null;
  cgpa_threshold?: number | null;
  minimum_graduation_year?: number | null;
}

export default function Shortlist() {
  const { logout } = useAuth();
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [jobRoles, setJobRoles] = useState<JobRole[]>([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [shortlistName, setShortlistName] = useState('');
  const [savedShortlists, setSavedShortlists] = useState<NamedShortlist[]>([]);
  const [selectedSavedShortlist, setSelectedSavedShortlist] = useState<NamedShortlist | null>(null);
  const [savedLoading, setSavedLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState<StudentProfileView | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [candidateFilter, setCandidateFilter] = useState('');
  const [candidatePage, setCandidatePage] = useState(1);
  const [customRoleOpen, setCustomRoleOpen] = useState(false);
  const [customRole, setCustomRole] = useState({
    company_name: '', title: '', required_skills: '', cgpa_threshold: '',
    minimum_graduation_year: '', description: '',
  });
  const candidatesPerPage = 20;

  const filteredCandidates = useMemo(() => {
    const query = candidateFilter.trim().toLowerCase();
    if (!query) return candidates;
    return candidates.filter((candidate) =>
      [
        candidate.name,
        candidate.cgpa?.toFixed(2) ?? '',
        candidate.compatibility_score.toFixed(1),
        ...candidate.matched_skills,
        ...candidate.missing_skills,
      ]
        .some((value) => value.toLowerCase().includes(query))
    );
  }, [candidates, candidateFilter]);
  const candidatePageCount = Math.max(1, Math.ceil(filteredCandidates.length / candidatesPerPage));
  const visibleCandidates = filteredCandidates.slice(
    (candidatePage - 1) * candidatesPerPage,
    candidatePage * candidatesPerPage
  );

  useEffect(() => {
    setCandidatePage(1);
  }, [candidateFilter, candidates.length]);

  useEffect(() => {
    if (!profile) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setProfile(null);
    };
    document.addEventListener('keydown', closeOnEscape);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', closeOnEscape);
      document.body.style.overflow = '';
    };
  }, [profile]);

  useEffect(() => {
    const loadJobRoles = async () => {
      try {
        const res = await api.get('/admin/jobs');
        setJobRoles(res.data);
      } catch {
        setError('Failed to load job roles. Please refresh and try again.');
      } finally {
        setJobsLoading(false);
      }
    };
    loadJobRoles();
  }, []);

  useEffect(() => {
    fetchSavedShortlists();
  }, [selectedJobId]);

  const fetchShortlist = async () => {
    if (!selectedJobId) {
      setError('Please select a job role.');
      return;
    }
    setError('');
    setMessage('');
    setLoading(true);
    setCandidates([]);
    setSelected(new Set());
    setCandidateFilter('');
    setCandidatePage(1);

    try {
      const res = await api.get(`/admin/jobs/${selectedJobId}/shortlist`);
      const data = res.data;
      if (data.message && (!data.candidates || data.candidates.length === 0)) {
        setMessage(data.message);
      } else {
        setCandidates(data.candidates || []);
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })
          ?.response?.data?.error?.message || 'Failed to load shortlist.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const fetchSavedShortlists = async () => {
    setSavedLoading(true);
    try {
      const res = await api.get('/admin/shortlists', {
        params: selectedJobId ? { job_role_id: Number(selectedJobId) } : undefined,
      });
      setSavedShortlists(Array.isArray(res.data) ? res.data : []);
    } catch {
      setSavedShortlists([]);
    } finally {
      setSavedLoading(false);
    }
  };

  const createCustomRole = async () => {
    setError('');
    try {
      const response = await api.post('/admin/custom-job', {
        ...customRole,
        cgpa_threshold: customRole.cgpa_threshold ? Number(customRole.cgpa_threshold) : 0,
        minimum_graduation_year: customRole.minimum_graduation_year
          ? Number(customRole.minimum_graduation_year) : null,
        required_skills: customRole.required_skills.split(',').map((skill) => skill.trim()).filter(Boolean),
      });
      const created = response.data as JobRole;
      setJobRoles((previous) => [created, ...previous]);
      setSelectedJobId(String(created.id));
      setCustomRoleOpen(false);
      setCustomRole({ company_name: '', title: '', required_skills: '', cgpa_threshold: '', minimum_graduation_year: '', description: '' });
      setMessage('Custom company and job role saved. You can now run the shortlist.');
    } catch (err: unknown) {
      setError((err as { response?: { data?: { error?: { message?: string } } } })
        ?.response?.data?.error?.message || 'Failed to save custom job role.');
    }
  };

  const toggleCandidate = (profileId: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(profileId)) {
        next.delete(profileId);
      } else {
        next.add(profileId);
      }
      return next;
    });
  };

  const toggleAll = () => {
    const visibleIds = visibleCandidates.map((candidate) => candidate.profile_id);
    if (visibleIds.length > 0 && visibleIds.every((id) => selected.has(id))) {
      setSelected((previous) => {
        const next = new Set(previous);
        visibleIds.forEach((id) => next.delete(id));
        return next;
      });
    } else {
      setSelected((previous) => {
        const next = new Set(previous);
        visibleIds.forEach((id) => next.add(id));
        return next;
      });
    }
  };

  const markShortlisted = async () => {
    if (selected.size === 0) {
      setError('Select at least one candidate.');
      return;
    }
    setSaving(true);
    setError('');
    setMessage('');
    try {
      const response = await api.post(`/admin/jobs/${selectedJobId}/shortlist`, {
        profile_ids: Array.from(selected),
        shortlist_name: shortlistName.trim(),
      });
      const savedName = response.data?.[0]?.shortlist_name || shortlistName.trim() || `Shortlist - ${selectedJobId}`;
      setMessage(`${selected.size} candidate(s) saved in "${savedName}".`);
      setSelected(new Set());
      setShortlistName('');
      fetchSavedShortlists();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })
          ?.response?.data?.error?.message || 'Failed to shortlist candidates.';
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const viewProfile = async (profileId: number) => {
    setProfileLoading(true);
    setError('');
    try {
      const res = await api.get(`/admin/students/${profileId}/profile`);
      setProfile(res.data);
    } catch {
      setError('Failed to load student profile.');
    } finally {
      setProfileLoading(false);
    }
  };

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Candidate Shortlisting</h1>
        <div className="page-header-actions">
          <Link to="/admin/dashboard" className="back-link">
            ← Dashboard
          </Link>
          <button onClick={logout} className="dash-logout-btn">
            Logout
          </button>
        </div>
      </div>

      {/* Job Selection */}
      <div className="form-card">
        <h2 className="form-title">Select Job Role</h2>
        <div className="flex gap-2 items-center" style={{ flexWrap: 'wrap' }}>
          <label className="label-col" style={{ minWidth: '280px' }}>
            Job Role
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="input"
              disabled={jobsLoading}
            >
              <option value="">
                {jobsLoading ? 'Loading job roles...' : 'Select a job role...'}
              </option>
              {jobRoles.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title}{job.company_name ? ` — ${job.company_name}` : ''}
                  {job.minimum_graduation_year ? ` (Batch ${job.minimum_graduation_year}+)` : ''}
                </option>
              ))}
            </select>
          </label>
          <button
            onClick={fetchShortlist}
            className="btn btn-primary"
            disabled={loading}
            style={{ alignSelf: 'flex-end' }}
          >
            {loading ? 'Loading...' : 'View Candidates'}
          </button>
        </div>
        <button type="button" className="btn btn-secondary" style={{ marginTop: '1rem' }}
          onClick={() => setCustomRoleOpen((open) => !open)}>
          {customRoleOpen ? 'Cancel custom role' : '+ Add startup / custom role'}
        </button>
        {customRoleOpen && (
          <div className="custom-role-form">
            <h3>Custom placement role</h3>
            <p className="muted-text">Save a startup role and use the same eligibility, skill matching, missing-skill, and course-gap workflow.</p>
            <div className="custom-role-grid">
              <label className="label">Company name<input className="input" value={customRole.company_name} onChange={(e) => setCustomRole({ ...customRole, company_name: e.target.value })} /></label>
              <label className="label">Job title<input className="input" value={customRole.title} onChange={(e) => setCustomRole({ ...customRole, title: e.target.value })} /></label>
              <label className="label">Required skills<input className="input" placeholder="Python, React, SQL" value={customRole.required_skills} onChange={(e) => setCustomRole({ ...customRole, required_skills: e.target.value })} /></label>
              <label className="label">Minimum CGPA<input type="number" min="0" max="10" step="0.01" className="input" value={customRole.cgpa_threshold} onChange={(e) => setCustomRole({ ...customRole, cgpa_threshold: e.target.value })} /></label>
              <label className="label">Minimum passing year<input type="number" className="input" value={customRole.minimum_graduation_year} onChange={(e) => setCustomRole({ ...customRole, minimum_graduation_year: e.target.value })} /></label>
              <label className="label">Description<textarea className="input" value={customRole.description} onChange={(e) => setCustomRole({ ...customRole, description: e.target.value })} /></label>
            </div>
            <button type="button" className="btn btn-primary" onClick={createCustomRole}>Save custom role</button>
          </div>
        )}
      </div>

      {error && <p className="error-text">{error}</p>}
      {message && <p className="success-text">{message}</p>}

      {/* Candidate List */}
      {candidates.length > 0 && (
        <>
          <div className="form-card" style={{ marginTop: '1.5rem' }}>
            <label className="label-col" style={{ maxWidth: '520px' }}>
              Shortlist name
              <input
                className="input"
                value={shortlistName}
                onChange={(event) => setShortlistName(event.target.value)}
                placeholder="Example: Java Backend - Batch 2026"
                maxLength={150}
              />
            </label>
            <p className="muted-text">Enter a name before selecting students. You can reopen this saved list below.</p>
          </div>
          <div className="shortlist-bar">
            <p className="shortlist-count">
              {filteredCandidates.length} of {candidates.length} eligible candidate(s)
            </p>
            <button
              onClick={markShortlisted}
              className="btn btn-success"
              disabled={saving || selected.size === 0}
            >
              {saving
                ? 'Saving...'
                : `Mark Shortlisted (${selected.size})`}
            </button>
          </div>
          <div className="shortlist-filters">
            <label className="label" htmlFor="candidate-filter">Filter candidates</label>
            <input
              id="candidate-filter"
              className="input"
              value={candidateFilter}
              onChange={(event) => setCandidateFilter(event.target.value)}
              placeholder="Search by name or skill..."
            />
          </div>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>
                    <input
                      type="checkbox"
                      checked={visibleCandidates.length > 0 && visibleCandidates.every((candidate) => selected.has(candidate.profile_id))}
                      onChange={toggleAll}
                    />
                  </th>
                  <th>Name</th>
                  <th>CGPA</th>
                  <th>Score</th>
                  <th>Matched Skills</th>
                  <th>Missing Skills</th>
                  <th>Profile</th>
                </tr>
              </thead>
              <tbody>
                {visibleCandidates.map((c) => (
                  <tr key={c.profile_id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.has(c.profile_id)}
                        onChange={() => toggleCandidate(c.profile_id)}
                      />
                    </td>
                    <td>{c.name}</td>
                    <td>{c.cgpa?.toFixed(2) ?? '—'}</td>
                    <td>
                      {c.compatibility_score.toFixed(1)}%
                    </td>
                    <td>
                      {c.matched_skills?.join(', ') || '—'}
                    </td>
                    <td>
                      {c.missing_skills?.join(', ') || 'None'}
                    </td>
                    <td>
                      <button type="button" className="btn btn-sm btn-secondary"
                        onClick={() => viewProfile(c.profile_id)}>
                        View Profile
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {candidatePageCount > 1 && (
            <div className="shortlist-pagination">
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                disabled={candidatePage === 1}
                onClick={() => setCandidatePage((page) => page - 1)}
              >
                ← Previous
              </button>
              <span>Page {candidatePage} of {candidatePageCount}</span>
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                disabled={candidatePage === candidatePageCount}
                onClick={() => setCandidatePage((page) => page + 1)}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      <div className="form-card" style={{ marginTop: '1.5rem' }}>
        <div className="flex gap-2 items-center" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
          <h2 className="form-title" style={{ marginBottom: 0 }}>Saved Shortlists</h2>
          <button type="button" className="btn btn-secondary" onClick={fetchSavedShortlists} disabled={savedLoading}>
            {savedLoading ? 'Loading...' : 'Refresh Lists'}
          </button>
        </div>
        {savedShortlists.length === 0 ? (
          <p className="muted-text">No named shortlists saved for this job role.</p>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead><tr><th>Shortlist Name</th><th>Job Role</th><th>Students</th><th>Student Names</th></tr></thead>
              <tbody>
                {savedShortlists.map((list) => (
                  <tr key={`${list.job_role_id}-${list.name}`}>
                    <td>
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        onClick={() => setSelectedSavedShortlist(list)}
                      >
                        {list.name}
                      </button>
                    </td>
                    <td>{list.job_title || '—'}</td>
                    <td>{list.students.length}</td>
                    <td>{list.students.map((student) => student.name).join(', ') || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {selectedSavedShortlist && (
          <div className="dash-widget" style={{ marginTop: '1rem' }}>
            <h3 className="dash-widget-title">{selectedSavedShortlist.name}</h3>
            <p className="muted-text">Students in this shortlist</p>
            <div className="table-wrapper">
              <table className="table">
                <thead><tr><th>Student Name</th><th>CGPA</th><th>Score</th><th>Status</th></tr></thead>
                <tbody>
                  {selectedSavedShortlist.students.map((student) => (
                    <tr key={student.profile_id}>
                      <td>{student.name}</td>
                      <td>{student.cgpa?.toFixed(2) ?? '—'}</td>
                      <td>{student.score == null ? '—' : `${student.score.toFixed(1)}%`}</td>
                      <td>{student.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {(profileLoading || profile) && (
        <div className="student-profile-modal" role="dialog" aria-modal="true" aria-labelledby="student-profile-title"
          onMouseDown={(event) => { if (event.target === event.currentTarget) setProfile(null); }}>
          <div className="student-profile-paper">
            <div className="student-profile-modal-header">
              <div>
                <span className="student-profile-kicker">PLACEMENT REVIEW</span>
                <h2 id="student-profile-title">Student Profile</h2>
              </div>
              <button type="button" className="student-profile-close" aria-label="Close profile" onClick={() => setProfile(null)}>×</button>
            </div>
          {profileLoading ? <p className="loading-text">Loading profile...</p> : profile && (
            <>
              <div className="student-profile-hero">
                <div className="student-profile-avatar">{(profile.student?.name || 'S').slice(0, 1).toUpperCase()}</div>
                <div>
                  <h3>{profile.student?.name || 'Student'}</h3>
                  <p>{profile.student?.email}{profile.student?.phone ? ` · ${profile.student.phone}` : ''}</p>
                  <p>{profile.degree || 'Degree'} · {profile.branch || 'Branch'}</p>
                </div>
              </div>
              <div className="student-profile-grid">
                <div><span>Institution</span><strong>{profile.institution || '—'}</strong></div>
                <div><span>CGPA</span><strong>{profile.cgpa ?? '—'}</strong></div>
                <div><span>Graduation</span><strong>{profile.graduation_year ?? '—'}</strong></div>
                <div><span>Backlogs</span><strong>{profile.backlogs_count ?? 0}</strong></div>
              </div>
              <section className="student-profile-section">
                <h3>Career Goals</h3>
                <p><strong>{profile.dream_job || '—'}</strong> · Expected LPA: {profile.expected_lpa ?? '—'}</p>
              </section>
              <section className="student-profile-section">
                <h3>Projects</h3>
                {profile.projects.length ? profile.projects.map((project, index) => (
                  <div key={`${project.title}-${index}`} className="student-profile-entry">
                    <strong>{project.title}</strong>
                    <p>{project.description || 'No description provided.'}</p>
                    <small>{project.technologies || 'Technologies not provided'}</small>
                    {project.project_url && <a href={project.project_url} target="_blank" rel="noreferrer">Open project link ↗</a>}
                  </div>
                )) : <p className="muted-text">No projects added.</p>}
              </section>
              <section className="student-profile-section">
                <h3>Certifications</h3>
                {profile.certifications.length ? profile.certifications.map((certification, index) => (
                  <div key={`${certification.name}-${index}`} className="student-profile-entry">
                    <strong>{certification.name}</strong><small>{certification.issuer || 'Issuer not provided'}</small>
                    {certification.certificate_url && (
                      <a href={`${api.defaults.baseURL}${certification.certificate_url}`} target="_blank" rel="noreferrer">
                        Preview certificate ↗
                      </a>
                    )}
                  </div>
                )) : <p className="muted-text">No certifications uploaded.</p>}
              </section>
              <section className="student-profile-section">
                <h3>Resumes</h3>
                {profile.resume_uploads.length ? profile.resume_uploads.map((resume) => (
                  <a className="student-profile-file" key={resume.id} href={`${api.defaults.baseURL}${resume.download_url}`} target="_blank" rel="noreferrer">
                    {resume.resume_variant === 'photo' ? 'With photo' : 'Without photo'} · {resume.original_filename}
                  </a>
                )) : <p className="muted-text">No resumes uploaded.</p>}
              </section>
            </>
          )}
          </div>
        </div>
      )}
    </div>
  );
}
