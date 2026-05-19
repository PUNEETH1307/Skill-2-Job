import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import { AxiosError } from 'axios';

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

interface FieldErrors {
  name?: string;
  email?: string;
  password?: string;
  general?: string;
}

export default function Register() {
  const { register } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);

  const validate = (): boolean => {
    const e: FieldErrors = {};
    if (!name.trim()) e.name = 'Name is required.';
    if (!email.trim()) e.email = 'Email is required.';
    else if (!EMAIL_REGEX.test(email)) e.email = 'Enter a valid email address.';
    if (!password) e.password = 'Password is required.';
    else if (password.length < 8) e.password = 'Password must be at least 8 characters.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});
    try {
      await register(name, email, phone, password);
      showToast('Account created! Please sign in.', 'success');
      navigate('/login', {
        state: { message: 'Registration successful! Please sign in.' },
        replace: true,
      });
    } catch (err) {
      if (err instanceof AxiosError && err.response) {
        const apiError = err.response.data?.error;
        if (apiError?.code === 'CONFLICT') {
          setErrors({ email: 'This email is already registered.' });
        } else if (apiError?.code === 'VALIDATION_ERROR') {
          const sf = apiError.fields ?? {};
          setErrors({
            general: !sf.email && !sf.password && !sf.name ? apiError.message : undefined,
            email: sf.email,
            password: sf.password,
            name: sf.name,
          });
        } else {
          setErrors({ general: 'Registration failed. Please try again.' });
        }
      } else {
        setErrors({ general: 'Unable to connect to the server.' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-brand">Skill2Job</h1>
        <h2 className="auth-subtitle">Create Student Account</h2>

        {errors.general && (
          <div className="auth-error-banner">{errors.general}</div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="reg-name" className="auth-label">Full Name</label>
            <input
              id="reg-name" type="text" value={name}
              onChange={e => setName(e.target.value)}
              className={`auth-input${errors.name ? ' input-error' : ''}`}
              placeholder="John Doe" autoComplete="name" disabled={loading}
            />
            {errors.name && <span className="auth-field-error">{errors.name}</span>}
          </div>

          <div className="auth-field">
            <label htmlFor="reg-email" className="auth-label">Email</label>
            <input
              id="reg-email" type="email" value={email}
              onChange={e => setEmail(e.target.value)}
              className={`auth-input${errors.email ? ' input-error' : ''}`}
              placeholder="you@example.com" autoComplete="email" disabled={loading}
            />
            {errors.email && <span className="auth-field-error">{errors.email}</span>}
          </div>

          <div className="auth-field">
            <label htmlFor="reg-phone" className="auth-label">
              Phone <span className="auth-label-optional">(optional)</span>
            </label>
            <input
              id="reg-phone" type="tel" value={phone}
              onChange={e => setPhone(e.target.value)}
              className="auth-input" placeholder="+91 98765 43210"
              autoComplete="tel" disabled={loading}
            />
          </div>

          <div className="auth-field">
            <label htmlFor="reg-password" className="auth-label">Password</label>
            <input
              id="reg-password" type="password" value={password}
              onChange={e => setPassword(e.target.value)}
              className={`auth-input${errors.password ? ' input-error' : ''}`}
              placeholder="At least 8 characters" autoComplete="new-password" disabled={loading}
            />
            {errors.password && <span className="auth-field-error">{errors.password}</span>}
          </div>

          <button type="submit" disabled={loading} className="auth-button">
            {loading ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign In</Link>
        </p>

        {/* Staff info box — informational only, no form */}
        <div style={{
          marginTop: '1.5rem',
          padding: '1rem',
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '10px',
          fontSize: '0.82rem',
          color: '#64748b',
          lineHeight: 1.6,
        }}>
          <strong style={{ color: '#1e293b' }}>🏢 Staff / Admin?</strong><br />
          Admin and Placement Officer accounts are created by the system administrator.<br />
          Contact your admin or{' '}
          <Link to="/login" style={{ color: 'var(--primary)', fontWeight: 600 }}>
            sign in
          </Link>{' '}
          if you already have an account.
        </div>
      </div>
    </div>
  );
}
