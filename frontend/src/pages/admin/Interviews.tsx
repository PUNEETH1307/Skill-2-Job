import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useToast } from '../../components/Toast';

interface InterviewSlot {
  id: number;
  student_name: string;
  job_title: string;
  company: string;
  date: string;
  time: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  feedback: string;
}

export default function Interviews() {
  const { showToast } = useToast();
  const [interviews, setInterviews] = useState<InterviewSlot[]>([
    { id: 1, student_name: 'Sample Student', job_title: 'Software Engineer', company: 'TechCorp', date: '2026-05-20', time: '10:00 AM', status: 'scheduled', feedback: '' },
  ]);
  const [showForm, setShowForm] = useState(false);
  const [newInterview, setNewInterview] = useState({ student_name: '', job_title: '', company: '', date: '', time: '' });
  const [filter, setFilter] = useState<'all' | 'scheduled' | 'completed' | 'cancelled'>('all');

  const addInterview = () => {
    if (!newInterview.student_name || !newInterview.job_title || !newInterview.date) {
      showToast('Please fill all required fields', 'error');
      return;
    }
    const slot: InterviewSlot = {
      id: Date.now(),
      ...newInterview,
      status: 'scheduled',
      feedback: '',
    };
    setInterviews([slot, ...interviews]);
    setNewInterview({ student_name: '', job_title: '', company: '', date: '', time: '' });
    setShowForm(false);
    showToast('Interview scheduled successfully!', 'success');
  };

  const updateStatus = (id: number, status: InterviewSlot['status']) => {
    setInterviews(interviews.map(i => i.id === id ? { ...i, status } : i));
    showToast(`Interview marked as ${status}`, 'info');
  };

  const filtered = filter === 'all' ? interviews : interviews.filter(i => i.status === filter);

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Interview Management</h1>
        <div className="page-header-actions">
          <Link to="/admin/dashboard" className="back-link">← Dashboard</Link>
          <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
            + Schedule Interview
          </button>
        </div>
      </div>

      {/* Schedule Form */}
      {showForm && (
        <div className="dash-widget" style={{ marginBottom: '1.5rem' }}>
          <h3 className="dash-widget-title">Schedule New Interview</h3>
          <div className="field-row">
            <div className="field">
              <label className="label">Student Name *</label>
              <input type="text" className="input" value={newInterview.student_name}
                onChange={e => setNewInterview({ ...newInterview, student_name: e.target.value })} />
            </div>
            <div className="field">
              <label className="label">Job Title *</label>
              <input type="text" className="input" value={newInterview.job_title}
                onChange={e => setNewInterview({ ...newInterview, job_title: e.target.value })} />
            </div>
          </div>
          <div className="field-row">
            <div className="field">
              <label className="label">Company</label>
              <input type="text" className="input" value={newInterview.company}
                onChange={e => setNewInterview({ ...newInterview, company: e.target.value })} />
            </div>
            <div className="field">
              <label className="label">Date *</label>
              <input type="date" className="input" value={newInterview.date}
                onChange={e => setNewInterview({ ...newInterview, date: e.target.value })} />
            </div>
          </div>
          <div className="field" style={{ maxWidth: '300px' }}>
            <label className="label">Time</label>
            <input type="text" className="input" placeholder="e.g., 10:00 AM" value={newInterview.time}
              onChange={e => setNewInterview({ ...newInterview, time: e.target.value })} />
          </div>
          <div className="btn-row">
            <button onClick={addInterview} className="btn btn-success">Schedule</button>
            <button onClick={() => setShowForm(false)} className="btn btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="filter-row" style={{ marginBottom: '1rem' }}>
        {(['all', 'scheduled', 'completed', 'cancelled'] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'}`}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Interview Table */}
      {filtered.length === 0 ? (
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
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(interview => (
                <tr key={interview.id}>
                  <td>{interview.student_name}</td>
                  <td>{interview.job_title}</td>
                  <td>{interview.company}</td>
                  <td>{interview.date}</td>
                  <td>{interview.time}</td>
                  <td>
                    <span className={`status-badge status-${interview.status}`}>
                      {interview.status}
                    </span>
                  </td>
                  <td>
                    <div className="btn-row">
                      {interview.status === 'scheduled' && (
                        <>
                          <button onClick={() => updateStatus(interview.id, 'completed')} className="btn btn-sm btn-success">Complete</button>
                          <button onClick={() => updateStatus(interview.id, 'cancelled')} className="btn btn-sm btn-danger">Cancel</button>
                        </>
                      )}
                    </div>
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
