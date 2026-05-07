import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import StudentDashboard from './pages/student/Dashboard';
import StudentProfile from './pages/student/Profile';
import SkillAnalysis from './pages/student/SkillAnalysis';
import JobRecommendations from './pages/student/JobRecommendations';
import SkillGap from './pages/student/SkillGap';
import Resume from './pages/student/Resume';
import AdminDashboard from './pages/admin/Dashboard';
import Companies from './pages/admin/Companies';
import JobRoles from './pages/admin/JobRoles';
import Shortlist from './pages/admin/Shortlist';
import Analytics from './pages/admin/Analytics';
import UserManagement from './pages/admin/UserManagement';
import SkillTaxonomy from './pages/admin/SkillTaxonomy';
import Courses from './pages/admin/Courses';

/**
 * Redirects the root path based on authentication state and role.
 */
function RootRedirect() {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role === 'placement_officer' || user.role === 'admin') {
    return <Navigate to="/admin/dashboard" replace />;
  }

  return <Navigate to="/student/dashboard" replace />;
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Root redirect */}
        <Route path="/" element={<RootRedirect />} />

        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Student protected routes */}
        <Route element={<ProtectedRoute requiredRole="student" />}>
          <Route path="/student/dashboard" element={<StudentDashboard />} />
          <Route path="/student/profile" element={<StudentProfile />} />
          <Route path="/student/skills" element={<SkillAnalysis />} />
          <Route path="/student/jobs" element={<JobRecommendations />} />
          <Route path="/student/jobs/:id/gap" element={<SkillGap />} />
          <Route path="/student/resume" element={<Resume />} />
        </Route>

        {/* Admin / Placement Officer protected routes */}
        <Route element={<ProtectedRoute requiredRole="placement_officer" />}>
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/admin/companies" element={<Companies />} />
          <Route path="/admin/jobs" element={<JobRoles />} />
          <Route path="/admin/shortlist" element={<Shortlist />} />
          <Route path="/admin/analytics" element={<Analytics />} />
          <Route path="/admin/courses" element={<Courses />} />
        </Route>

        {/* Admin-only routes */}
        <Route element={<ProtectedRoute requiredRole="admin" />}>
          <Route path="/admin/users" element={<UserManagement />} />
          <Route path="/admin/skills" element={<SkillTaxonomy />} />
        </Route>

        {/* Catch-all: redirect to root */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
