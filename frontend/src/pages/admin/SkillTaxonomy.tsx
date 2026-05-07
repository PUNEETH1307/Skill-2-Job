import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

interface TaxonomySkill {
  id: number;
  canonical_name: string;
  category: string | null;
  synonyms_json: string | null;
  is_deprecated: boolean;
}

interface UncategorizedSkill {
  id: number;
  term: string;
  occurrence_count: number;
  reviewed: boolean;
  flagged_at: string | null;
}

interface SkillForm {
  canonical_name: string;
  category: string;
  synonyms: string;
}

const emptyForm: SkillForm = {
  canonical_name: '',
  category: '',
  synonyms: '',
};

const CATEGORIES = [
  'Programming Languages',
  'Frameworks',
  'Databases',
  'Tools',
  'Soft Skills',
  'Domain Knowledge',
];

export default function SkillTaxonomy() {
  const { user: currentUser, logout } = useAuth();
  const [skills, setSkills] = useState<TaxonomySkill[]>([]);
  const [uncategorized, setUncategorized] = useState<UncategorizedSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState<SkillForm>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  // Admin-only check
  if (currentUser?.role !== 'admin') {
    return (
      <div className="page-container">
        <p className="error-text">
          Access denied. Only administrators can manage the skill taxonomy.
        </p>
        <Link to="/admin/dashboard">← Back to Dashboard</Link>
      </div>
    );
  }

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const [taxRes, uncatRes] = await Promise.all([
        api.get('/admin/skills/taxonomy'),
        api.get('/admin/skills/uncategorized'),
      ]);
      setSkills(taxRes.data);
      setUncategorized(uncatRes.data);
    } catch {
      setError('Failed to load skill taxonomy.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const parseSynonyms = (raw: string): string[] =>
    raw
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!form.canonical_name.trim()) {
      setFormError('Canonical name is required.');
      return;
    }

    const payload = {
      canonical_name: form.canonical_name.trim(),
      category: form.category || null,
      synonyms_json: parseSynonyms(form.synonyms),
    };

    setSaving(true);
    try {
      if (editingId) {
        await api.put(`/admin/skills/taxonomy/${editingId}`, payload);
      } else {
        await api.post('/admin/skills/taxonomy', payload);
      }
      setForm(emptyForm);
      setEditingId(null);
      await fetchData();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })
          ?.response?.data?.error?.message || 'Failed to save skill.';
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (s: TaxonomySkill) => {
    let synonyms = '';
    if (s.synonyms_json) {
      try {
        const arr = JSON.parse(s.synonyms_json);
        if (Array.isArray(arr)) synonyms = arr.join(', ');
      } catch {
        synonyms = s.synonyms_json;
      }
    }
    setEditingId(s.id);
    setForm({
      canonical_name: s.canonical_name,
      category: s.category || '',
      synonyms,
    });
    setFormError('');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm(emptyForm);
    setFormError('');
  };

  const handleDeprecate = async (id: number) => {
    if (!confirm('Deprecate this skill? It will be excluded from future extractions.'))
      return;
    try {
      await api.delete(`/admin/skills/taxonomy/${id}`);
      await fetchData();
    } catch {
      setError('Failed to deprecate skill.');
    }
  };

  const renderSynonyms = (json: string | null) => {
    if (!json) return '—';
    try {
      const arr = JSON.parse(json);
      return Array.isArray(arr) && arr.length > 0 ? arr.join(', ') : '—';
    } catch {
      return json;
    }
  };

  const activeSkills = skills.filter((s) => !s.is_deprecated);
  const deprecatedSkills = skills.filter((s) => s.is_deprecated);

  return (
    <div className="page-container-wide">
      <div className="page-header-narrow">
        <h1 className="page-title">Skill Taxonomy Management</h1>
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

      {/* Add / Edit Form */}
      <div className="form-card">
        <h2 className="form-title">
          {editingId ? 'Edit Skill' : 'Add Skill'}
        </h2>
        {formError && <p className="error-text">{formError}</p>}
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="label-col">
              Canonical Name *
              <input
                name="canonical_name"
                value={form.canonical_name}
                onChange={handleChange}
                className="input"
                required
              />
            </label>
            <label className="label-col">
              Category
              <select
                name="category"
                value={form.category}
                onChange={handleChange}
                className="input"
              >
                <option value="">Select category</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label className="label-col">
              Synonyms (comma-separated)
              <input
                name="synonyms"
                value={form.synonyms}
                onChange={handleChange}
                className="input"
                placeholder="JS, ECMAScript"
              />
            </label>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : editingId ? 'Update' : 'Add Skill'}
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

      {loading ? (
        <p className="loading-text"><span className="spinner" /> Loading taxonomy...</p>
      ) : error ? (
        <p className="error-text">{error}</p>
      ) : (
        <>
          {/* Active Skills */}
          <div className="page-section">
            <h2 className="section-title">
              Active Skills ({activeSkills.length})
            </h2>
            {activeSkills.length === 0 ? (
              <p className="muted-text">No skills in taxonomy.</p>
            ) : (
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Canonical Name</th>
                      <th>Category</th>
                      <th>Synonyms</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeSkills.map((s) => (
                      <tr key={s.id}>
                        <td>{s.canonical_name}</td>
                        <td>{s.category || '—'}</td>
                        <td>
                          {renderSynonyms(s.synonyms_json)}
                        </td>
                        <td>
                          <span className="flex gap-1">
                            <button
                              onClick={() => startEdit(s)}
                              className="btn btn-warning btn-sm"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleDeprecate(s.id)}
                              className="btn btn-danger btn-sm"
                            >
                              Deprecate
                            </button>
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Deprecated Skills */}
          {deprecatedSkills.length > 0 && (
            <div className="page-section">
              <h2 className="section-title">
                Deprecated Skills ({deprecatedSkills.length})
              </h2>
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Canonical Name</th>
                      <th>Category</th>
                      <th>Synonyms</th>
                    </tr>
                  </thead>
                  <tbody>
                    {deprecatedSkills.map((s) => (
                      <tr key={s.id} className="row-deprecated">
                        <td>{s.canonical_name}</td>
                        <td>{s.category || '—'}</td>
                        <td>
                          {renderSynonyms(s.synonyms_json)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Uncategorized Skills */}
          <div className="page-section">
            <h2 className="section-title">
              Uncategorized Skills ({uncategorized.length})
            </h2>
            {uncategorized.length === 0 ? (
              <p className="muted-text">
                No uncategorized skills flagged for review.
              </p>
            ) : (
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Term</th>
                      <th>Occurrences</th>
                      <th>Flagged At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {uncategorized.map((s) => (
                      <tr key={s.id}>
                        <td>{s.term}</td>
                        <td>{s.occurrence_count}</td>
                        <td>
                          {s.flagged_at
                            ? new Date(s.flagged_at).toLocaleDateString()
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
