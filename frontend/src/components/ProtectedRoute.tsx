import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  requiredRole?: 'student' | 'placement_officer' | 'admin';
}

/**
 * Role hierarchy: admin > placement_officer > student.
 * A higher-privilege role can access lower-privilege routes.
 */
const ROLE_LEVEL: Record<string, number> = {
  student: 0,
  placement_officer: 1,
  admin: 2,
};

export default function ProtectedRoute({ requiredRole }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {
    const userLevel = ROLE_LEVEL[user.role] ?? -1;
    const requiredLevel = ROLE_LEVEL[requiredRole] ?? 0;
    if (userLevel < requiredLevel) {
      return <Navigate to="/" replace />;
    }
  }

  return <Outlet />;
}
