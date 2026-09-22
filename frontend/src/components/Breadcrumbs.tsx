import { Link } from "react-router-dom";

export interface BreadcrumbItem {
  label: string;
  to?: string;      // omit for the last (current) item
}

export function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  return (
    <nav
      aria-label="Breadcrumb"
      className="flex items-center gap-1.5 text-sm text-gray-500 mb-3"
    >
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5 min-w-0">
          {i > 0 && (
            <svg
              className="w-3.5 h-3.5 text-gray-400 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          )}
          {item.to ? (
            <Link
              to={item.to}
              className="hover:text-brand-600 hover:underline truncate"
            >
              {item.label}
            </Link>
          ) : (
            <span className="text-gray-800 font-medium truncate">
              {item.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}