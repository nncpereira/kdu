import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/auth/useAuth";
import clsx from "clsx";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/members", label: "Members" },
  { to: "/savings", label: "Savings" },
  { to: "/loans", label: "Loans" },
  { to: "/expenses", label: "Expenses" },
  { to: "/shu", label: "SHU" },
  { to: "/pipeline", label: "Pipeline" },
  { to: "/reports", label: "Reports" },
  { to: "/governance", label: "Governance" },
  { to: "/users", label: "Users", role: "SUPERADMIN" },
];

export function AppLayout() {
  const { profile, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="flex h-screen">
      <aside className="w-60 bg-brand-700 text-white flex flex-col">
        <div className="px-5 py-5 border-b border-brand-600">
          <h1 className="text-lg font-bold">KDU</h1>
          <p className="text-xs text-brand-100">Cooperative Core</p>
        </div>
        <nav className="flex-1 py-4">
          {NAV.filter((item) => !item.role || profile?.role === item.role).map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={clsx(
                "block px-5 py-2 text-sm hover:bg-brand-600",
                location.pathname === item.to && "bg-brand-600 font-semibold"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-brand-600 text-xs">
          <Link
            to="/profile"
            className={clsx(
              "block hover:bg-brand-600 -mx-5 px-5 py-2",
              location.pathname === "/profile" && "bg-brand-600"
            )}
          >
            <p className="font-medium">{profile?.username}</p>
            <p className="text-brand-100">{profile?.role}</p>
          </Link>
          <button
            onClick={logout}
            className="mt-2 text-brand-100 hover:text-white underline"
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-gray-50">
        <Outlet />
      </main>
    </div>
  );
}
