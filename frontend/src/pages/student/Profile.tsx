import { useState, useEffect, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { AxiosError } from 'axios';

interface ProjectEntry {
  title: string;
  description: string;
  technologies: string;
}

interface CertificationEntry {
  name: string;
  issuer: string;
  issue_date: string;
}

interface ProfileData {
  institution: string;
  degree: string;
  branch: string;
  cgpa: string;
  graduation_year: string;
  skills: string[];
  projects: ProjectEntry[];
  certifications: CertificationEntry[];
}

interface FieldErrors {
  institution?: string;
  degree?: string;
  branch?: string;
  cgpa?: string;
  graduation_year?: string;
  general?: string;
}

const emptyProject: ProjectEntry = { title: '', description: '', technologies: '' };
const emptyCert: CertificationEntry = { name: '', issuer: '', issue_date: '' };

export default function Profile() {
  const [form, setForm] = useState<ProfileData>({
    institution: '',
    degree: '',
    branch: '',
    cgpa: '',
    graduation_year: '',
    skills: [],
    projects: [],
    certifications: [],
  });
  const [skillInput, setSkillInput] = useState('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [fetchError, setFetchError] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get('/profile');
        const d = res.data;
        setForm({
          institution: d.institution ?? '',
          degree: d.degree ?? '',
          branch: d.branch ?? '',
          cgpa: d.cgpa != null ? String(d.cgpa) : '',
          graduation_year: d.graduation_year != null ? String(d.graduation_year) : '',
          skills: Array.isArray(d.skills) ? d.skills : [],
          projects: Array.isArray(d.projects) ? d.projects : [],
          certifications: Array.isArray(d.certifications) ? d.certifications : [],
        });
      } catch (err) {
        if (err instanceof AxiosError && err.response?.status === 404) {
          // No profile yet — keep defaults
        } else {
          setFetchError('Failed to load profile. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const validate = (): boolean => {
    const e: FieldErrors = {};
    if (!form.institution.trim()) e.institution = 'Institution is required.';
    if (!form.degree.trim()) e.degree = 'Degree is required.';
    if (!form.branch.trim()) e.branch = 'Branch is required.';

    const cgpaNum = parseFloat(form.cgpa);
    if (form.cgpa === '') {
      e.cgpa = 'CGPA is required.';
    } else if (isNaN(cgpaNum) || cgpaNum < 0.0 || cgpaNum > 10.0) {
      e.cgpa = 'CGPA must be between 0.0 and 10.0.';
    }

    if (!form.graduation_year.trim()) {
      e.graduation_year = 'Graduation year is required.';
    }

    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (ev: FormEvent) => {
    ev.preventDefault();
    setSuccessMsg('');
    if (!validate()) return;

    setSaving(true);
    setErrors({});
    try {
      await api.put('/profile', {
        institution: form.institution,
        degree: form.degree,
        branch: form.branch,
        cgpa: parseFloat(form.cgpa),
        graduation_year: parseInt(form.graduation_year, 10),
        skills: form.skills,
        projects: form.projects,
        certifications: form.certifications,
      });
      setSuccessMsg('Profile saved successfully!');
    } catch (err) {
      if (err instanceof AxiosError && err.response) {
        const apiErr = err.response.data?.error;
        setErrors({ general: apiErr?.message ?? 'Failed to save profile.' });
      } else {
        setErrors({ general: 'Unable to connect to the server.' });
      }
    } finally {
      setSaving(false);
    }
  };

  const addSkill = () => {
    const s = skillInput.trim();
    if (s && !form.skills.includes(s)) {
      setForm({ ...form, skills: [...form.skills, s] });
    }
    setSkillInput('');
  };

  const removeSkill = (idx: number) => {
    setForm({ ...form, skills: form.skills.filter((_, i) => i !== idx) });
  };

  const addProject = () => {
    setForm({ ...form, projects: [...form.projects, { ...emptyProject }] });
  };

  const updateProject = (idx: number, field: keyof ProjectEntry, value: string) => {
    const updated = form.projects.map((p, i) => (i === idx ? { ...p, [field]: value } : p));
    setForm({ ...form, projects: updated });
  };

  const removeProject = (idx: number) => {
    setForm({ ...form, projects: form.projects.filter((_, i) => i !== idx) });
  };

  const addCertification = () => {
    setForm({ ...form, certifications: [...form.certifications, { ...emptyCert }] });
  };

  const updateCert = (idx: number, field: keyof CertificationEntry, value: string) => {
    const updated = form.certifications.map((c, i) => (i === idx ? { ...c, [field]: value } : c));
    setForm({ ...form, certifications: updated });
  };

  const removeCert = (idx: number) => {
    setForm({ ...form, certifications: form.certifications.filter((_, i) => i !== idx) });
  };

  if (loading) {
    return (
      <div className="page-container">
        <p className="loading-text"><span className="spinner" /> Loading profile...</p>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="page-container">
        <div className="alert alert-error">{fetchError}</div>
        <Link to="/student/dashboard" className="back-link">Back to Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">My Profile</h1>
        <Link to="/student/dashboard" className="back-link">Back to Dashboard</Link>
      </div>

      {successMsg && <div className="alert alert-success">{successMsg}</div>}
      {errors.general && <div className="alert alert-error">{errors.general}</div>}

      <form onSubmit={handleSubmit} noValidate>
        {/* Academic Details */}
        <div className="page-section">
          <h2 className="section-title">Academic Details</h2>

          <div className="field">
            <label htmlFor="institution" className="label">Institution</label>
            <input id="institution" type="text" value={form.institution}
              onChange={(e) => setForm({ ...form, institution: e.target.value })}
              className={`input${errors.institution ? ' input-error' : ''}`} />
            {errors.institution && <span className="field-error">{errors.institution}</span>}
          </div>

          <div className="field">
            <label htmlFor="degree" className="label">Degree</label>
            <input id="degree" type="text" value={form.degree}
              onChange={(e) => setForm({ ...form, degree: e.target.value })}
              className={`input${errors.degree ? ' input-error' : ''}`} />
            {errors.degree && <span className="field-error">{errors.degree}</span>}
          </div>

          <div className="field">
            <label htmlFor="branch" className="label">Branch</label>
            <input id="branch" type="text" value={form.branch}
              onChange={(e) => setForm({ ...form, branch: e.target.value })}
              className={`input${errors.branch ? ' input-error' : ''}`} />
            {errors.branch && <span className="field-error">{errors.branch}</span>}
          </div>

          <div className="field-row">
            <div className="field field-flex">
              <label htmlFor="cgpa" className="label">CGPA (0.0 - 10.0)</label>
              <input id="cgpa" type="number" step="0.01" min="0" max="10" value={form.cgpa}
                onChange={(e) => setForm({ ...form, cgpa: e.target.value })}
                className={`input${errors.cgpa ? ' input-error' : ''}`} />
              {errors.cgpa && <span className="field-error">{errors.cgpa}</span>}
            </div>
            <div className="field field-flex">
              <label htmlFor="graduation_year" className="label">Graduation Year</label>
              <input id="graduation_year" type="number" value={form.graduation_year}
                onChange={(e) => setForm({ ...form, graduation_year: e.target.value })}
                className={`input${errors.graduation_year ? ' input-error' : ''}`} />
              {errors.graduation_year && <span className="field-error">{errors.graduation_year}</span>}
            </div>
          </div>
        </div>

        {/* Skills */}
        <div className="page-section">
          <h2 className="section-title">Skills</h2>
          <div className="skill-input-row">
            <input type="text" value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addSkill(); } }}
              placeholder="Type a skill and press Enter or Add"
              className="input" />
            <button type="button" onClick={addSkill} className="btn btn-primary">Add</button>
          </div>
          <div className="tags-container">
            {form.skills.map((skill, idx) => (
              <span key={idx} className="tag-removable">
                {skill}
                <button type="button" onClick={() => removeSkill(idx)} className="tag-remove-btn">&times;</button>
              </span>
            ))}
            {form.skills.length === 0 && <p className="empty-text">No skills added yet.</p>}
          </div>
        </div>

        {/* Projects */}
        <div className="page-section">
          <h2 className="section-title">Projects</h2>
          {form.projects.map((proj, idx) => (
            <div key={idx} className="entry-card">
              <div className="entry-header">
                <strong>Project {idx + 1}</strong>
                <button type="button" onClick={() => removeProject(idx)} className="btn btn-danger btn-sm">Remove</button>
              </div>
              <div className="field">
                <label className="label">Title</label>
                <input type="text" value={proj.title}
                  onChange={(e) => updateProject(idx, 'title', e.target.value)} className="input" />
              </div>
              <div className="field">
                <label className="label">Description</label>
                <textarea value={proj.description}
                  onChange={(e) => updateProject(idx, 'description', e.target.value)}
                  className="input" />
              </div>
              <div className="field">
                <label className="label">Technologies</label>
                <input type="text" value={proj.technologies}
                  onChange={(e) => updateProject(idx, 'technologies', e.target.value)} className="input" />
              </div>
            </div>
          ))}
          <button type="button" onClick={addProject} className="btn btn-primary">+ Add Project</button>
        </div>

        {/* Certifications */}
        <div className="page-section">
          <h2 className="section-title">Certifications</h2>
          {form.certifications.map((cert, idx) => (
            <div key={idx} className="entry-card">
              <div className="entry-header">
                <strong>Certification {idx + 1}</strong>
                <button type="button" onClick={() => removeCert(idx)} className="btn btn-danger btn-sm">Remove</button>
              </div>
              <div className="field">
                <label className="label">Name</label>
                <input type="text" value={cert.name}
                  onChange={(e) => updateCert(idx, 'name', e.target.value)} className="input" />
              </div>
              <div className="field">
                <label className="label">Issuer</label>
                <input type="text" value={cert.issuer}
                  onChange={(e) => updateCert(idx, 'issuer', e.target.value)} className="input" />
              </div>
              <div className="field">
                <label className="label">Issue Date</label>
                <input type="date" value={cert.issue_date}
                  onChange={(e) => updateCert(idx, 'issue_date', e.target.value)} className="input" />
              </div>
            </div>
          ))}
          <button type="button" onClick={addCertification} className="btn btn-primary">+ Add Certification</button>
        </div>

        <button type="submit" disabled={saving} className="btn btn-success btn-block mt-1">
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </form>
    </div>
  );
}
