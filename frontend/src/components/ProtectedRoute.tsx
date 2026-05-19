import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  requiredRole?: 'student' | 'placement_officer' | 'admin';
}

const ROLE_LEVEL: Record<string, number> = {
  student: 0,
  placement_officer: 1,
  admin: 2,
};

export default function ProtectedRoute({ requiredRole }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  // Wait for session restore before making any redirect decision
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: '#f8fafc',
        fontSize: '16px',
        color: '#64748b',
      }}>
        Loading...
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {
    const userLevel = ROLE_LEVEL[user.role] ?? -1;
    const requiredLevel = ROLE_LEVEL[requiredRole] ?? 0;
    if (userLevel < requiredLevel) {
      // Redirect to their own dashboard instead of landing
      const home = user.role === 'student' ? '/student/dashboard' : '/admin/dashboard';
      return <Navigate to={home} replace />;
    }
  }

  return <Outlet />;
}
