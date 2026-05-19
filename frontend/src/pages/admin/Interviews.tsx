import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { useToast } from '../../components/Toast';
import { AxiosError } from 'axios';

interface InterviewRecord {
  id: number;
  profile_id: number;
  job_role_id: number | null;
  company_id: number | null;
  interview_date: string;
  interview_time: string | null;
  mode: string;
  venue_or_link: string | null;
  status: 'scheduled' | 'completed' | 'cancelled' | 'no-show';
  feedback: string | null;
  result: 'selected' | 'rejected' | 'on-hold' | null;
  student_name: string | null;
  job_title: string | null;
  company_name: string | null;
}

interface Company { id: number; name: string; }
interface JobRole { id: number; title: string; company_id: number; }
interface StudentProfile { id: number; user_id: number; }
interface UserRecord { id: number; name: string; profile?: { id: number }; }

const STATUS_COLORS: Record<string, string> = {
  scheduled: '#3b82f6',
  completed: '#10b981',
  cancelled: '#ef4444',
  'no-show': '#f59e0b',
};

const RESULT_COLORS: Record<string, string> = {
  selected: '#10b981',
  rejected: '#ef4444',
  'on-hold': '#f59e0b',
};

export default function Interviews() {
  const { showToast } = useToast();
  const [interviews, setInterviews] = useState<InterviewRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [jobRoles, setJobRoles] = useState<JobRole[]>([]);
  const [students, setStudents] = useState<UserRecord[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const [editId, setEditId] = useState<number | null>(null);
  const [editData, setEditData] = useState<{ status: string; result: string; feedback: string }>({ status: '', result: '', feedback: '' });

  const [form, setForm] = useState({
    profile_id: '',
    job_role_id: '',
    company_id: '',
    interview_date: '',
    interview_time: '',
    mode: 'in-person',
    venue_or_link: '',
  });
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [intRes, compRes, jobRes, userRes] = await Promise.allSettled([
        api.get('/interviews'),
        api.get('/admin/companies'),
        api.get('/admin/jobs'),
        api.get('/admin/users', { params: { per_page: 200 } }),
      ]);
      if (intRes.status === 'fulfilled') setInterviews(intRes.value.data);
      if (compRes.status === 'fulfilled') setCompanies(compRes.value.data);
      if (jobRes.status === 'fulfilled') setJobRoles(jobRes.value.data);
      if (userRes.status === 'fulfilled') setStudents(userRes.value.data.users.filter((u: UserRecord & { role: string }) => u.role === 'student'));
    } catch {
      showToast('Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    if (!form.profile_id || !form.interview_date) {
      setFormError('Student and interview date are required.');
      return;
    }
    setSaving(true);
    try {
      await api.post('/interviews', {
        profile_id: parseInt(form.profile_id),
        job_role_id: form.job_role_id ? parseInt(form.job_role_id) : null,
        company_id: form.company_id ? parseInt(form.company_id) : null,
        interview_date: form.interview_date,
        interview_time: form.interview_time || null,
        mode: form.mode,
        venue_or_link: form.venue_or_link || null,
      });
      showToast('Interview scheduled successfully!', 'success');
      setShowForm(false);
      setForm({ profile_id: '', job_role_id: '', company_id: '', interview_date: '', interview_time: '', mode: 'in-person', venue_or_link: '' });
      fetchAll();
    } catch (err) {
      const msg = (err instanceof AxiosError && err.response?.data?.error?.message) || 'Failed to schedule interview.';
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (id: number) => {
    try {
      await api.put(`/interviews/${id}`, {
        status: editData.status || undefined,
        result: editData.result || undefined,
        feedback: editData.feedback || undefined,
      });
      showToast('Interview updated!', 'success');
      setEditId(null);
      fetchAll();
    } catch {
      showToast('Failed to update interview', 'error');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this interview record?')) return;
    try {
      await api.delete(`/interviews/${id}`);
      showToast('Interview deleted', 'info');
      fetchAll();
    } catch {
      showToast('Failed to delete interview', 'error');
    }
  };

  const filtered = filter === 'all' ? interviews : interviews.filter(i => i.status === filter);

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Interview Management</h1>
        <div className="page-header-actions">
          <Link to="/admin/dashboard" className="back-link">← Dashboard</Link>
          <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
            {showForm ? 'Cancel' : '+ Schedule Interview'}
          </button>
        </div>
      </div>

      {/* Schedule Form */}
      {showForm && (
        <div className="dash-widget" style={{ marginBottom: '1.5rem' }}>
          <h3 className="dash-widget-title">Schedule New Interview</h3>
          {formError && <div className="alert alert-error">{formError}</div>}
          <form onSubmit={handleCreate}>
            <div className="field-row">
              <div className="field">
                <label className="label">Student *</label>
                <select className="input" value={form.profile_id} onChange={e => setForm({ ...form, profile_id: e.target.value })} required>
                  <option value="">Select student...</option>
                  {students.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label className="label">Job Role</label>
                <select className="input" value={form.job_role_id} onChange={e => setForm({ ...form, job_role_id: e.target.value })}>
                  <option value="">Select job role...</option>
                  {jobRoles.map(j => (
                    <option key={j.id} value={j.id}>{j.title}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="field-row">
              <div className="field">
                <label className="label">Company</label>
                <select className="input" value={form.company_id} onChange={e => setForm({ ...form, company_id: e.target.value })}>
                  <option value="">Select company...</option>
                  {companies.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label className="label">Interview Date *</label>
                <input type="date" className="input" value={form.interview_date} onChange={e => setForm({ ...form, interview_date: e.target.value })} required />
              </div>
            </div>
            <div className="field-row">
              <div className="field">
                <label className="label">Time</label>
                <input type="text" className="input" placeholder="e.g. 10:00 AM" value={form.interview_time} onChange={e => setForm({ ...form, interview_time: e.target.value })} />
              </div>
              <div className="field">
                <label className="label">Mode</label>
                <select className="input" value={form.mode} onChange={e => setForm({ ...form, mode: e.target.value })}>
                  <option value="in-person">In-Person</option>
                  <option value="online">Online</option>
                  <option value="phone">Phone</option>
                </select>
              </div>
            </div>
            <div className="field">
              <label className="label">Venue / Meeting Link</label>
              <input type="text" className="input" placeholder="Room 101 or https://meet.google.com/..." value={form.venue_or_link} onChange={e => setForm({ ...form, venue_or_link: e.target.value })} />
            </div>
            <div className="btn-row">
              <button type="submit" className="btn btn-success" disabled={saving}>{saving ? 'Scheduling...' : 'Schedule'}</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="filter-row" style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {['all', 'scheduled', 'completed', 'cancelled', 'no-show'].map(f => (
          <button key={f} onClick={() => setFilter(f)} className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'}`}>
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Table */}
      {loading ? (
        <p className="loading-text"><span className="spinner" /> Loading interviews...</p>
      ) : filtered.length === 0 ? (
        <p className="empty-text">No interviews found.</p>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Job Title</th>
                <th>Company</th>
                <th>Date</th>
                <th>Time</th>
                <th>Mode</th>
                <th>Status</th>
                <th>Result</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(interview => (
                <>
                  <tr key={interview.id}>
                    <td>{interview.student_name || `Profile #${interview.profile_id}`}</td>
                    <td>{interview.job_title || '—'}</td>
                    <td>{interview.company_name || '—'}</td>
                    <td>{interview.interview_date}</td>
                    <td>{interview.interview_time || '—'}</td>
                    <td style={{ textTransform: 'capitalize' }}>{interview.mode}</td>
                    <td>
                      <span className="status-badge" style={{ backgroundColor: STATUS_COLORS[interview.status] || '#6b7280', color: 'white', padding: '2px 10px', borderRadius: '12px', fontSize: '12px' }}>
                        {interview.status}
                      </span>
                    </td>
                    <td>
                      {interview.result ? (
                        <span style={{ backgroundColor: RESULT_COLORS[interview.result] || '#6b7280', color: 'white', padding: '2px 10px', borderRadius: '12px', fontSize: '12px' }}>
                          {interview.result}
                        </span>
                      ) : '—'}
                    </td>
                    <td>
                      <div className="btn-row">
                        <button onClick={() => { setEditId(interview.id); setEditData({ status: interview.status, result: interview.result || '', feedback: interview.feedback || '' }); }} className="btn btn-sm btn-primary">Edit</button>
                        <button onClick={() => handleDelete(interview.id)} className="btn btn-sm btn-danger">Delete</button>
                      </div>
                    </td>
                  </tr>
                  {editId === interview.id && (
                    <tr key={`edit-${interview.id}`}>
                      <td colSpan={9} style={{ background: '#f8fafc', padding: '1rem' }}>
                        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                          <div className="field" style={{ minWidth: '150px' }}>
                            <label className="label">Status</label>
                            <select className="input" value={editData.status} onChange={e => setEditData({ ...editData, status: e.target.value })}>
                              <option value="scheduled">Scheduled</option>
                              <option value="completed">Completed</option>
                              <option value="cancelled">Cancelled</option>
                              <option value="no-show">No-Show</option>
                            </select>
                          </div>
                          <div className="field" style={{ minWidth: '150px' }}>
                            <label className="label">Result</label>
                            <select className="input" value={editData.result} onChange={e => setEditData({ ...editData, result: e.target.value })}>
                              <option value="">— None —</option>
                              <option value="selected">Selected</option>
                              <option value="rejected">Rejected</option>
                              <option value="on-hold">On Hold</option>
                            </select>
                          </div>
                          <div className="field" style={{ flex: 1, minWidth: '200px' }}>
                            <label className="label">Feedback</label>
                            <input type="text" className="input" value={editData.feedback} onChange={e => setEditData({ ...editData, feedback: e.target.value })} placeholder="Optional feedback..." />
                          </div>
                          <div className="btn-row">
                            <button onClick={() => handleUpdate(interview.id)} className="btn btn-success">Save</button>
                            <button onClick={() => setEditId(null)} className="btn btn-secondary">Cancel</button>
                          </div>
                        </div>
                        {editData.result === 'selected' && (
                          <p style={{ margin: '0.5rem 0 0', color: '#10b981', fontSize: '13px' }}>
                            ✓ Saving "selected" will automatically create a placement record for this student.
                          </p>
                        )}
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
