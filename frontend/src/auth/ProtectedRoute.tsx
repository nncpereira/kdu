import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./useAuth";
import { Spinner } from "@/components/Spinner";

export function ProtectedRoute({ roles }: { roles?: string[] }) {
  const { isAuthenticated, isLoading, profile } = useAuth();
  const location = useLocation();

  if (isLoading) return <Spinner />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  // Members are routed to the portal, never to staff pages.
  if (profile?.role === "MEMBER") {
    return <Navigate to="/portal/dashboard" replace />;
  }

  if (roles && profile && !roles.includes(profile.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  if (
    profile?.must_change_password &&
    location.pathname !== "/profile"
  ) {
    return <Navigate to="/profile" replace />;
  }

  return <Outlet />;
}