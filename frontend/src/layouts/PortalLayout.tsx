import { Link, Outlet, useLocation } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "@/auth/useAuth";
import { Logo } from "@/components/Logo";

const NAV = [
  { to: "/portal/dashboard", label: "Home" },
  { to: "/portal/savings", label: "Savings" },
  { to: "/portal/loans", label: "Loans" },
  { to: "/portal/statement", label: "SHU Statement" },
  { to: "/portal/profile", label: "Profile" },
];

export function PortalLayout() {
  const { profile, logout } = useAuth();
  const location = useLocation();
  const showNav = !profile?.must_change_password;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-brand-700 text-white shadow-md">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center">
              <Logo size={34} />
            </div>
            <div>
              <p className="text-[10px] text-brand-100 uppercase tracking-widest leading-tight">
                Member Portal
              </p>
              <p className="text-sm font-semibold leading-tight">
                {profile?.first_name || profile?.username}
                {profile?.last_name ? ` ${profile.last_name}` : ""}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="text-xs text-brand-100 hover:text-white underline"
          >
            Log out
          </button>
        </div>

        {/* Tab nav */}
        {showNav && (
          <nav className="border-t border-brand-600">
            <div className="max-w-5xl mx-auto px-4 flex overflow-x-auto">
              {NAV.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={clsx(
                    "px-4 py-3 text-sm whitespace-nowrap border-b-2 transition",
                    location.pathname === item.to
                      ? "border-white text-white font-semibold"
                      : "border-transparent text-brand-100 hover:text-white"
                  )}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </nav>
        )}

        {!showNav && (
          <div className="bg-yellow-100 border-t border-yellow-200 px-4 py-2 text-xs text-yellow-800 text-center">
            Please set a new password before continuing.
          </div>
        )}
      </header>

      {/* Content */}
      <main className="flex-1">
        <div className="max-w-5xl mx-auto p-4 sm:p-6">
          <Outlet />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4 mt-6">
        <div className="max-w-5xl mx-auto px-4 text-center">
          <p className="text-xs text-gray-500">
            Koperativa Dezenvolvimentu Umanu · KDU
          </p>
          <p className="text-[10px] text-gray-400 mt-1">
            DL 16/2004 as amended by DL 76/2022
          </p>
        </div>
      </footer>
    </div>
  );
}