import { useEffect, useState, type ChangeEvent } from 'react';
import { Link } from 'react-router-dom';
import { AxiosError } from 'axios';
import api from '../../services/api';
import { useToast } from '../../components/Toast';
import { useAuth } from '../../context/AuthContext';

interface ResumeUploadEntry {
  id: number;
  original_filename: string;
  content_type: string;
  uploaded_at: string;
}

type TemplateId = 'classic' | 'modern' | 'minimal';

interface ResumeDraftForm {
  summary: string;
  education: string;
  skills: string;
  projects: string;
  certificates: string;
  courses: string;
  languages: string;
  linkedin: string;
  github: string;
  portfolio: string;
}

const TEMPLATE_OPTIONS: Array<{
  id: TemplateId;
  label: string;
  description: string;
  accent: string;
  previewClass: string;
}> = [
  {
    id: 'classic',
    label: 'Classic',
    description: 'Clean blue resume with strong section spacing.',
    accent: '#1a237e',
    previewClass: 'resume-preview-classic',
  },
  {
    id: 'modern',
    label: 'Modern',
    description: 'Teal accent with a polished, balanced layout.',
    accent: '#0d9488',
    previewClass: 'resume-preview-modern',
  },
  {
    id: 'minimal',
    label: 'Minimal',
    description: 'Monochrome resume for a simple professional look.',
    accent: '#111827',
    previewClass: 'resume-preview-minimal',
  },
];

const EMPTY_FORM: ResumeDraftForm = {
  summary: '',
  education: '',
  skills: '',
  projects: '',
  certificates: '',
  courses: '',
  languages: '',
  linkedin: '',
  github: '',
  portfolio: '',
};

