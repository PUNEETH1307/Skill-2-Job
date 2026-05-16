import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AxiosError } from 'axios';
import api from '../services/api';

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

interface FieldErrors {
  email?: string;
  general?: string;
}

export default function ForgotPassword() {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const validate = (): boolean => {
    const newErrors: FieldErrors = {};

    if (!email.trim()) {
      newErrors.email = 'Email is required.';
    } else if (!EMAIL_REGEX.test(email)) {
      newErrors.email = 'Please enter a valid email address.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setErrors({});
    setSuccessMsg('');

    try {
      await api.post('/auth/forgot-password', { email });
      setSuccessMsg(
        'If an account with that email exists, a password reset link will be sent to your email.'
      );
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      if (err instanceof AxiosError && err.response) {
        const data = err.response.data;
        const apiError = data?.error;
        setErrors({ general: apiError?.message || 'Request failed.' });
      } else {
        setErrors({ general: 'Unable to connect to the server. Please try again later.' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-brand">Skill2Job</h1>
        <h2 className="auth-subtitle">Forgot Password</h2>

        {successMsg && (
          <div className="auth-success-banner">{successMsg}</div>
        )}

        {errors.general && (
          <div className="auth-error-banner">{errors.general}</div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="email" className="auth-label">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={`auth-input${errors.email ? ' input-error' : ''}`}
              placeholder="you@example.com"
              autoComplete="email"
            />
            {errors.email && (
              <span className="auth-field-error">{errors.email}</span>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="auth-button"
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        <p className="auth-footer">
          Remember your password?{' '}
          <Link to="/login">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
