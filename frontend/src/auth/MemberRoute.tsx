import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./useAuth";
import { Spinner } from "@/components/Spinner";

export function MemberRoute() {
  const { isAuthenticated, isLoading, profile } = useAuth();
  const location = useLocation();

  if (isLoading) return <Spinner />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  // Staff are routed to their dashboard, never into the portal.
  if (profile?.role !== "MEMBER") {
    return <Navigate to="/dashboard" replace />;
  }

  // Forced password change inside the portal.
  if (
    profile?.must_change_password &&
    location.pathname !== "/portal/profile"
  ) {
    return <Navigate to="/portal/profile" replace />;
  }

  return <Outlet />;
}