function splitNonEmptyLines(value: string): string[] {
  return value
    .replace(/\r/g, '\n')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

function splitCommaList(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function stringifyProjects(value: any[] | undefined): string {
  if (!value || value.length === 0) return '';
  return value
    .map((project) => {
      const title = project.title ?? project.name ?? '';
      const description = project.description ?? '';
      const technologies = project.technologies ?? '';
      return [title, description, technologies].filter(Boolean).join('\n');
    })
    .join('\n\n');
}

function stringifyCertifications(value: any[] | undefined): string {
  if (!value || value.length === 0) return '';
  return value.map((cert) => cert.name ?? cert.title ?? '').filter(Boolean).join('\n');
}

export default function Resume() {
  const { showToast } = useToast();
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploads, setUploads] = useState<ResumeUploadEntry[]>([]);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [generatedFile, setGeneratedFile] = useState('');
  const [missingSections, setMissingSections] = useState<string[]>([]);
  const [dreamJob, setDreamJob] = useState<string | null>(null);
  const { user } = useAuth();

  const [selectedTemplate, setSelectedTemplate] = useState<TemplateId>('classic');

  // Profile data for preview / missing-field checks
  const [profileData, setProfileData] = useState<any | null>(null);
  const [showMissingModal, setShowMissingModal] = useState(false);
  const [profileForm, setProfileForm] = useState<ResumeDraftForm>(EMPTY_FORM);

  const fetchUploads = async () => {
    try {
      const res = await api.get('/resume/uploads');
      setUploads(res.data.uploads ?? []);
    } catch {
      setUploads([]);
    }
  };

  const fetchProfile = async () => {
    try {
      const res = await api.get('/profile');
      setDreamJob(res.data.dream_job ?? null);
      setProfileData(res.data ?? null);
      const existingLinks = res.data?.links ?? {};
      setProfileForm({
        summary: res.data?.dream_job ? `Seeking a ${res.data.dream_job} role with strong software development and problem-solving skills.` : '',
        education: [
          res.data?.degree,
          res.data?.institution,
          res.data?.branch,
          res.data?.cgpa != null ? `CGPA: ${res.data.cgpa}` : '',
          res.data?.graduation_year ? `Batch: ${res.data.graduation_year}` : '',
        ].filter(Boolean).join('\n'),
        skills: (() => {
          try {
            return res.data?.skills_json ? JSON.parse(res.data.skills_json).join(', ') : '';
          } catch {
            return '';
          }
        })(),
        projects: stringifyProjects(res.data?.projects),
        certificates: stringifyCertifications(res.data?.certifications),
        courses: '',
        languages: '',
        linkedin: existingLinks.linkedin ?? '',
        github: existingLinks.github ?? '',
        portfolio: existingLinks.portfolio ?? '',
      });
    } catch {
      setDreamJob(null);
      setProfileData(null);
    }
  };

  useEffect(() => {
    fetchUploads();
    fetchProfile();
  }, []);

  const readApiError = (err: unknown, fallback: string) => {
    if (err instanceof AxiosError && err.response) {
      return err.response.data?.error?.message ?? fallback;
    }
    return 'Unable to connect to the server.';
  };

  const computeMissingSections = (profile: any | null) => {
    const missing: string[] = [];
    if (!profile?.skills_json || !String(profile.skills_json).trim()) missing.push('Technical Skills');
    if (!profile?.projects || profile.projects.length === 0) missing.push('Projects');
    if (!profile?.certifications || profile.certifications.length === 0) missing.push('Certificates');
    if (!profileForm.summary.trim()) missing.push('Profile');
    if (!profileForm.education.trim()) missing.push('Education');
    if (!profileForm.courses.trim()) missing.push('Courses');
    if (!profileForm.languages.trim()) missing.push('Languages');
    if (!profileForm.linkedin.trim() && !profileForm.github.trim() && !profileForm.portfolio.trim()) missing.push('Links');
    return missing;
  };

  const buildProfileOverride = () => ({
    summary: profileForm.summary,
    education: profileForm.education,
    skills: profileForm.skills,
    projects: profileForm.projects,
    certifications: profileForm.certificates,
    courses: profileForm.courses,
    languages: profileForm.languages,
    links: {
      linkedin: profileForm.linkedin,
      github: profileForm.github,
      portfolio: profileForm.portfolio,
    },
  });

  const handleGenerate = async (useOverrides = false, skipValidation = false) => {
    setError('');
    setSuccessMsg('');

    const missing = computeMissingSections(profileData);
    if (missing.length > 0 && !useOverrides && !skipValidation) {
      setMissingSections(missing);
      setShowMissingModal(true);
      return;
    }

    setGenerating(true);
    try {
      const payload: any = { template: selectedTemplate };
      if (useOverrides) {
        payload.profile_override = buildProfileOverride();
      }
      const res = await api.post('/resume/generate', payload);
      setGenerated(true);
      setGeneratedFile(res.data.filename ?? 'resume.pdf');
      setSuccessMsg('Resume generated successfully. You can download the latest PDF now.');
      showToast('Resume generated successfully!', 'success');
      setShowMissingModal(false);
    } catch (err) {
      if (err instanceof AxiosError && err.response) {
        const apiErr = err.response.data?.error;
        const missingApi = apiErr?.fields?.missing_fields;
        if (Array.isArray(missingApi) && missingApi.length > 0) {
          setMissingSections(missingApi);
          setShowMissingModal(true);
          setError('Your profile is incomplete. Fill the missing sections or skip to generate a shorter resume.');
        } else {
          setError(apiErr?.message ?? 'Failed to generate resume.');
        }
      } else {
        setError('Unable to connect to the server.');
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    setError('');

    try {
      const res = await api.get('/resume/download', {
        responseType: 'blob',
        params: { template: selectedTemplate },
      });

      const disposition = res.headers['content-disposition'];
      let filename = generatedFile || 'resume.pdf';
      if (disposition) {
        const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, '');
        }
      }

      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(readApiError(err, 'Failed to download resume. Please generate it first.'));
    } finally {
      setDownloading(false);
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSelectedFile(event.target.files?.[0] ?? null);
    setError('');
    setSuccessMsg('');
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a PDF or DOCX resume file first.');
      return;
    }

    setUploading(true);
    setError('');
    setSuccessMsg('');

    try {
      const formData = new FormData();
      formData.append('resume', selectedFile);
      await api.post('/resume/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSelectedFile(null);
      await fetchUploads();
      setSuccessMsg('Resume uploaded successfully.');
      showToast('Resume uploaded successfully!', 'success');
    } catch (err) {
      setError(readApiError(err, 'Resume upload failed.'));
    } finally {
      setUploading(false);
    }
  };

  const handleUploadedDownload = async (uploadId: number, originalName: string) => {
    setError('');

    try {
      const res = await api.get(`/resume/uploads/${uploadId}/download`, {
        responseType: 'blob',
      });
      const contentType = res.headers['content-type'];
      const blob = new Blob([res.data], {
        type: typeof contentType === 'string' ? contentType : 'application/octet-stream',
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = originalName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(readApiError(err, 'Failed to download uploaded resume.'));
    }
  };

  const selectedTemplateMeta = TEMPLATE_OPTIONS.find((item) => item.id === selectedTemplate) ?? TEMPLATE_OPTIONS[0];
  const skillsPreview = splitCommaList(profileForm.skills).slice(0, 8);
  const projectsPreview = splitNonEmptyLines(profileForm.projects).slice(0, 8);
  const certificatesPreview = splitNonEmptyLines(profileForm.certificates).slice(0, 6);
  const coursesPreview = splitNonEmptyLines(profileForm.courses).slice(0, 6);
  const languagesPreview = splitCommaList(profileForm.languages).slice(0, 6);
  const linkPreview = [profileForm.linkedin, profileForm.github, profileForm.portfolio].filter(Boolean);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Resume Builder</h1>
        <Link to="/student/dashboard" className="back-link">Back to Dashboard</Link>
      </div>

      {successMsg && <div className="alert alert-success">{successMsg}</div>}

      {error && (
        <div className="alert alert-error">
          {error}
          {missingSections.length > 0 && (
            <ul className="missing-list">
              {missingSections.map((section) => (
                <li key={section}>{section}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="page-section">
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
            <div>
              <h2 className="card-title">Choose a Template</h2>
              <p className="card-desc">Three no-photo resume demos. Click one to preview the layout, then generate the PDF with your data.</p>
            </div>
            {dreamJob ? (
              <p className="alert alert-success" style={{ margin: 0 }}>
                <strong>Tailored for:</strong> {dreamJob}
              </p>
            ) : null}
          </div>

          <div className="resume-template-layout" style={{ marginTop: '1rem' }}>
            <div className="template-grid">
              {TEMPLATE_OPTIONS.map((template) => (
                <button
                  key={template.id}
                  type="button"
                  onClick={() => setSelectedTemplate(template.id)}
                  className={`resume-template-card ${selectedTemplate === template.id ? 'selected' : ''}`}
                >
                  <div className={`template-preview ${template.previewClass}`}>
                    <div className="template-preview-header" style={{ borderColor: template.accent }}>
                      <div>
                        <div className="template-preview-name">Puneeth J</div>
                        <div className="template-preview-role">Full Stack Developer</div>
                      </div>
                      <div className="template-preview-dot" style={{ background: template.accent }} />
                    </div>
                    <div className="template-preview-section">
                      <div className="template-preview-section-title">Profile</div>
                      <div className="template-preview-line short" />
                      <div className="template-preview-line" />
                      <div className="template-preview-line tiny" />
                    </div>
                    <div className="template-preview-section">
                      <div className="template-preview-section-title">Projects</div>
                      <div className="template-preview-chip-row">
                        <span className="template-preview-chip">React</span>
                        <span className="template-preview-chip">Node</span>
                        <span className="template-preview-chip">SQL</span>
                      </div>
                    </div>
                  </div>
                  <div className="template-card-body">
                    <div className="template-label">{template.label}</div>
                    <p className="template-description">{template.description}</p>
                    <span className="template-action">{selectedTemplate === template.id ? 'Selected' : 'Preview & Select'}</span>
                  </div>
                </button>
              ))}
            </div>

            <div className={`resume-preview-paper ${selectedTemplateMeta.previewClass}`}>
              <div className="resume-preview-header">
                <div>
                  <div className="resume-preview-name">{user?.name ?? 'Your Name'}</div>
                  <div className="resume-preview-role">{profileForm.summary || 'Final-year Computer Science student'}</div>
                </div>
                <div className="resume-preview-accent" style={{ background: selectedTemplateMeta.accent }} />
              </div>

              <div className="resume-preview-contact">
                <span>{user?.email ?? 'your@email.com'}</span>
                <span>{profileData?.phone ?? 'Mobile number'}</span>
                {linkPreview.map((link) => (
                  <span key={link}>{link}</span>
                ))}
              </div>

              <div className="resume-preview-section-block">
                <div className="resume-preview-section-title">Profile</div>
                <p>{profileForm.summary || 'Short professional summary goes here.'}</p>
              </div>

              <div className="resume-preview-section-block">
                <div className="resume-preview-section-title">Education</div>
                <pre className="resume-preview-text">{profileForm.education || 'Add your education details.'}</pre>
              </div>

              <div className="resume-preview-section-block">
                <div className="resume-preview-section-title">Technical Skills</div>
                <div className="resume-chip-row">
                  {skillsPreview.length > 0 ? skillsPreview.map((skill) => <span key={skill} className="resume-chip">{skill}</span>) : <span className="resume-preview-muted">List your core skills here.</span>}
                </div>
              </div>

              <div className="resume-preview-section-block">
                <div className="resume-preview-section-title">Projects</div>
                {projectsPreview.length > 0 ? (
                  <ul className="resume-preview-list">
                    {projectsPreview.map((project) => <li key={project}>{project}</li>)}
                  </ul>
                ) : (
                  <p className="resume-preview-muted">Paste your project titles and bullet points here.</p>
                )}
              </div>

              <div className="resume-preview-section-block two-column">
                <div>
                  <div className="resume-preview-section-title">Certificates</div>
                  {certificatesPreview.length > 0 ? (
                    <ul className="resume-preview-list compact">
                      {certificatesPreview.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  ) : (
                    <p className="resume-preview-muted">Certificates will appear here.</p>
                  )}
                </div>
                <div>
                  <div className="resume-preview-section-title">Courses</div>
                  {coursesPreview.length > 0 ? (
                    <ul className="resume-preview-list compact">
                      {coursesPreview.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  ) : (
                    <p className="resume-preview-muted">Courses will appear here.</p>
                  )}
                </div>
              </div>

              <div className="resume-preview-section-block">
                <div className="resume-preview-section-title">Languages</div>
                <div className="resume-chip-row">
                  {languagesPreview.length > 0 ? languagesPreview.map((language) => <span key={language} className="resume-chip">{language}</span>) : <span className="resume-preview-muted">Add languages here.</span>}
                </div>
              </div>
            </div>
          </div>

          <div className="btn-row" style={{ marginTop: '1rem' }}>
            <button onClick={() => handleGenerate(false)} disabled={generating} className="btn btn-primary">
              {generating ? 'Generating...' : 'Generate PDF'}
            </button>
            <button onClick={handleDownload} disabled={downloading || (!generated && !generatedFile)} className="btn btn-success">
              {downloading ? 'Downloading...' : 'Download PDF'}
            </button>
          </div>

          {generatedFile && <p className="muted-text" style={{ marginTop: '0.75rem' }}>Latest generated file: {generatedFile}</p>}
        </div>
      </div>

      {showMissingModal && (
        <div className="modal">
          <div className="modal-content resume-modal">
            <h3>Missing Sections</h3>
            <p>
              I could not auto-fill these sections from your profile: <strong>{missingSections.join(', ')}</strong>.
              Fill them now, or skip to generate a shorter version.
            </p>

            <div className="resume-modal-grid">
              <label className="field">
                <span className="label">Profile Summary</span>
                <textarea className="input" rows={4} value={profileForm.summary} onChange={(e) => setProfileForm({ ...profileForm, summary: e.target.value })} placeholder="Write a short professional summary." />
              </label>

              <label className="field">
                <span className="label">Education</span>
                <textarea className="input" rows={4} value={profileForm.education} onChange={(e) => setProfileForm({ ...profileForm, education: e.target.value })} placeholder="Enter each education entry on a new line." />
              </label>

              <label className="field">
                <span className="label">Technical Skills</span>
                <textarea className="input" rows={4} value={profileForm.skills} onChange={(e) => setProfileForm({ ...profileForm, skills: e.target.value })} placeholder="Comma separated skills, e.g. Java, Python, React.js, SQL" />
              </label>

              <label className="field">
                <span className="label">Projects</span>
                <textarea className="input" rows={5} value={profileForm.projects} onChange={(e) => setProfileForm({ ...profileForm, projects: e.target.value })} placeholder="One project per block. Include bullets or short notes." />
              </label>

              <label className="field">
                <span className="label">Certificates</span>
                <textarea className="input" rows={4} value={profileForm.certificates} onChange={(e) => setProfileForm({ ...profileForm, certificates: e.target.value })} placeholder="One certificate per line." />
              </label>

              <label className="field">
                <span className="label">Courses</span>
                <textarea className="input" rows={4} value={profileForm.courses} onChange={(e) => setProfileForm({ ...profileForm, courses: e.target.value })} placeholder="One course per line." />
              </label>

              <label className="field">
                <span className="label">Languages</span>
                <input className="input" value={profileForm.languages} onChange={(e) => setProfileForm({ ...profileForm, languages: e.target.value })} placeholder="English, Kannada, Hindi" />
              </label>

              <label className="field">
                <span className="label">LinkedIn</span>
                <input className="input" value={profileForm.linkedin} onChange={(e) => setProfileForm({ ...profileForm, linkedin: e.target.value })} placeholder="linkedin.com/in/yourname" />
              </label>

              <label className="field">
                <span className="label">GitHub</span>
                <input className="input" value={profileForm.github} onChange={(e) => setProfileForm({ ...profileForm, github: e.target.value })} placeholder="github.com/yourname" />
              </label>

              <label className="field">
                <span className="label">Portfolio</span>
                <input className="input" value={profileForm.portfolio} onChange={(e) => setProfileForm({ ...profileForm, portfolio: e.target.value })} placeholder="portfolio / website link" />
              </label>
            </div>

            <div className="btn-row" style={{ marginTop: '1rem' }}>
              <button className="btn btn-primary" onClick={() => handleGenerate(true)}>
                Fill & Generate
              </button>
              <button className="btn btn-secondary" onClick={() => { setShowMissingModal(false); handleGenerate(false, true); }}>
                Skip and Generate
              </button>
              <button className="btn btn-outline" onClick={() => setShowMissingModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="page-section">
        <div className="card">
          <h2 className="card-title">Uploaded Resume</h2>
          <p className="card-desc">Store an existing PDF or DOCX resume alongside the generated version.</p>

          <div className="resume-upload-row">
            <input type="file" accept=".pdf,.docx" onChange={handleFileChange} className="input" />
            <button type="button" onClick={handleUpload} disabled={uploading} className="btn btn-secondary">
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>

          {selectedFile && <p className="muted-text">Selected file: {selectedFile.name}</p>}
        </div>
      </div>

      <div className="page-section">
        <h2 className="section-title">Upload History</h2>
        {uploads.length > 0 ? (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Type</th>
                  <th>Uploaded</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {uploads.map((upload) => (
                  <tr key={upload.id}>
                    <td>{upload.original_filename}</td>
                    <td>{upload.content_type}</td>
                    <td>{new Date(upload.uploaded_at).toLocaleString()}</td>
                    <td>
                      <button type="button" className="btn btn-sm btn-secondary" onClick={() => handleUploadedDownload(upload.id, upload.original_filename)}>
                        Download
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="empty-text">No uploaded resumes yet.</p>
        )}
      </div>
    </div>
  );
}
