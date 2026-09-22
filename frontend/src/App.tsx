import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";

import { queryClient } from "@/lib/queryClient";
import { AuthProvider } from "@/auth/AuthContext";
import { ProtectedRoute } from "@/auth/ProtectedRoute";
import { MemberRoute } from "@/auth/MemberRoute";
import { AppLayout } from "@/layouts/AppLayout";
import { PortalLayout } from "@/layouts/PortalLayout";

import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { MembersPage } from "@/pages/MembersPage";
import { MemberDetailPage } from "@/pages/MemberDetailPage";
import { SavingsPage } from "@/pages/SavingsPage";
import { LoansPage } from "@/pages/LoansPage";
import { LoanDetailPage } from "@/pages/LoanDetailPage";
import { ExpensesPage } from "@/pages/ExpensesPage";
import { ShuPage } from "@/pages/ShuPage";
import { ShuDetailPage } from "@/pages/ShuDetailPage";
import { PipelinePage } from "@/pages/PipelinePage";
import { ReportsPage } from "@/pages/ReportsPage";
import { GovernancePage } from "@/pages/GovernancePage";
import { UsersPage } from "@/pages/UsersPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { NotFoundPage } from "@/pages/NotFoundPage";

import { PortalDashboardPage } from "@/pages/portal/PortalDashboardPage";
import { PortalSavingsPage } from "@/pages/portal/PortalSavingsPage";
import { PortalLoansPage } from "@/pages/portal/PortalLoansPage";
import { PortalStatementPage } from "@/pages/portal/PortalStatementPage";
import { PortalProfilePage } from "@/pages/portal/PortalProfilePage";
import { AuditPage } from "@/pages/AuditPage";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Toaster position="top-right" richColors closeButton duration={4000} />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<LoginPage />} />

            {/* Staff app */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />

                <Route path="/members" element={<MembersPage />} />
                <Route path="/members/:id" element={<MemberDetailPage />} />

                <Route path="/savings" element={<SavingsPage />} />

                <Route path="/loans" element={<LoansPage />} />
                <Route path="/loans/:id" element={<LoanDetailPage />} />

                <Route path="/expenses" element={<ExpensesPage />} />

                <Route path="/shu" element={<ShuPage />} />
                <Route path="/shu/:fyId" element={<ShuDetailPage />} />

                <Route path="/pipeline" element={<PipelinePage />} />
                <Route path="/reports" element={<ReportsPage />} />

                <Route
                  path="/governance"
                  element={
                    <ProtectedRoute roles={["SUPERADMIN", "MAKER"]} />
                  }
                >
                  <Route index element={<GovernancePage />} />
                </Route>

                <Route
                  path="/users"
                  element={<ProtectedRoute roles={["SUPERADMIN"]} />}
                >
                  <Route index element={<UsersPage />} />
                </Route>

                <Route
                  path="/audit"
                  element={<ProtectedRoute roles={["SUPERADMIN", "BOARD", "AUDITOR"]} />}
                >
                  <Route index element={<AuditPage />} />
                </Route>

                <Route path="/profile" element={<ProfilePage />} />
              </Route>
            </Route>

            {/* Member portal */}
            <Route element={<MemberRoute />}>
              <Route element={<PortalLayout />}>
                <Route
                  path="/portal"
                  element={<Navigate to="/portal/dashboard" replace />}
                />
                <Route
                  path="/portal/dashboard"
                  element={<PortalDashboardPage />}
                />
                <Route
                  path="/portal/savings"
                  element={<PortalSavingsPage />}
                />
                <Route path="/portal/loans" element={<PortalLoansPage />} />
                <Route
                  path="/portal/statement"
                  element={<PortalStatementPage />}
                />
                <Route
                  path="/portal/profile"
                  element={<PortalProfilePage />}
                />
              </Route>
            </Route>

            {/* Catch-all — MUST be last */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}