import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { AxiosError } from 'axios';

interface SkillCategory {
  category: string;
  skills: string[];
}

export default function SkillAnalysis() {
  const [categories, setCategories] = useState<SkillCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const res = await api.get('/skills/analysis');
        const data = res.data;

        // The API may return { categories: { "Programming Languages": [...], ... } }
        // or a flat object. Normalize to array of { category, skills }.
        if (data.categories && typeof data.categories === 'object') {
          const cats: SkillCategory[] = Object.entries(data.categories).map(
            ([category, skills]) => ({
              category,
              skills: Array.isArray(skills) ? (skills as string[]) : [],
            })
          );
          setCategories(cats);
        } else if (Array.isArray(data)) {
          setCategories(data);
        } else {
          // Try treating the whole response as category map
          const cats: SkillCategory[] = Object.entries(data)
            .filter(([key]) => key !== 'total_skills')
            .map(([category, skills]) => ({
              category,
              skills: Array.isArray(skills) ? (skills as string[]) : [],
            }));
          setCategories(cats);
        }
      } catch (err) {
        if (err instanceof AxiosError && err.response) {
          setError(err.response.data?.error?.message ?? 'Failed to load skill analysis.');
        } else {
          setError('Unable to connect to the server.');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchAnalysis();
  }, []);

  const totalSkills = categories.reduce((sum, c) => sum + c.skills.length, 0);

  if (loading) {
    return (
      <div className="page-container">
        <p className="loading-text"><span className="spinner" /> Loading skill analysis...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Skill Analysis</h1>
        <Link to="/student/dashboard" className="back-link">Back to Dashboard</Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {!error && totalSkills === 0 && (
        <div className="empty-state">
          <p>No skills found. Please update your profile with skills to see the analysis.</p>
          <Link to="/student/profile" className="back-link">Go to Profile</Link>
        </div>
      )}

      {!error && totalSkills > 0 && (
        <>
          <p className="summary-text">Total skills identified: <strong>{totalSkills}</strong></p>
          <div className="skill-grid">
            {categories.filter(c => c.skills.length > 0).map((cat) => (
              <div key={cat.category} className="skill-category-card">
                <h3 className="skill-category-title">{cat.category}</h3>
                <p className="skill-category-count">{cat.skills.length} skill{cat.skills.length !== 1 ? 's' : ''}</p>
                <div className="tags-container">
                  {cat.skills.map((skill, idx) => (
                    <span key={idx} className="tag">{skill}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
