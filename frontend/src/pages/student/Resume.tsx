import { useEffect, useState, type ChangeEvent } from 'react';
import { Link } from 'react-router-dom';
import { AxiosError } from 'axios';
import api from '../../services/api';
import { useToast } from '../../components/Toast';

interface ResumeUploadEntry {
  id: number;
  original_filename: string;
  content_type: string;
  uploaded_at: string;
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
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [dreamJob, setDreamJob] = useState<string | null>(null);

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
    } catch {
      setDreamJob(null);
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

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    setSuccessMsg('');
    setMissingFields([]);

    try {
      const res = await api.post('/resume/generate');
      setGenerated(true);
      setGeneratedFile(res.data.filename ?? 'resume.pdf');
      setSuccessMsg('Resume generated successfully. You can download the latest PDF now.');
      showToast('Resume generated successfully!', 'success');
    } catch (err) {
      if (err instanceof AxiosError && err.response) {
        const apiErr = err.response.data?.error;
        const missing = apiErr?.fields?.missing_fields;
        if (Array.isArray(missing) && missing.length > 0) {
          setMissingFields(missing);
          setError('Your profile is incomplete. Please fill in the missing fields below.');
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

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Resume</h1>
        <Link to="/student/dashboard" className="back-link">Back to Dashboard</Link>
      </div>

      {successMsg && <div className="alert alert-success">{successMsg}</div>}

      {error && (
        <div className="alert alert-error">
          {error}
          {missingFields.length > 0 && (
            <ul className="missing-list">
              {missingFields.map((field) => (
                <li key={field}>{field}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="page-section">
        <div className="card">
          <h2 className="card-title">Generated Resume</h2>
          <p className="card-desc">
            Build a professional PDF from your profile, academic details, skills,
            projects, and certifications.
          </p>

          {dreamJob ? (
            <p className="alert alert-success" style={{ marginBottom: '0.75rem' }}>
              <strong>AI-Enhanced Resume</strong> — Your resume will be tailored for: {dreamJob}
            </p>
          ) : (
            <p className="muted-text" style={{ marginBottom: '0.75rem' }}>
              💡 Set your <Link to="/student/profile" className="back-link">dream job in your profile</Link> to get an AI-tailored resume.
            </p>
          )}

          {generatedFile && (
            <p className="muted-text">Latest generated file: {generatedFile}</p>
          )}

          <div className="btn-row">
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="btn btn-primary"
            >
              {generating ? 'Generating...' : 'Generate PDF'}
            </button>

            <button
              onClick={handleDownload}
              disabled={downloading || (!generated && !generatedFile)}
              className="btn btn-success"
            >
              {downloading ? 'Downloading...' : 'Download PDF'}
            </button>
          </div>

          {missingFields.length > 0 && (
            <p className="mt-1" style={{ fontSize: '0.9rem' }}>
              <Link to="/student/profile" className="back-link">
                Complete profile details
              </Link>
            </p>
          )}
        </div>
      </div>

      <div className="page-section">
        <div className="card">
          <h2 className="card-title">Uploaded Resume</h2>
          <p className="card-desc">
            Store an existing PDF or DOCX resume alongside the generated version.
          </p>

          <div className="resume-upload-row">
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="input"
            />
            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading}
              className="btn btn-secondary"
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>

          {selectedFile && (
            <p className="muted-text">Selected file: {selectedFile.name}</p>
          )}
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
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleUploadedDownload(upload.id, upload.original_filename)}
                      >
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
