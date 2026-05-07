import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import { AxiosError } from 'axios';

export default function Resume() {
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [missingFields, setMissingFields] = useState<string[]>([]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    setSuccessMsg('');
    setMissingFields([]);

    try {
      await api.post('/resume/generate');
      setGenerated(true);
      setSuccessMsg('Resume generated successfully! You can now download it.');
    } catch (err) {
      if (err instanceof AxiosError && err.response) {
        const data = err.response.data;
        const apiErr = data?.error;
        if (apiErr?.fields?.missing_fields) {
          setMissingFields(
            Array.isArray(apiErr.fields.missing_fields)
              ? apiErr.fields.missing_fields
              : [apiErr.fields.missing_fields]
          );
          setError('Your profile is incomplete. Please fill in the missing fields:');
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

      // Extract filename from Content-Disposition header if available
      const disposition = res.headers['content-disposition'];
      let filename = 'resume.pdf';
      if (disposition) {
        const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, '');
        }
      }

      // Create blob URL and trigger download
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
      if (err instanceof AxiosError && err.response) {
        setError('Failed to download resume. Please generate it first.');
      } else {
        setError('Unable to connect to the server.');
      }
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Resume</h1>
        <Link to="/student/dashboard" className="back-link">Back to Dashboard</Link>
      </div>

      <div className="card">
        <h2 className="card-title">Generate Your Resume</h2>
        <p className="card-desc">
          Generate a professional PDF resume from your profile data. Make sure your
          profile is complete before generating.
        </p>

        {successMsg && <div className="alert alert-success">{successMsg}</div>}

        {error && (
          <div className="alert alert-error">
            {error}
            {missingFields.length > 0 && (
              <ul className="missing-list">
                {missingFields.map((field, idx) => (
                  <li key={idx}>{field}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        <div className="btn-row">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="btn btn-primary"
          >
            {generating ? 'Generating...' : 'Generate Resume'}
          </button>

          <button
            onClick={handleDownload}
            disabled={downloading || (!generated && !successMsg)}
            className="btn btn-success"
          >
            {downloading ? 'Downloading...' : 'Download PDF'}
          </button>
        </div>

        {missingFields.length > 0 && (
          <p className="mt-1" style={{ fontSize: '0.9rem' }}>
            <Link to="/student/profile" className="back-link">
              Go to Profile to complete your details &rarr;
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
