import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

interface Drive {
  id: number; company_name: string; job_title: string; title: string; description: string;
  job_description: string; package_lpa: number | null; location: string; eligibility_criteria: string;
  minimum_cgpa: number; allowed_graduation_years: number[]; no_backlogs_required: boolean;
  registration_deadline: string | null; drive_date: string; drive_time: string; blocked: boolean;
  eligible: boolean; eligibility_reasons: string[]; deadline_passed: boolean; registration: { status: string; attended: boolean } | null;
}

export default function Drives() {
  const [drives, setDrives] = useState<Drive[]>([]);
  const [blocks, setBlocks] = useState(0);
  const [codes, setCodes] = useState<Record<number, string>>({});
  const [error, setError] = useState('');

  const load = async () => {
    try { const response = await api.get('/placements/drives'); setDrives(response.data.drives ?? []); setBlocks(response.data.missed_drive_blocks ?? 0); }
    catch (err: any) { setError(err.response?.data?.error?.message ?? 'Unable to load drives.'); }
  };
  useEffect(() => { void load(); }, []);

  const register = async (id: number) => {
    try { await api.post(`/placements/drives/${id}/register`); await load(); }
    catch (err: any) { setError(err.response?.data?.error?.message ?? 'Registration failed.'); }
  };
  const attend = async (id: number) => {
    try { await api.post(`/placements/drives/${id}/attend`, { attendance_code: codes[id] ?? '' }); await load(); }
    catch (err: any) { setError(err.response?.data?.error?.message ?? 'Attendance could not be marked.'); }
  };

  return <div className="page-container-wide">
    <div className="page-header"><div><h1 className="page-title">Placement Drives</h1><p className="text-muted">Register before the deadline and enter the code on the drive day.</p></div><Link to="/student/dashboard" className="back-link">Back to Dashboard</Link></div>
    {blocks > 0 && <div className="alert alert-error"><strong>Registration blocked:</strong> you have {blocks} drive(s) remaining because you missed an eligible registration. This block does not apply after you are placed.</div>}
    {error && <div className="alert alert-error">{error}</div>}
    <div className="job-list">{drives.map((drive) => <article className="job-card" key={drive.id}>
      <div className="job-card-header"><div><h2 className="job-title">{drive.title}</h2><p className="job-company">{drive.company_name} · {drive.job_title}</p></div><span className="score-badge">{drive.drive_date}</span></div>
      <p>{drive.description}</p><p><strong>Location:</strong> {drive.location || 'To be announced'} · <strong>Time:</strong> {drive.drive_time || 'To be announced'} · <strong>Package:</strong> {drive.package_lpa ? `₹${drive.package_lpa} LPA` : 'As per company'}</p>
      <p><strong>Eligibility:</strong> CGPA {drive.minimum_cgpa}+{drive.no_backlogs_required ? ', no backlogs' : ''}{drive.allowed_graduation_years.length ? `, graduating ${drive.allowed_graduation_years.join(', ')}` : ''}. {drive.eligibility_criteria}</p>
      {!drive.registration && <button className="btn btn-primary" disabled={drive.blocked || !drive.eligible || drive.deadline_passed} onClick={() => void register(drive.id)}>{!drive.eligible ? 'Not Eligible' : drive.deadline_passed ? 'Registration Closed' : drive.blocked ? 'Registration Blocked' : 'Register for Drive'}</button>}
      {!drive.eligible && <div className="alert alert-warning"><strong>Why you are not eligible:</strong><ul>{drive.eligibility_reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></div>}
      {drive.deadline_passed && !drive.registration && <div className="alert alert-warning">Registration closed because the deadline has passed.</div>}
      {drive.registration && <div className="alert alert-success">Status: {drive.registration.status}{drive.registration.attended ? ' · Attendance verified' : ''}</div>}
      {drive.registration && !drive.registration.attended && <div className="form-grid"><input className="input" placeholder="Enter attendance code" value={codes[drive.id] ?? ''} onChange={(event) => setCodes({ ...codes, [drive.id]: event.target.value })} /><button className="btn btn-success" onClick={() => void attend(drive.id)}>Mark Attendance</button></div>}
    </article>)}{!drives.length && <p className="empty-text">No active placement drives.</p>}</div>
  </div>;
}
