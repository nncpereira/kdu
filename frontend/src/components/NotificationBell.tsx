import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { getNotifications, Notification } from "@/api/notifications";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: getNotifications,
    refetchInterval: 60_000,          // refresh every minute
    refetchOnWindowFocus: true,
  });

  const count = data?.count ?? 0;
  const items = data?.items ?? [];

  // Close dropdown on outside click
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", onClick);
      return () => document.removeEventListener("mousedown", onClick);
    }
  }, [open]);

  // Close on Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    if (open) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div className="relative" ref={wrapperRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        className={clsx(
          "relative w-9 h-9 rounded-full flex items-center justify-center",
          "transition-colors",
          open ? "bg-brand-600" : "hover:bg-brand-600"
        )}
        aria-label={
          count > 0
            ? `${count} notification${count === 1 ? "" : "s"}`
            : "Notifications"
        }
      >
        <BellIcon />
        {count > 0 && (
          <span
            className={clsx(
              "absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px]",
              "rounded-full flex items-center justify-center",
              "text-[10px] font-bold text-white",
              "bg-red-500 ring-2 ring-brand-700"
            )}
          >
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>

      {open && (
        <div
            className={clsx(
            "absolute left-full top-0 ml-3 w-96 max-h-[480px] overflow-y-auto",
            "bg-white rounded-lg shadow-xl border border-gray-200",
            "z-50"
            )}
        >
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-800">
              Notifications
            </h3>
            {count > 0 && (
              <span className="text-xs text-gray-500">{count} pending</span>
            )}
          </div>

          {items.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm text-gray-500">You're all caught up.</p>
            </div>
          ) : (
            <ul className="divide-y divide-gray-100">
              {items.map((item) => (
                <li key={item.id}>
                  <NotificationItem
                    item={item}
                    onNavigate={() => setOpen(false)}
                  />
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function NotificationItem({
  item,
  onNavigate,
}: {
  item: Notification;
  onNavigate: () => void;
}) {
  const isRejected = item.queue === "REJECTED";

  return (
    <Link
      to={item.link}
      onClick={onNavigate}
      className={clsx(
        "block px-4 py-3 hover:bg-gray-50 transition-colors",
        isRejected && "border-l-4 border-red-500 pl-3"
      )}
    >
      <div className="flex items-start gap-3">
        <QueueIcon queue={item.queue} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-800 line-clamp-2">
            {item.label}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            {item.transaction_type.replace("_", " ")}
            {item.maker_username && ` · by ${item.maker_username}`}
          </p>
          {isRejected && item.reason && (
            <p className="text-xs text-red-600 mt-1 italic truncate">
              "{item.reason}"
            </p>
          )}
          {!isRejected && item.action && (
            <p className="text-xs text-gray-400 mt-1">{item.action}</p>
          )}
        </div>
        <p className="text-[10px] text-gray-400 whitespace-nowrap mt-0.5">
          {timeAgo(item.updated_at)}
        </p>
      </div>
    </Link>
  );
}

function QueueIcon({ queue }: { queue?: string }) {
  if (queue === "PENDING_CHECK") {
    return (
      <span className="w-2 h-2 rounded-full bg-yellow-500 shrink-0 mt-1.5" />
    );
  }
  if (queue === "PENDING_CERTIFY") {
    return (
      <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0 mt-1.5" />
    );
  }
  if (queue === "REJECTED") {
    return (
      <span className="w-2 h-2 rounded-full bg-red-500 shrink-0 mt-1.5" />
    );
  }
  return <span className="w-2 h-2 rounded-full bg-gray-300 shrink-0 mt-1.5" />;
}

function BellIcon() {
  return (
    <svg
      className="w-5 h-5 text-white"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
      />
    </svg>
  );
}

function timeAgo(iso: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(iso).getTime()) / 1000
  );
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
  return `${Math.floor(seconds / 86400)}d`;
}