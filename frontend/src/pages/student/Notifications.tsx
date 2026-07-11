import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useToast } from '../../components/Toast';

interface NotificationRecord {
    id: number;
    title: string;
    message: string;
    target_audience: string;
    sender_name: string | null;
    sent_at: string;
    is_email: boolean;
    recipient_count: number;
}

const AUDIENCE_LABEL: Record<string, { label: string; color: string }> = {
    all_students: { label: 'All Students', color: '#4f46e5' },
    shortlisted: { label: 'Shortlisted', color: '#10b981' },
    specific_department: { label: 'Your Department', color: '#f59e0b' },
};

function timeAgo(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return new Date(dateStr).toLocaleDateString();
}

export default function StudentNotifications() {
    const { user, logout } = useAuth();
    const { showToast } = useToast();
    const navigate = useNavigate();
    const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [expanded, setExpanded] = useState<number | null>(null);

    const fetchNotifications = useCallback(async () => {
        setLoading(true);
        try {
            const res = await api.get('/notifications/student');
            setNotifications(res.data);
        } catch {
            showToast('Failed to load notifications', 'error');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchNotifications(); }, [fetchNotifications]);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="student-layout">
            <StudentSidebar active="notifications" sidebarOpen={sidebarOpen}
                onToggle={() => setSidebarOpen(!sidebarOpen)} onLogout={handleLogout} />

            <main className="student-main">
                <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>☰</button>

                <div className="welcome-section">
                    <h1 className="welcome-title">🔔 Notifications</h1>
                    <p className="welcome-sub">Announcements and updates from your placement cell</p>
                </div>

                {loading ? (
                    <div className="dash-loading">Loading notifications...</div>
                ) : notifications.length === 0 ? (
                    <div className="dash-widget" style={{ textAlign: 'center', padding: '3rem' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔕</div>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', fontWeight: 500 }}>
                            No notifications yet
                        </p>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                            Your placement cell will send announcements here.
                        </p>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {notifications.map((n) => {
                            const audience = AUDIENCE_LABEL[n.target_audience] ?? { label: n.target_audience, color: '#64748b' };
                            const isOpen = expanded === n.id;
                            return (
                                <div
                                    key={n.id}
                                    style={{
                                        background: 'var(--surface)',
                                        border: '1px solid var(--border)',
                                        borderRadius: 'var(--radius-lg)',
                                        overflow: 'hidden',
                                        transition: 'box-shadow 0.2s',
                                        boxShadow: isOpen ? 'var(--shadow-md)' : 'var(--shadow-xs)',
                                    }}
                                >
                                    {/* Header — always visible, click to expand */}
                                    <div
                                        onClick={() => setExpanded(isOpen ? null : n.id)}
                                        style={{
                                            display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
                                            padding: '1rem 1.25rem', cursor: 'pointer', gap: '1rem',
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', flex: 1 }}>
                                            {/* Icon */}
                                            <div style={{
                                                width: '40px', height: '40px', borderRadius: '50%', flexShrink: 0,
                                                background: `${audience.color}18`,
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                fontSize: '1.1rem',
                                            }}>
                                                📢
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem', marginBottom: '0.25rem' }}>
                                                    {n.title}
                                                </div>
                                                {!isOpen && (
                                                    <div style={{
                                                        color: 'var(--text-secondary)', fontSize: '0.82rem',
                                                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                                        maxWidth: '400px',
                                                    }}>
                                                        {n.message}
                                                    </div>
                                                )}
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.35rem', flexWrap: 'wrap' }}>
                                                    <span style={{
                                                        fontSize: '0.7rem', fontWeight: 600, padding: '2px 8px',
                                                        borderRadius: 'var(--radius-pill)',
                                                        background: `${audience.color}18`, color: audience.color,
                                                        border: `1px solid ${audience.color}40`,
                                                    }}>
                                                        {audience.label}
                                                    </span>
                                                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                                        {timeAgo(n.sent_at)}
                                                    </span>
                                                    {n.sender_name && (
                                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                                            · by {n.sender_name}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.25rem', flexShrink: 0 }}>
                                            {isOpen ? '▲' : '▼'}
                                        </span>
                                    </div>

                                    {/* Expanded message */}
                                    {isOpen && (
                                        <div style={{
                                            padding: '0 1.25rem 1.25rem 1.25rem',
                                            borderTop: '1px solid var(--border)',
                                            paddingTop: '1rem',
                                            marginTop: 0,
                                        }}>
                                            <p style={{
                                                color: 'var(--text)', fontSize: '0.9rem',
                                                lineHeight: 1.7, whiteSpace: 'pre-wrap',
                                            }}>
                                                {n.message}
                                            </p>
                                            <div style={{ marginTop: '0.75rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                                                Sent on {new Date(n.sent_at).toLocaleString()}
                                                {n.is_email && ' · Also sent via email'}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
}

/* ── Sidebar (same as Dashboard) ── */
interface SidebarProps {
    active: string;
    sidebarOpen: boolean;
    onToggle: () => void;
    onLogout: () => void;
}

function StudentSidebar({ active, sidebarOpen, onToggle, onLogout }: SidebarProps) {
    const { user } = useAuth();

    const navItems = [
        { id: 'dashboard', label: 'Dashboard', icon: '🏠', path: '/student/dashboard' },
        { id: 'profile', label: 'Profile', icon: '👤', path: '/student/profile' },
        { id: 'resume', label: 'Resume', icon: '📄', path: '/student/resume' },
        { id: 'skills', label: 'Skill Analysis', icon: '🧠', path: '/student/skills' },
        { id: 'jobs', label: 'Job Matches', icon: '💼', path: '/student/jobs' },
        { id: 'notifications', label: 'Notifications', icon: '🔔', path: '/student/notifications' },
        { id: 'settings', label: 'Settings', icon: '⚙️', path: '/student/settings' },
    ];

    return (
        <>
            {sidebarOpen && <div className="sidebar-overlay" onClick={onToggle} />}
            <aside className={`student-sidebar ${sidebarOpen ? 'open' : ''}`}>
                <div className="sidebar-brand">
                    <Link to="/">Skill2Job</Link>
                </div>
                <nav className="sidebar-nav">
                    {navItems.map((item) => (
                        <Link key={item.id} to={item.path}
                            className={`sidebar-link ${active === item.id ? 'active' : ''}`}>
                            <span className="sidebar-link-icon">{item.icon}</span>
                            <span>{item.label}</span>
                        </Link>
                    ))}
                </nav>
                <div className="sidebar-footer">
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: '0.6rem',
                        padding: '0.6rem 0.75rem', background: 'rgba(255,255,255,0.07)',
                        borderRadius: 'var(--radius)', marginBottom: '0.6rem',
                    }}>
                        <div style={{
                            width: '32px', height: '32px', borderRadius: '50%', flexShrink: 0,
                            background: 'linear-gradient(135deg,#a5b4fc,#c4b5fd)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontWeight: 700, fontSize: '0.9rem', color: '#1e1b4b',
                        }}>
                            {user?.name?.charAt(0).toUpperCase() ?? '?'}
                        </div>
                        <div style={{ overflow: 'hidden' }}>
                            <div style={{
                                fontSize: '0.82rem', fontWeight: 600, color: 'white',
                                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'
                            }}>
                                {user?.name}
                            </div>
                            <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.55)' }}>Student</div>
                        </div>
                    </div>
                    <button onClick={onLogout} className="sidebar-logout-btn">🚪 Logout</button>
                </div>
            </aside>
        </>
    );
}
