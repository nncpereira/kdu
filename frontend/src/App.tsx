import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/auth/AuthContext";
import { ProtectedRoute } from "@/auth/ProtectedRoute";
import { AppLayout } from "@/layouts/AppLayout";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { MembersPage } from "@/pages/MembersPage";
import { MemberDetailPage } from "@/pages/MemberDetailPage";
import { SavingsPage } from "@/pages/SavingsPage";
import { LoansPage } from "@/pages/LoansPage";
import { LoanDetailPage } from "@/pages/LoanDetailPage";
import { ExpensesPage } from "@/pages/ExpensesPage";
import { ShuPage } from "@/pages/ShuPage";
import { PipelinePage } from "@/pages/PipelinePage";
import { ReportsPage } from "@/pages/ReportsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { queryClient } from "@/lib/queryClient";
import { ShuDetailPage } from "@/pages/ShuDetailPage";
import { GovernancePage } from "@/pages/GovernancePage";
import { UsersPage } from "@/pages/UsersPage";
import { ProfilePage } from "@/pages/ProfilePage";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
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
                <Route path="/governance" element={<GovernancePage />} />
                <Route path="/users" element={<UsersPage />} />
                <Route path="/profile" element={<ProfilePage />} />
              </Route>
            </Route>
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}