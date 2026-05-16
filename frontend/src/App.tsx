import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
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

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Landing page with 3 role options */}
        <Route path="/" element={<Landing />} />

        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

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

        {/* Catch-all: redirect to landing */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
