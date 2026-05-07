import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AxiosError } from 'axios';

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

interface FieldErrors {
  name?: string;
  email?: string;
  phone?: string;
  password?: string;
  general?: string;
}

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);

  /**
   * Client-side validation. Returns true if all fields are valid.
   */
  const validate = (): boolean => {
    const newErrors: FieldErrors = {};

    if (!name.trim()) {
      newErrors.name = 'Name is required.';
    }

    if (!email.trim()) {
      newErrors.email = 'Email is required.';
    } else if (!EMAIL_REGEX.test(email)) {
      newErrors.email = 'Please enter a valid email address.';
    }

    if (!password) {
      newErrors.password = 'Password is required.';
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setErrors({});

    try {
      await register(name, email, phone, password);
      // Redirect to login with success message
      navigate('/login', {
        state: { message: 'Registration successful! Please sign in.' },
        replace: true,
      });
    } catch (err) {
      if (err instanceof AxiosError && err.response) {
        const data = err.response.data;
        const apiError = data?.error;

        if (apiError?.code === 'CONFLICT') {
          setErrors({ email: 'This email is already registered.' });
        } else if (apiError?.code === 'VALIDATION_ERROR') {
          // Map server field errors to our field error state
          const fieldErrors: FieldErrors = {};
          if (apiError.message) {
            fieldErrors.general = apiError.message;
          }
          const serverFields = apiError.fields ?? {};
          if (serverFields.email) {
            fieldErrors.email = Array.isArray(serverFields.email)
              ? serverFields.email[0]
              : serverFields.email;
          }
          if (serverFields.password) {
            fieldErrors.password = Array.isArray(serverFields.password)
              ? serverFields.password[0]
              : serverFields.password;
          }
          if (serverFields.name) {
            fieldErrors.name = Array.isArray(serverFields.name)
              ? serverFields.name[0]
              : serverFields.name;
          }
          setErrors(
            Object.keys(fieldErrors).length > 0
              ? fieldErrors
              : { general: apiError.message || 'Registration failed.' }
          );
        } else {
          setErrors({ general: 'Registration failed. Please try again.' });
        }
      } else {
        setErrors({
          general: 'Unable to connect to the server. Please try again later.',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-brand">Skill2Job</h1>
        <h2 className="auth-subtitle">Create Account</h2>

        {errors.general && (
          <div className="auth-error-banner">{errors.general}</div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="name" className="auth-label">
              Full Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={`auth-input${errors.name ? ' input-error' : ''}`}
              placeholder="John Doe"
              autoComplete="name"
            />
            {errors.name && (
              <span className="auth-field-error">{errors.name}</span>
            )}
          </div>

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

          <div className="auth-field">
            <label htmlFor="phone" className="auth-label">
              Phone Number{' '}
              <span className="auth-label-optional">(optional)</span>
            </label>
            <input
              id="phone"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className={`auth-input${errors.phone ? ' input-error' : ''}`}
              placeholder="+1 234 567 8900"
              autoComplete="tel"
            />
            {errors.phone && (
              <span className="auth-field-error">{errors.phone}</span>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="password" className="auth-label">
              Password
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

          <button
            type="submit"
            disabled={loading}
            className="auth-button"
          >
            {loading ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{' '}
          <Link to="/login">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
