import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

export default function Landing() {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  // If already logged in, redirect to appropriate dashboard
  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === 'admin') {
        navigate('/admin/dashboard', { replace: true });
      } else if (user.role === 'placement_officer') {
        navigate('/admin/dashboard', { replace: true });
      } else {
        navigate('/student/dashboard', { replace: true });
      }
    }
  }, [isAuthenticated, user, navigate]);

  return (
    <div className="landing-container">
      <div className="landing-bg-shapes">
        <div className="landing-shape landing-shape-1" />
        <div className="landing-shape landing-shape-2" />
        <div className="landing-shape landing-shape-3" />
      </div>

      <div className="landing-content">
        <div className="landing-header">
          <h1 className="landing-brand">Skill2Job</h1>
          <p className="landing-tagline">
            AI-Driven Placement Coordination & Skill Mapping System
          </p>
        </div>

        <div className="landing-cards">
          {/* Student Login */}
          <Link to="/login?role=student" className="landing-card landing-card-student">
            <div className="landing-card-icon">🎓</div>
            <h2 className="landing-card-title">Student Login</h2>
            <p className="landing-card-desc">
              Access your profile, view job recommendations, generate AI-powered resumes, and track skill progress.
            </p>
            <span className="landing-card-btn">Login as Student →</span>
          </Link>

          {/* Admin Login */}
          <Link to="/login?role=admin" className="landing-card landing-card-admin">
            <div className="landing-card-icon">🛡️</div>
            <h2 className="landing-card-title">Admin Login</h2>
            <p className="landing-card-desc">
              Manage users, skill taxonomy, course recommendations, and system configuration.
            </p>
            <span className="landing-card-btn">Login as Admin →</span>
          </Link>

          {/* Placement Cell Login */}
          <Link to="/login?role=placement_officer" className="landing-card landing-card-officer">
            <div className="landing-card-icon">🏢</div>
            <h2 className="landing-card-title">Placement Cell Login</h2>
            <p className="landing-card-desc">
              Manage companies, job openings, shortlist candidates, and view placement analytics.
            </p>
            <span className="landing-card-btn">Login as Placement Officer →</span>
          </Link>
        </div>

        <div className="landing-footer">
          <p>Don't have an account? <Link to="/register">Register as Student</Link></p>
        </div>
      </div>
    </div>
  );
}
