import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { useToast } from '../../components/Toast';
import { AxiosError } from 'axios';

interface NotificationRecord {
  id: number;
  sent_by: number | null;
  sender_name: string | null;
  title: string;
  message: string;
  target_audience: string;
  target_department: string | null;
  is_email: boolean;
  recipient_count: number;
  sent_at: string;
}

export default function Notifications() {
  const { showToast } = useToast();
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [target, setTarget] = useState<string>('all_students');
  const [targetDept, setTargetDept] = useState('');
  const [sendEmail, setSendEmail] = useState(false);
  const [sending, setSending] = useState(false);
  const [formError, setFormError] = useState('');

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/notifications');
      setNotifications(res.data);
    } catch {
      showToast('Failed to load notifications', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchNotifications(); }, [fetchNotifications]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    if (!title.trim() || !message.trim()) {
      setFormError('Title and message are required.');
      return;
    }
    setSending(true);
    try {
      await api.post('/notifications', {
        title: title.trim(),
        message: message.trim(),
        target_audience: target,
        target_department: target === 'specific_department' ? targetDept : null,
        send_email: sendEmail,
      });
      showToast('Notification sent successfully!', 'success');
      setTitle('');
      setMessage('');
      setTarget('all_students');
      setTargetDept('');
      setSendEmail(false);
      fetchNotifications();
    } catch (err) {
      const msg = (err instanceof AxiosError && err.response?.data?.error?.message) || 'Failed to send notification.';
      setFormError(msg);
      showToast('Failed to send notification', 'error');
    } finally {
      setSending(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this notification record?')) return;
    try {
      await api.delete(`/notifications/${id}`);
      showToast('Notification deleted', 'info');
      fetchNotifications();
    } catch {
      showToast('Failed to delete notification', 'error');
    }
  };

  const audienceLabel = (n: NotificationRecord) => {
    if (n.target_audience === 'all_students') return 'All Students';
    if (n.target_audience === 'shortlisted') return 'Shortlisted Only';
    if (n.target_audience === 'specific_department') return `Dept: ${n.target_department || '—'}`;
    return n.target_audience;
  };

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Notifications & Announcements</h1>
        <Link to="/admin/dashboard" className="back-link">← Dashboard</Link>
      </div>

      {/* Send Form */}
      <div className="dash-widget" style={{ marginBottom: '1.5rem' }}>
        <h3 className="dash-widget-title">📢 Send Notification</h3>
        {formError && <div className="alert alert-error">{formError}</div>}
        <form onSubmit={handleSend}>
          <div className="field">
            <label className="label">Title *</label>
            <input type="text" className="input" value={title} onChange={e => setTitle(e.target.value)}
              placeholder="e.g. New Placement Drive – TechCorp" />
          </div>
          <div className="field">
            <label className="label">Message *</label>
            <textarea className="input" value={message} onChange={e => setMessage(e.target.value)}
              placeholder="Enter the notification message..." rows={4} />
          </div>
          <div className="field-row">
            <div className="field">
              <label className="label">Target Audience</label>
              <select className="input" value={target} onChange={e => setTarget(e.target.value)}>
                <option value="all_students">All Students</option>
                <option value="shortlisted">Shortlisted Candidates Only</option>
                <option value="specific_department">Specific Department</option>
              </select>
            </div>
            {target === 'specific_department' && (
              <div className="field">
                <label className="label">Department Name</label>
                <input type="text" className="input" value={targetDept} onChange={e => setTargetDept(e.target.value)}
                  placeholder="e.g. Computer Science" />
              </div>
            )}
          </div>
          <div className="field" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input type="checkbox" id="sendEmail" checked={sendEmail} onChange={e => setSendEmail(e.target.checked)} />
            <label htmlFor="sendEmail" className="label" style={{ margin: 0 }}>
              Also send via email to recipients
            </label>
          </div>
          <button type="submit" disabled={sending} className="btn btn-primary">
            {sending ? 'Sending...' : '📤 Send Notification'}
          </button>
        </form>
      </div>

      {/* History */}
      <div className="page-section">
        <h2 className="section-title">Sent Notifications</h2>
        {loading ? (
          <p className="loading-text"><span className="spinner" /> Loading...</p>
        ) : notifications.length === 0 ? (
          <p className="empty-text">No notifications sent yet.</p>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Message</th>
                  <th>Audience</th>
                  <th>Recipients</th>
                  <th>Email</th>
                  <th>Sent By</th>
                  <th>Sent At</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {notifications.map(n => (
                  <tr key={n.id}>
                    <td style={{ fontWeight: 600 }}>{n.title}</td>
                    <td style={{ maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{n.message}</td>
                    <td>{audienceLabel(n)}</td>
                    <td>{n.recipient_count}</td>
                    <td>{n.is_email ? '✓' : '—'}</td>
                    <td>{n.sender_name || '—'}</td>
                    <td>{new Date(n.sent_at).toLocaleString()}</td>
                    <td>
                      <button onClick={() => handleDelete(n.id)} className="btn btn-sm btn-danger">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
