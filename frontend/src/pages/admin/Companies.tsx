import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

interface Company {
  id: number;
  name: string;
  industry: string | null;
  location: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  created_at: string | null;
}

interface CompanyForm {
  name: string;
  industry: string;
  location: string;
  contact_email: string;
  contact_phone: string;
}

const emptyForm: CompanyForm = {
  name: '',
  industry: '',
  location: '',
  contact_email: '',
  contact_phone: '',
};

export default function Companies() {
  const { logout } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState<CompanyForm>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchCompanies = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/companies');
      setCompanies(res.data);
      setError('');
    } catch {
      setError('Failed to load companies.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!form.name.trim()) {
      setFormError('Company name is required.');
      return;
    }

    setSaving(true);
    try {
      if (editingId) {
        await api.put(`/admin/companies/${editingId}`, form);
      } else {
        await api.post('/admin/companies', form);
      }
      setForm(emptyForm);
      setEditingId(null);
      await fetchCompanies();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })
          ?.response?.data?.error?.message || 'Failed to save company.';
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (c: Company) => {
    setEditingId(c.id);
    setForm({
      name: c.name,
      industry: c.industry || '',
      location: c.location || '',
      contact_email: c.contact_email || '',
      contact_phone: c.contact_phone || '',
    });
    setFormError('');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm(emptyForm);
    setFormError('');
  };

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Company Management</h1>
        <div className="page-header-actions">
          <Link to="/admin/dashboard" className="back-link">
            ← Dashboard
          </Link>
          <button onClick={logout} className="dash-logout-btn">
            Logout
          </button>
        </div>
      </div>

      {/* Add / Edit Form */}
      <div className="form-card">
        <h2 className="form-title">
          {editingId ? 'Edit Company' : 'Add Company'}
        </h2>
        {formError && <p className="error-text">{formError}</p>}
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="label-col">
              Name *
              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                className="input"
                required
              />
            </label>
            <label className="label-col">
              Industry
              <input
                name="industry"
                value={form.industry}
                onChange={handleChange}
                className="input"
              />
            </label>
            <label className="label-col">
              Location
              <input
                name="location"
                value={form.location}
                onChange={handleChange}
                className="input"
              />
            </label>
            <label className="label-col">
              Contact Email
              <input
                name="contact_email"
                value={form.contact_email}
                onChange={handleChange}
                className="input"
                type="email"
              />
            </label>
            <label className="label-col">
              Contact Phone
              <input
                name="contact_phone"
                value={form.contact_phone}
                onChange={handleChange}
                className="input"
              />
            </label>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : editingId ? 'Update' : 'Add Company'}
            </button>
            {editingId && (
              <button
                type="button"
                onClick={cancelEdit}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Company List */}
      {loading ? (
        <p className="loading-text"><span className="spinner" /> Loading companies...</p>
      ) : error ? (
        <p className="error-text">{error}</p>
      ) : companies.length === 0 ? (
        <p className="empty-text">No companies found. Add one above.</p>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Industry</th>
                <th>Location</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td>{c.industry || '—'}</td>
                  <td>{c.location || '—'}</td>
                  <td>{c.contact_email || '—'}</td>
                  <td>{c.contact_phone || '—'}</td>
                  <td>
                    <button
                      onClick={() => startEdit(c)}
                      className="btn btn-warning btn-sm"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
