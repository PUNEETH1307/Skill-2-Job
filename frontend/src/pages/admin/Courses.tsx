import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

interface CourseForm {
  skill_name: string;
  course_name: string;
  provider: string;
  url: string;
}

interface CourseRecord {
  id: number;
  skill_name: string;
  course_name: string;
  provider: string | null;
  url: string | null;
  created_at: string | null;
}

const emptyForm: CourseForm = {
  skill_name: '',
  course_name: '',
  provider: '',
  url: '',
};

export default function Courses() {
  const { logout } = useAuth();
  const [form, setForm] = useState<CourseForm>(emptyForm);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);
  const [recentCourses, setRecentCourses] = useState<CourseRecord[]>([]);
  const [successMsg, setSuccessMsg] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSuccessMsg('');

    if (!form.skill_name.trim()) {
      setFormError('Skill name is required.');
      return;
    }
    if (!form.course_name.trim()) {
      setFormError('Course name is required.');
      return;
    }

    setSaving(true);
    try {
      const res = await api.post('/admin/courses', {
        skill_name: form.skill_name.trim(),
        course_name: form.course_name.trim(),
        provider: form.provider.trim() || null,
        url: form.url.trim() || null,
      });
      setRecentCourses((prev) => [res.data, ...prev]);
      setForm(emptyForm);
      setSuccessMsg('Course recommendation added successfully.');
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })
          ?.response?.data?.error?.message ||
        'Failed to add course recommendation.';
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Course Recommendations</h1>
        <div className="page-header-actions">
          <Link to="/admin/dashboard" className="back-link">
            ← Dashboard
          </Link>
          <button onClick={logout} className="dash-logout-btn">
            Logout
          </button>
        </div>
      </div>

      <p className="section-description">
        Add course recommendations that will be suggested to students when they
        have skill gaps. Each course is mapped to a specific skill.
      </p>

      {/* Add Course Form */}
      <div className="form-card">
        <h2 className="form-title">Add Course Recommendation</h2>
        {formError && <p className="error-text">{formError}</p>}
        {successMsg && <p className="success-text">{successMsg}</p>}
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="label-col">
              Skill Name *
              <input
                name="skill_name"
                value={form.skill_name}
                onChange={handleChange}
                className="input"
                placeholder="e.g. Python"
                required
              />
            </label>
            <label className="label-col">
              Course Name *
              <input
                name="course_name"
                value={form.course_name}
                onChange={handleChange}
                className="input"
                placeholder="e.g. Python for Beginners"
                required
              />
            </label>
            <label className="label-col">
              Provider
              <input
                name="provider"
                value={form.provider}
                onChange={handleChange}
                className="input"
                placeholder="e.g. Coursera, Udemy"
              />
            </label>
            <label className="label-col">
              URL
              <input
                name="url"
                value={form.url}
                onChange={handleChange}
                className="input"
                placeholder="https://..."
                type="url"
              />
            </label>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Adding...' : 'Add Course'}
            </button>
          </div>
        </form>
      </div>

      {/* Recently Added */}
      {recentCourses.length > 0 && (
        <div className="page-section">
          <h2 className="section-title">Recently Added</h2>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Skill</th>
                  <th>Course</th>
                  <th>Provider</th>
                  <th>URL</th>
                </tr>
              </thead>
              <tbody>
                {recentCourses.map((c) => (
                  <tr key={c.id}>
                    <td>{c.skill_name}</td>
                    <td>{c.course_name}</td>
                    <td>{c.provider || '—'}</td>
                    <td>
                      {c.url ? (
                        <a
                          href={c.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="table-link"
                        >
                          Link
                        </a>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
