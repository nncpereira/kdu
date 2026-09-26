import { Link, Outlet, useLocation } from "react-router-dom";
import clsx from "clsx";
import { toast } from "sonner";
import { useAuth } from "@/auth/useAuth";
import { Logo } from "@/components/Logo";
import { NotificationBell } from "@/components/NotificationBell";
import { grantAdminSession } from "@/api/users";

const NAV: { to: string; label: string; roles?: string | string[] }[] = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/members", label: "Members" },
  { to: "/savings", label: "Savings" },
  { to: "/loans", label: "Loans" },
  { to: "/expenses", label: "Expenses" },
  { to: "/shu", label: "SHU" },
  { to: "/pipeline", label: "Pipeline" },
  { to: "/reports", label: "Reports" },
  { to: "/audit", label: "Audit Log", roles: ["SUPERADMIN", "BOARD", "AUDITOR"] },
  { to: "/governance", label: "Governance" },
  { to: "/users", label: "Users", roles: "SUPERADMIN" },
];

export function AppLayout() {
  const { profile, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-60 bg-brand-700 text-white flex flex-col">
        {/* Letterhead with logo */}
        <div className="px-4 py-4 border-b border-brand-600">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-full bg-white flex items-center justify-center shrink-0">
              <Logo size={38} />
            </div>
            <div className="min-w-0 flex-1">
              <h1 className="text-base font-bold leading-tight tracking-tight">
                KDU
              </h1>
              <p className="text-[10px] text-brand-100 uppercase tracking-widest leading-tight">
                Cooperative Core
              </p>
            </div>
            {/* Show bell only for roles that have actionable notifications. */}
            {profile?.role &&
              ["MAKER", "CHECKER", "CERTIFIER", "SUPERADMIN"].includes(
                profile.role
              ) && <NotificationBell />}
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 overflow-y-auto">
          {NAV.filter(
            (item) =>
              !item.roles ||
              (Array.isArray(item.roles)
                ? item.roles.includes(profile?.role ?? "")
                : profile?.role === item.roles)
          ).map(
            (item) => (
              <Link
                key={item.to}
                to={item.to}
                className={clsx(
                  "block px-5 py-2.5 text-sm transition-colors",
                  location.pathname === item.to
                    ? "bg-brand-600 font-semibold"
                    : "hover:bg-brand-600"
                )}
              >
                {item.label}
              </Link>
            )
          )}
        </nav>

        {/* User footer */}
        <div className="border-t border-brand-600">
          <Link
            to="/profile"
            className={clsx(
              "block px-5 py-4 transition-colors",
              location.pathname === "/profile"
                ? "bg-brand-600"
                : "hover:bg-brand-600"
            )}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xs font-bold shrink-0">
                {(profile?.username ?? "?").charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium truncate">
                  {profile?.first_name || profile?.username}
                </p>
                <p className="text-[10px] text-brand-100 uppercase tracking-wider truncate">
                  {profile?.role}
                </p>
              </div>
            </div>
          </Link>
          <button
            onClick={async () => { await logout(); }}
            className="w-full text-left px-5 py-2.5 text-xs text-brand-100 hover:bg-brand-600 hover:text-white transition-colors"
          >
            Log out
          </button>
          {profile?.role === "SUPERADMIN" && (
            <button
              onClick={async () => {
                try {
                  await grantAdminSession();
                  window.open("/admin/", "_blank", "noopener,noreferrer");
                } catch {
                  toast.error("Could not open Django admin.");
                }
              }}
              className="block w-full text-left px-5 pb-2.5 text-[10px] text-brand-300 hover:text-brand-100 transition-colors"
            >
              Django Admin ↗
            </button>
          )}
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
