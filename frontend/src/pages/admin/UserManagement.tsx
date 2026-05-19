import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

interface UserRecord {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  role: string;
  status: string;
  created_at: string | null;
}

interface UserForm {
  name: string;
  email: string;
  phone: string;
  password: string;
  role: string;
}

const emptyForm: UserForm = {
  name: '',
  email: '',
  phone: '',
  password: '',
  role: 'student',
};

export default function UserManagement() {
  const { user: currentUser, logout } = useAuth();
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [form, setForm] = useState<UserForm>(emptyForm);
  const [showForm, setShowForm] = useState(false);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  // Admin-only check
  if (currentUser?.role !== 'admin') {
    return (
      <div className="page-container">
        <p className="error-text">
          Access denied. Only administrators can manage users.
        </p>
        <Link to="/admin/dashboard">← Back to Dashboard</Link>
      </div>
    );
  }

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const params: Record<string, string | number> = {
        page,
        per_page: 15,
      };
      if (search) params.search = search;
      const res = await api.get('/admin/users', { params });
      setUsers(res.data.users);
      setTotalPages(res.data.pages);
      setTotal(res.data.total);
    } catch {
      setError('Failed to load users.');
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput);
  };

  const handleFormChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!form.name.trim() || !form.email.trim() || !form.password) {
      setFormError('Name, email, and password are required.');
      return;
    }
    if (form.password.length < 8) {
      setFormError('Password must be at least 8 characters.');
      return;
    }

    setSaving(true);
    try {
      await api.post('/admin/users', form);
      setForm(emptyForm);
      setShowForm(false);
      await fetchUsers();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })
          ?.response?.data?.error?.message || 'Failed to create user.';
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  const toggleStatus = async (u: UserRecord) => {
    const newStatus = u.status === 'active' ? 'inactive' : 'active';
    try {
      await api.put(`/admin/users/${u.id}/status`, { status: newStatus });
      await fetchUsers();
    } catch {
      setError('Failed to update user status.');
    }
  };

  const changeRole = async (u: UserRecord, newRole: string) => {
    if (u.role === newRole) return;
    if (!confirm(`Change ${u.name}'s role from "${u.role}" to "${newRole}"?`)) return;
    try {
      await api.post('/auth/update-role', { user_id: u.id, role: newRole });
      await fetchUsers();
    } catch {
      setError('Failed to update user role.');
    }
  };

  return (
    <div className="page-container-wide">
      <div className="page-header-narrow">
        <h1 className="page-title">User Management</h1>
        <div className="page-header-actions">
          <Link to="/admin/dashboard" className="back-link">
            ← Dashboard
          </Link>
          <button onClick={logout} className="dash-logout-btn">
            Logout
          </button>
        </div>
      </div>

      <div className="admin-note">Admin only — requires admin role</div>

      {/* Search & Create */}
      <div className="toolbar">
        <form onSubmit={handleSearch} className="search-row">
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by name or email"
            className="input search-input"
          />
          <button type="submit" className="btn btn-primary">
            Search
          </button>
          {search && (
            <button
              type="button"
              onClick={() => {
                setSearchInput('');
                setSearch('');
                setPage(1);
              }}
              className="btn btn-secondary"
            >
              Clear
            </button>
          )}
        </form>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn btn-create"
        >
          {showForm ? 'Cancel' : '+ Create User'}
        </button>
      </div>

      {/* Create User Form */}
      {showForm && (
        <div className="form-card">
          <h2 className="form-title">Create New User</h2>
          {formError && <p className="error-text">{formError}</p>}
          <form onSubmit={handleCreateUser}>
            <div className="form-grid">
              <label className="label-col">
                Name *
                <input
                  name="name"
                  value={form.name}
                  onChange={handleFormChange}
                  className="input"
                  required
                />
              </label>
              <label className="label-col">
                Email *
                <input
                  name="email"
                  value={form.email}
                  onChange={handleFormChange}
                  className="input"
                  type="email"
                  required
                />
              </label>
              <label className="label-col">
                Phone
                <input
                  name="phone"
                  value={form.phone}
                  onChange={handleFormChange}
                  className="input"
                />
              </label>
              <label className="label-col">
                Password *
                <input
                  name="password"
                  value={form.password}
                  onChange={handleFormChange}
                  className="input"
                  type="password"
                  required
                  minLength={8}
                />
              </label>
              <label className="label-col">
                Role *
                <select
                  name="role"
                  value={form.role}
                  onChange={handleFormChange}
                  className="input"
                >
                  <option value="student">Student</option>
                  <option value="placement_officer">Placement Officer</option>
                  <option value="admin">Admin</option>
                </select>
              </label>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Creating...' : 'Create User'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* User List */}
      {loading ? (
        <p className="loading-text"><span className="spinner" /> Loading users...</p>
      ) : error ? (
        <p className="error-text">{error}</p>
      ) : (
        <>
          <p className="muted-text" style={{ fontStyle: 'normal', marginBottom: '0.5rem' }}>
            Showing {users.length} of {total} users — Page {page} of{' '}
            {totalPages}
          </p>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>{u.id}</td>
                    <td>{u.name}</td>
                    <td>{u.email}</td>
                    <td>
                      <select
                        value={u.role}
                        onChange={(e) => changeRole(u, e.target.value)}
                        style={{
                          padding: '3px 8px', borderRadius: '6px', border: '1px solid var(--border)',
                          fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer',
                          background: u.role === 'admin' ? '#fef3c7' : u.role === 'placement_officer' ? '#dbeafe' : '#d1fae5',
                          color: u.role === 'admin' ? '#92400e' : u.role === 'placement_officer' ? '#1e40af' : '#065f46',
                        }}
                      >
                        <option value="student">student</option>
                        <option value="placement_officer">placement_officer</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                    <td>
                      <span className={u.status === 'active' ? 'status-active' : 'status-inactive'}>
                        {u.status}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => toggleStatus(u)}
                        className={u.status === 'active' ? 'btn btn-danger btn-sm' : 'btn btn-success btn-sm'}
                      >
                        {u.status === 'active' ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="btn btn-primary btn-sm"
            >
              ← Previous
            </button>
            <span className="page-info">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="btn btn-primary btn-sm"
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
