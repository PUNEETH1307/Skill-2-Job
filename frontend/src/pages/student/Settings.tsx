import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { useToast } from '../../components/Toast';
import { AxiosError } from 'axios';

export default function Settings() {
  const { showToast } = useToast();
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

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <Link to="/student/dashboard" className="back-link">Back to Dashboard</Link>
      </div>

      {/* Change Password */}
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

      {/* Notification Preferences */}
      <div className="page-section">
        <h2 className="section-title">Notification Preferences</h2>
        <div className="settings-toggle-list">
          <label className="settings-toggle">
            <span>New placement drive alerts</span>
            <input type="checkbox" defaultChecked />
          </label>
          <label className="settings-toggle">
            <span>Application status updates</span>
            <input type="checkbox" defaultChecked />
          </label>
          <label className="settings-toggle">
            <span>Skill recommendation alerts</span>
            <input type="checkbox" defaultChecked />
          </label>
          <label className="settings-toggle">
            <span>Interview reminders</span>
            <input type="checkbox" defaultChecked />
          </label>
          <label className="settings-toggle">
            <span>Course recommendations</span>
            <input type="checkbox" defaultChecked />
          </label>
        </div>
      </div>

      {/* Privacy */}
      <div className="page-section">
        <h2 className="section-title">Privacy</h2>
        <div className="settings-toggle-list">
          <label className="settings-toggle">
            <span>Show profile to placement officers</span>
            <input type="checkbox" defaultChecked />
          </label>
          <label className="settings-toggle">
            <span>Allow companies to view my resume</span>
            <input type="checkbox" defaultChecked />
          </label>
        </div>
      </div>
    </div>
  );
}
