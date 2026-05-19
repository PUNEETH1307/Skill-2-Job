import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { useToast } from '../../components/Toast';
import { AxiosError } from 'axios';

interface PlacementRecord {
    id: number;
    profile_id: number;
    job_role_id: number;
    company_id: number;
    placement_date: string | null;
    department: string | null;
    package_lpa: number | null;
    notes: string | null;
    student_name: string | null;
    job_title: string | null;
    company_name: string | null;
}

interface Company { id: number; name: string; }
interface JobRole { id: number; title: string; company_id: number; }
interface UserRecord { id: number; name: string; role: string; }

export default function Placements() {
    const { showToast } = useToast();
    const [placements, setPlacements] = useState<PlacementRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [companies, setCompanies] = useState<Company[]>([]);
    const [jobRoles, setJobRoles] = useState<JobRole[]>([]);
    const [students, setStudents] = useState<UserRecord[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [formError, setFormError] = useState('');
    const [saving, setSaving] = useState(false);

    const [form, setForm] = useState({
        profile_id: '',
        job_role_id: '',
        company_id: '',
        placement_date: '',
        package_lpa: '',
        notes: '',
    });

    const [editId, setEditId] = useState<number | null>(null);
    const [editData, setEditData] = useState({ package_lpa: '', placement_date: '', notes: '' });

    const fetchAll = useCallback(async () => {
        setLoading(true);
        try {
            const [plRes, compRes, jobRes, userRes] = await Promise.allSettled([
                api.get('/placements'),
                api.get('/admin/companies'),
                api.get('/admin/jobs'),
                api.get('/admin/users', { params: { per_page: 200 } }),
            ]);
            if (plRes.status === 'fulfilled') setPlacements(plRes.value.data);
            if (compRes.status === 'fulfilled') setCompanies(compRes.value.data);
            if (jobRes.status === 'fulfilled') setJobRoles(jobRes.value.data);
            if (userRes.status === 'fulfilled') setStudents(userRes.value.data.users.filter((u: UserRecord) => u.role === 'student'));
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
        if (!form.profile_id || !form.job_role_id || !form.company_id) {
            setFormError('Student, job role, and company are required.');
            return;
        }
        setSaving(true);
        try {
            await api.post('/placements', {
                profile_id: parseInt(form.profile_id),
                job_role_id: parseInt(form.job_role_id),
                company_id: parseInt(form.company_id),
                placement_date: form.placement_date || null,
                package_lpa: form.package_lpa ? parseFloat(form.package_lpa) : null,
                notes: form.notes || null,
            });
            showToast('Placement recorded successfully!', 'success');
            setShowForm(false);
            setForm({ profile_id: '', job_role_id: '', company_id: '', placement_date: '', package_lpa: '', notes: '' });
            fetchAll();
        } catch (err) {
            const msg = (err instanceof AxiosError && err.response?.data?.error?.message) || 'Failed to record placement.';
            setFormError(msg);
        } finally {
            setSaving(false);
        }
    };

    const handleUpdate = async (id: number) => {
        try {
            await api.put(`/placements/${id}`, {
                package_lpa: editData.package_lpa ? parseFloat(editData.package_lpa) : undefined,
                placement_date: editData.placement_date || undefined,
                notes: editData.notes || undefined,
            });
            showToast('Placement updated!', 'success');
            setEditId(null);
            fetchAll();
        } catch {
            showToast('Failed to update placement', 'error');
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Delete this placement record?')) return;
        try {
            await api.delete(`/placements/${id}`);
            showToast('Placement record deleted', 'info');
            fetchAll();
        } catch {
            showToast('Failed to delete placement', 'error');
        }
    };

    const filteredJobs = form.company_id
        ? jobRoles.filter(j => j.company_id === parseInt(form.company_id))
        : jobRoles;

    return (
        <div className="page-container-wide">
            <div className="page-header">
                <h1 className="page-title">Placement Records</h1>
                <div className="page-header-actions">
                    <Link to="/admin/dashboard" className="back-link">← Dashboard</Link>
                    <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
                        {showForm ? 'Cancel' : '+ Record Placement'}
                    </button>
                </div>
            </div>

            {/* Stats bar */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
                <div className="dash-widget" style={{ flex: 1, minWidth: '150px', textAlign: 'center' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: '#10b981' }}>{placements.length}</div>
                    <div style={{ color: '#64748b', fontSize: '14px' }}>Total Placed</div>
                </div>
                <div className="dash-widget" style={{ flex: 1, minWidth: '150px', textAlign: 'center' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: '#4f46e5' }}>
                        {placements.filter(p => p.package_lpa).length > 0
                            ? (placements.filter(p => p.package_lpa).reduce((s, p) => s + (p.package_lpa || 0), 0) / placements.filter(p => p.package_lpa).length).toFixed(1)
                            : '—'}
                    </div>
                    <div style={{ color: '#64748b', fontSize: '14px' }}>Avg Package (LPA)</div>
                </div>
                <div className="dash-widget" style={{ flex: 1, minWidth: '150px', textAlign: 'center' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: '#f59e0b' }}>
                        {new Set(placements.map(p => p.company_id)).size}
                    </div>
                    <div style={{ color: '#64748b', fontSize: '14px' }}>Companies</div>
                </div>
            </div>

            {/* Create Form */}
            {showForm && (
                <div className="dash-widget" style={{ marginBottom: '1.5rem' }}>
                    <h3 className="dash-widget-title">Record New Placement</h3>
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
                                <label className="label">Company *</label>
                                <select className="input" value={form.company_id} onChange={e => setForm({ ...form, company_id: e.target.value, job_role_id: '' })} required>
                                    <option value="">Select company...</option>
                                    {companies.map(c => (
                                        <option key={c.id} value={c.id}>{c.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="field-row">
                            <div className="field">
                                <label className="label">Job Role *</label>
                                <select className="input" value={form.job_role_id} onChange={e => setForm({ ...form, job_role_id: e.target.value })} required>
                                    <option value="">Select job role...</option>
                                    {filteredJobs.map(j => (
                                        <option key={j.id} value={j.id}>{j.title}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="field">
                                <label className="label">Placement Date</label>
                                <input type="date" className="input" value={form.placement_date} onChange={e => setForm({ ...form, placement_date: e.target.value })} />
                            </div>
                        </div>
                        <div className="field-row">
                            <div className="field">
                                <label className="label">Package (LPA)</label>
                                <input type="number" step="0.1" min="0" className="input" placeholder="e.g. 6.5" value={form.package_lpa} onChange={e => setForm({ ...form, package_lpa: e.target.value })} />
                            </div>
                            <div className="field">
                                <label className="label">Notes</label>
                                <input type="text" className="input" placeholder="Optional notes..." value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} />
                            </div>
                        </div>
                        <div className="btn-row">
                            <button type="submit" className="btn btn-success" disabled={saving}>{saving ? 'Saving...' : 'Record Placement'}</button>
                            <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary">Cancel</button>
                        </div>
                    </form>
                </div>
            )}

            {/* Table */}
            {loading ? (
                <p className="loading-text"><span className="spinner" /> Loading placements...</p>
            ) : placements.length === 0 ? (
                <p className="empty-text">No placement records yet. Record a placement to get started.</p>
            ) : (
                <div className="table-wrapper">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Student</th>
                                <th>Job Title</th>
                                <th>Company</th>
                                <th>Date</th>
                                <th>Package (LPA)</th>
                                <th>Department</th>
                                <th>Notes</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {placements.map(p => (
                                <>
                                    <tr key={p.id}>
                                        <td>{p.student_name || `Profile #${p.profile_id}`}</td>
                                        <td>{p.job_title || '—'}</td>
                                        <td>{p.company_name || '—'}</td>
                                        <td>{p.placement_date || '—'}</td>
                                        <td>{p.package_lpa != null ? `₹${p.package_lpa} LPA` : '—'}</td>
                                        <td>{p.department || '—'}</td>
                                        <td style={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.notes || '—'}</td>
                                        <td>
                                            <div className="btn-row">
                                                <button onClick={() => { setEditId(p.id); setEditData({ package_lpa: p.package_lpa?.toString() || '', placement_date: p.placement_date || '', notes: p.notes || '' }); }} className="btn btn-sm btn-primary">Edit</button>
                                                <button onClick={() => handleDelete(p.id)} className="btn btn-sm btn-danger">Delete</button>
                                            </div>
                                        </td>
                                    </tr>
                                    {editId === p.id && (
                                        <tr key={`edit-${p.id}`}>
                                            <td colSpan={8} style={{ background: '#f8fafc', padding: '1rem' }}>
                                                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                                                    <div className="field" style={{ minWidth: '150px' }}>
                                                        <label className="label">Package (LPA)</label>
                                                        <input type="number" step="0.1" min="0" className="input" value={editData.package_lpa} onChange={e => setEditData({ ...editData, package_lpa: e.target.value })} />
                                                    </div>
                                                    <div className="field" style={{ minWidth: '160px' }}>
                                                        <label className="label">Placement Date</label>
                                                        <input type="date" className="input" value={editData.placement_date} onChange={e => setEditData({ ...editData, placement_date: e.target.value })} />
                                                    </div>
                                                    <div className="field" style={{ flex: 1, minWidth: '200px' }}>
                                                        <label className="label">Notes</label>
                                                        <input type="text" className="input" value={editData.notes} onChange={e => setEditData({ ...editData, notes: e.target.value })} />
                                                    </div>
                                                    <div className="btn-row">
                                                        <button onClick={() => handleUpdate(p.id)} className="btn btn-success">Save</button>
                                                        <button onClick={() => setEditId(null)} className="btn btn-secondary">Cancel</button>
                                                    </div>
                                                </div>
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
