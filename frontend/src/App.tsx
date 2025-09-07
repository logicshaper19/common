/**
 * Main App Component - Sets up routing and authentication
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, ProtectedRoute } from './contexts/AuthContext';
import { SectorProvider } from './contexts/SectorContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { ToastProvider } from './contexts/ToastContext';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import ConfirmationDemo from './pages/ConfirmationDemo';
import TransparencyDashboard from './pages/TransparencyDashboard';
import SupplierOnboardingDashboard from './pages/SupplierOnboardingDashboard';
import UserManagementDashboard from './components/user/UserManagementDashboard';
import { ProductCatalogManagement } from './components/admin/ProductCatalogManagement';
import { UserCompanyManagement } from './components/admin/UserCompanyManagement';
import { AdminDashboard } from './components/admin/AdminDashboard';

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <SectorProvider>
          <NotificationProvider>
          <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />

          {/* Protected routes */}
          <Route path="/app" element={<Layout />}>
            <Route index element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />

            {/* Main application routes using existing components */}
            <Route path="purchase-orders" element={
              <ProtectedRoute>
                <div className="text-center py-12">
                  <h2 className="text-2xl font-semibold text-neutral-900 mb-2">
                    Purchase Orders
                  </h2>
                  <p className="text-neutral-600">
                    Purchase order management is available in the admin dashboard.
                  </p>
                </div>
              </ProtectedRoute>
            } />

            <Route path="products" element={
              <ProtectedRoute>
                <ProductCatalogManagement />
              </ProtectedRoute>
            } />

            <Route path="companies" element={
              <ProtectedRoute requiredRole="admin">
                <UserCompanyManagement />
              </ProtectedRoute>
            } />

            <Route path="transparency" element={
              <ProtectedRoute>
                <TransparencyDashboard />
              </ProtectedRoute>
            } />

            <Route path="onboarding" element={
              <ProtectedRoute>
                <SupplierOnboardingDashboard />
              </ProtectedRoute>
            } />

            <Route path="users" element={
              <ProtectedRoute requiredRole="admin">
                <UserCompanyManagement />
              </ProtectedRoute>
            } />

            <Route path="settings" element={
              <ProtectedRoute>
                <UserManagementDashboard />
              </ProtectedRoute>
            } />

            <Route path="confirmation-demo" element={
              <ProtectedRoute>
                <ConfirmationDemo />
              </ProtectedRoute>
            } />

            {/* Catch all route */}
            <Route path="*" element={
              <div className="text-center py-12">
                <h2 className="text-2xl font-semibold text-neutral-900 mb-2">
                  Page Not Found
                </h2>
                <p className="text-neutral-600 mb-4">
                  The page you're looking for doesn't exist.
                </p>
                <button
                  onClick={() => window.location.href = '/'}
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  Go back to dashboard
                </button>
              </div>
            } />
          </Route>
        </Routes>
          </Router>
          </NotificationProvider>
        </SectorProvider>
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;
