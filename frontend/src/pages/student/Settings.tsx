import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../components/Toast';
import { AxiosError } from 'axios';

export default function Settings() {
  const { showToast } = useToast();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleChangePassword = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setSaving(true);
    try {
      await api.put('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      showToast('Password changed successfully!', 'success');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      if (err instanceof AxiosError && err.response) {
        setError(err.response.data?.error?.message ?? 'Failed to change password.');
      } else {
        setError('Unable to connect to the server.');
      }
      showToast('Failed to change password', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    showToast('Logged out successfully', 'info');
    navigate('/login');
  };

  const roleLabel: Record<string, string> = {
    student: '👨‍🎓 Student',
    placement_officer: '🎓 Placement Officer',
    admin: '🔑 Administrator',
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <Link to="/student/dashboard" className="back-link">← Back to Dashboard</Link>
      </div>

      {/* ── Account Section ─────────────────────────────── */}
      <div className="page-section">
        <h2 className="section-title">Account</h2>

        {/* User Info Card */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '1.25rem 1.5rem',
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          marginBottom: '1rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* Avatar */}
            <div style={{
              width: '52px', height: '52px', borderRadius: '50%',
              background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', fontWeight: 700, fontSize: '1.3rem', flexShrink: 0,
            }}>
              {user?.name?.charAt(0).toUpperCase() ?? '?'}
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)' }}>
                {user?.name}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {user?.email}
              </div>
              <div style={{
                display: 'inline-block', marginTop: '4px',
                fontSize: '0.75rem', fontWeight: 600, padding: '2px 10px',
                borderRadius: 'var(--radius-pill)',
                background: 'var(--primary-50)', color: 'var(--primary)',
                border: '1px solid var(--primary-200)',
              }}>
                {roleLabel[user?.role ?? ''] ?? user?.role}
              </div>
            </div>
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              padding: '0.65rem 1.4rem',
              background: '#fef2f2', border: '1.5px solid #fca5a5',
              borderRadius: 'var(--radius)', cursor: 'pointer',
              color: '#dc2626', fontWeight: 600, fontSize: '0.9rem',
              transition: 'all 0.2s',
            }}
            onMouseOver={e => {
              (e.currentTarget as HTMLButtonElement).style.background = '#dc2626';
              (e.currentTarget as HTMLButtonElement).style.color = 'white';
            }}
            onMouseOut={e => {
              (e.currentTarget as HTMLButtonElement).style.background = '#fef2f2';
              (e.currentTarget as HTMLButtonElement).style.color = '#dc2626';
            }}
          >
            🚪 Logout
          </button>
        </div>

        {/* Switch Account hint */}
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          Want to switch to a different account?{' '}
          <button
            onClick={handleLogout}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--primary)', fontWeight: 600, fontSize: '0.82rem',
              padding: 0, textDecoration: 'underline',
            }}
          >
            Logout and sign in as another user →
          </button>
        </p>
      </div>

      {/* ── Change Password ──────────────────────────────── */}
      <div className="page-section">
        <h2 className="section-title">Change Password</h2>
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleChangePassword} noValidate>
          <div className="field">
            <label className="label">Current Password</label>
            <input type="password" value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="input" placeholder="Enter current password" />
          </div>
          <div className="field">
            <label className="label">New Password</label>
            <input type="password" value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="input" placeholder="At least 8 characters" />
          </div>
          <div className="field">
            <label className="label">Confirm New Password</label>
            <input type="password" value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="input" placeholder="Re-enter new password" />
          </div>
          <button type="submit" disabled={saving} className="btn btn-primary">
            {saving ? 'Saving...' : 'Change Password'}
          </button>
        </form>
      </div>

      {/* ── Notification Preferences ─────────────────────── */}
      <div className="page-section">
        <h2 className="section-title">Notification Preferences</h2>
        <div className="settings-toggle-list">
          {[
            'New placement drive alerts',
            'Application status updates',
            'Skill recommendation alerts',
            'Interview reminders',
            'Course recommendations',
          ].map(label => (
            <label key={label} className="settings-toggle">
              <span>{label}</span>
              <input type="checkbox" defaultChecked />
            </label>
          ))}
        </div>
      </div>

      {/* ── Privacy ──────────────────────────────────────── */}
      <div className="page-section">
        <h2 className="section-title">Privacy</h2>
        <div className="settings-toggle-list">
          {[
            'Show profile to placement officers',
            'Allow companies to view my resume',
          ].map(label => (
            <label key={label} className="settings-toggle">
              <span>{label}</span>
              <input type="checkbox" defaultChecked />
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
