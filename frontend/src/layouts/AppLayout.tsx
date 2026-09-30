import { useState } from "react";
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
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const showBell =
    profile?.role &&
    ["MAKER", "CHECKER", "CERTIFIER", "SUPERADMIN"].includes(profile.role);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 inset-x-0 h-14 bg-brand-700 text-white flex items-center justify-between px-4 z-30">
        <button
          onClick={() => setMobileNavOpen(true)}
          aria-label="Open menu"
          className="p-1 -ml-1"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <span className="font-bold text-sm tracking-tight">KDU</span>
        {showBell ? <NotificationBell /> : <span className="w-6" />}
      </div>

      {/* Backdrop (mobile only, shown while nav is open) */}
      {mobileNavOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/40 z-40"
          onClick={() => setMobileNavOpen(false)}
        />
      )}

      <aside
        className={clsx(
          "w-60 bg-brand-700 text-white flex flex-col fixed md:static inset-y-0 left-0 z-50",
          "transition-transform duration-200 md:translate-x-0",
          mobileNavOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
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
            {showBell && <NotificationBell />}
            <button
              onClick={() => setMobileNavOpen(false)}
              aria-label="Close menu"
              className="md:hidden p-1 text-brand-100 hover:text-white"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
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
                onClick={() => setMobileNavOpen(false)}
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
            onClick={() => setMobileNavOpen(false)}
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

      <main className="flex-1 overflow-y-auto pt-14 md:pt-0">
        <Outlet />
      </main>
    </div>
  );
}
