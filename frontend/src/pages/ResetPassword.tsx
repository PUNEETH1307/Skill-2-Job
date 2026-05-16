import { useState, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AxiosError } from 'axios';
import api from '../services/api';

interface FieldErrors {
  token?: string;
  password?: string;
  general?: string;
}

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tokenFromUrl = searchParams.get('token') || '';

  const [token, setToken] = useState(tokenFromUrl);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const validate = (): boolean => {
    const newErrors: FieldErrors = {};

    if (!token.trim()) {
      newErrors.token = 'Reset token is required.';
    }

    if (!password) {
      newErrors.password = 'Password is required.';
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters.';
    }

    if (password !== confirmPassword) {
      newErrors.password = 'Passwords do not match.';
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
      await api.post('/auth/reset-password', { token, password });
      setSuccessMsg('Password has been reset successfully. Redirecting to login...');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      if (err instanceof AxiosError && err.response) {
        const data = err.response.data;
        const apiError = data?.error;
        setErrors({ general: apiError?.message || 'Password reset failed.' });
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
        <h2 className="auth-subtitle">Reset Password</h2>

        {successMsg && (
          <div className="auth-success-banner">{successMsg}</div>
        )}

        {errors.general && (
          <div className="auth-error-banner">{errors.general}</div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          {!tokenFromUrl && (
            <div className="auth-field">
              <label htmlFor="token" className="auth-label">
                Reset Token
              </label>
              <input
                id="token"
                type="text"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className={`auth-input${errors.token ? ' input-error' : ''}`}
                placeholder="Paste your reset token here"
              />
              {errors.token && (
                <span className="auth-field-error">{errors.token}</span>
              )}
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="password" className="auth-label">
              New Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={`auth-input${errors.password ? ' input-error' : ''}`}
              placeholder="At least 8 characters"
              autoComplete="new-password"
            />
            {errors.password && (
              <span className="auth-field-error">{errors.password}</span>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="confirmPassword" className="auth-label">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="auth-input"
              placeholder="Confirm your new password"
              autoComplete="new-password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="auth-button"
          >
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>
      </div>
    </div>
  );
}
