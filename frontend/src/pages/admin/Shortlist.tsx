import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

interface Candidate {
  profile_id: number;
  name: string;
  cgpa: number;
  compatibility_score: number;
  matched_skills: string[];
  missing_skills: string[];
}

export default function Shortlist() {
  const { logout } = useAuth();
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchShortlist = async () => {
    if (!selectedJobId) {
      setError('Please enter a Job Role ID.');
      return;
    }
    setError('');
    setMessage('');
    setLoading(true);
    setCandidates([]);
    setSelected(new Set());

    try {
      const res = await api.get(`/admin/jobs/${selectedJobId}/shortlist`);
      const data = res.data;
      if (data.message && (!data.candidates || data.candidates.length === 0)) {
        setMessage(data.message);
      } else {
        setCandidates(data.candidates || []);
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })
          ?.response?.data?.error?.message || 'Failed to load shortlist.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const toggleCandidate = (profileId: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(profileId)) {
        next.delete(profileId);
      } else {
        next.add(profileId);
      }
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === candidates.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(candidates.map((c) => c.profile_id)));
    }
  };

  const markShortlisted = async () => {
    if (selected.size === 0) {
      setError('Select at least one candidate.');
      return;
    }
    setSaving(true);
    setError('');
    setMessage('');
    try {
      await api.post(`/admin/jobs/${selectedJobId}/shortlist`, {
        profile_ids: Array.from(selected),
      });
      setMessage(`${selected.size} candidate(s) marked as shortlisted.`);
      setSelected(new Set());
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })
          ?.response?.data?.error?.message || 'Failed to shortlist candidates.';
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Candidate Shortlisting</h1>
        <div className="page-header-actions">
          <Link to="/admin/dashboard" className="back-link">
            ← Dashboard
          </Link>
          <button onClick={logout} className="dash-logout-btn">
            Logout
          </button>
        </div>
      </div>

      {/* Job Selection */}
      <div className="form-card">
        <h2 className="form-title">Select Job Role</h2>
        <div className="flex gap-2 items-center" style={{ flexWrap: 'wrap' }}>
          <label className="label-col">
            Job Role ID
            <input
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="input"
              type="number"
              min="1"
              placeholder="Enter job role ID"
              style={{ width: '180px' }}
            />
          </label>
          <button
            onClick={fetchShortlist}
            className="btn btn-primary"
            disabled={loading}
            style={{ alignSelf: 'flex-end' }}
          >
            {loading ? 'Loading...' : 'View Candidates'}
          </button>
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}
      {message && <p className="success-text">{message}</p>}

      {/* Candidate List */}
      {candidates.length > 0 && (
        <>
          <div className="shortlist-bar">
            <p className="shortlist-count">
              {candidates.length} eligible candidate(s) found
            </p>
            <button
              onClick={markShortlisted}
              className="btn btn-success"
              disabled={saving || selected.size === 0}
            >
              {saving
                ? 'Saving...'
                : `Mark Shortlisted (${selected.size})`}
            </button>
          </div>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>
                    <input
                      type="checkbox"
                      checked={selected.size === candidates.length}
                      onChange={toggleAll}
                    />
                  </th>
                  <th>Name</th>
                  <th>CGPA</th>
                  <th>Score</th>
                  <th>Matched Skills</th>
                  <th>Missing Skills</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((c) => (
                  <tr key={c.profile_id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.has(c.profile_id)}
                        onChange={() => toggleCandidate(c.profile_id)}
                      />
                    </td>
                    <td>{c.name}</td>
                    <td>{c.cgpa?.toFixed(2) ?? '—'}</td>
                    <td>
                      {(c.compatibility_score * 100).toFixed(1)}%
                    </td>
                    <td>
                      {c.matched_skills?.join(', ') || '—'}
                    </td>
                    <td>
                      {c.missing_skills?.join(', ') || 'None'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
