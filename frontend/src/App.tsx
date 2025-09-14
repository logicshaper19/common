/**
 * Main App Component - Sets up routing and authentication
 */
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, ProtectedRoute } from './contexts/AuthContext';
import { SectorProvider } from './contexts/SectorContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { ToastProvider } from './contexts/ToastContext';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import LandingPage from './pages/LandingPage';
import DashboardRouter from './components/dashboard/DashboardRouter';

import TransparencyDashboard from './pages/TransparencyDashboard';
import SupplierOnboardingDashboard from './pages/SupplierOnboardingDashboard';
import UserManagementDashboard from './components/user/UserManagementDashboard';
import { UserCompanyManagement } from './components/admin/user-company-management';
import { SystemMonitoring } from './components/admin/SystemMonitoring';
import { AuditLogViewer } from './components/admin/AuditLogViewer';
import { SupportTicketSystem } from './components/admin/SupportTicketSystem';
import TeamManagement from './pages/TeamManagement';
import PurchaseOrderDetailPage from './pages/PurchaseOrderDetailPage';
import IncomingPurchaseOrdersPage from './pages/IncomingPurchaseOrdersPage';
import OutgoingPurchaseOrdersPage from './pages/OutgoingPurchaseOrdersPage';
import ProductsRouter from './components/products/ProductsRouter';
import InventoryRouter from './components/inventory/InventoryRouter';
import OriginatorRouter from './components/origin/OriginatorRouter';
import OriginatorFeaturesDemo from './pages/OriginatorFeaturesDemo';
import HarvestManagement from './pages/HarvestManagement';

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

          {/* V2 Dashboard routes - removed, now handled within main layout */}

          {/* Protected routes with Layout */}
          <Route path="/" element={<Layout />}>
            {/* Dashboard - default route when authenticated */}
            <Route path="dashboard" element={
              <ProtectedRoute>
                <DashboardRouter />
              </ProtectedRoute>
            } />

            {/* Main application routes */}
            <Route path="purchase-orders" element={
              <ProtectedRoute>
                <IncomingPurchaseOrdersPage />
              </ProtectedRoute>
            } />

            <Route path="purchase-orders/:id" element={
              <ProtectedRoute>
                <PurchaseOrderDetailPage />
              </ProtectedRoute>
            } />

            <Route path="purchase-orders/incoming" element={
              <ProtectedRoute>
                <IncomingPurchaseOrdersPage />
              </ProtectedRoute>
            } />

            <Route path="purchase-orders/outgoing" element={
              <ProtectedRoute>
                <OutgoingPurchaseOrdersPage />
              </ProtectedRoute>
            } />

            <Route path="products" element={
              <ProtectedRoute>
                <ProductsRouter />
              </ProtectedRoute>
            } />

            <Route path="inventory" element={
              <ProtectedRoute>
                <InventoryRouter />
              </ProtectedRoute>
            } />

            <Route path="inventory/batches" element={
              <ProtectedRoute>
                <InventoryRouter view="batches" />
              </ProtectedRoute>
            } />

            <Route path="inventory/analytics" element={
              <ProtectedRoute>
                <InventoryRouter view="analytics" />
              </ProtectedRoute>
            } />

            <Route path="originator" element={
              <ProtectedRoute>
                <OriginatorRouter />
              </ProtectedRoute>
            } />

            <Route path="originator/farms" element={
              <ProtectedRoute>
                <OriginatorRouter view="farms" />
              </ProtectedRoute>
            } />

            <Route path="originator/certifications" element={
              <ProtectedRoute>
                <OriginatorRouter view="certifications" />
              </ProtectedRoute>
            } />


            <Route path="originator/demo" element={
              <ProtectedRoute>
                <OriginatorFeaturesDemo />
              </ProtectedRoute>
            } />

            <Route path="harvest" element={
              <ProtectedRoute>
                <HarvestManagement />
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

            <Route path="team" element={
              <ProtectedRoute>
                <TeamManagement />
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

            {/* Admin-specific routes */}
            <Route path="admin/system" element={
              <ProtectedRoute requiredRole="admin">
                <SystemMonitoring />
              </ProtectedRoute>
            } />

            <Route path="admin/audit" element={
              <ProtectedRoute requiredRole="admin">
                <AuditLogViewer />
              </ProtectedRoute>
            } />

            <Route path="admin/support" element={
              <ProtectedRoute requiredRole="admin">
                <SupportTicketSystem />
              </ProtectedRoute>
            } />

            {/* Redirect root to dashboard when authenticated */}
            <Route index element={
              <ProtectedRoute>
                <Navigate to="/dashboard" replace />
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
                  onClick={() => window.location.href = '/dashboard'}
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
