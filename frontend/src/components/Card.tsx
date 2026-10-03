import { ReactNode } from "react";
import clsx from "clsx";

export function Card({
  title,
  children,
  action,
  onClick,
}: {
  title?: string;
  children: ReactNode;
  action?: ReactNode;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        "bg-white rounded-lg shadow border border-gray-200",
        onClick && "cursor-pointer hover:shadow-md hover:border-gray-300 transition"
      )}
    >
      {title && (
        <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}