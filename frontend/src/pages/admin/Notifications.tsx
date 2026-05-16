import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useToast } from '../../components/Toast';
import api from '../../services/api';

interface NotificationEntry {
  id: number;
  title: string;
  message: string;
  target: 'all_students' | 'shortlisted' | 'specific';
  sent_at: string;
}

export default function Notifications() {
  const { showToast } = useToast();
  const [notifications, setNotifications] = useState<NotificationEntry[]>([]);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [target, setTarget] = useState<'all_students' | 'shortlisted' | 'specific'>('all_students');
  const [sending, setSending] = useState(false);

  const sendNotification = async () => {
    if (!title.trim() || !message.trim()) {
      showToast('Please fill title and message', 'error');
      return;
    }

    setSending(true);
    try {
      // In production this would call a backend API to send emails/push notifications
      const entry: NotificationEntry = {
        id: Date.now(),
        title,
        message,
        target,
        sent_at: new Date().toISOString(),
      };
      setNotifications([entry, ...notifications]);
      setTitle('');
      setMessage('');
      showToast('Notification sent successfully!', 'success');
    } catch {
      showToast('Failed to send notification', 'error');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Notifications & Announcements</h1>
        <Link to="/admin/dashboard" className="back-link">← Dashboard</Link>
      </div>

      {/* Send Notification Form */}
      <div className="dash-widget" style={{ marginBottom: '1.5rem' }}>
        <h3 className="dash-widget-title">📢 Send Notification</h3>

        <div className="field">
          <label className="label">Title *</label>
          <input type="text" className="input" value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="e.g., New Placement Drive - TechCorp" />
        </div>

        <div className="field">
          <label className="label">Message *</label>
          <textarea className="input" value={message}
            onChange={e => setMessage(e.target.value)}
            placeholder="Enter the notification message..."
            rows={4} />
        </div>

        <div className="field">
          <label className="label">Target Audience</label>
          <select className="input" value={target} onChange={e => setTarget(e.target.value as typeof target)}>
            <option value="all_students">All Students</option>
            <option value="shortlisted">Shortlisted Candidates Only</option>
            <option value="specific">Specific Department</option>
          </select>
        </div>

        <button onClick={sendNotification} disabled={sending} className="btn btn-primary">
          {sending ? 'Sending...' : '📤 Send Notification'}
        </button>
      </div>

      {/* Notification History */}
      <div className="page-section">
        <h2 className="section-title">Sent Notifications</h2>
        {notifications.length === 0 ? (
          <p className="empty-text">No notifications sent yet.</p>
        ) : (
          <div className="notification-list">
            {notifications.map(n => (
              <div key={n.id} className="notification-card">
                <div className="notification-card-header">
                  <h4>{n.title}</h4>
                  <span className="notification-target">{n.target.replace('_', ' ')}</span>
                </div>
                <p className="notification-message">{n.message}</p>
                <span className="notification-time">{new Date(n.sent_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
