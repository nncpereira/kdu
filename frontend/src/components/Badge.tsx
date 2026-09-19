import clsx from "clsx";

const COLORS: Record<string, string> = {
  // pipeline
  PENDING_CHECK: "bg-yellow-100 text-yellow-800",
  PENDING_CERTIFY: "bg-blue-100 text-blue-800",
  COMPLETED: "bg-green-100 text-green-800",
  REJECTED: "bg-red-100 text-red-800",
  // savings
  DEPOSIT: "bg-emerald-100 text-emerald-800",
  WITHDRAWAL: "bg-orange-100 text-orange-800",
  // loans
  DISBURSED: "bg-blue-100 text-blue-800",
  DRAFT: "bg-gray-100 text-gray-800",
  FULLY_REPAID: "bg-green-100 text-green-800",
  WRITTEN_OFF: "bg-red-100 text-red-800",
  MANUAL: "bg-indigo-100 text-indigo-800",
  SCHEDULED: "bg-cyan-100 text-cyan-800",
  // SHU
  OPEN: "bg-green-100 text-green-800",
  CLOSED: "bg-gray-100 text-gray-800",
  PAYOUT_COMPLETE: "bg-emerald-100 text-emerald-800",
  CERTIFIED: "bg-blue-100 text-blue-800",
  // members
  Active: "bg-green-100 text-green-800",
  Pending: "bg-yellow-100 text-yellow-800",
  Dormant: "bg-gray-100 text-gray-800",
  Suspended: "bg-orange-100 text-orange-800",
  Disabled: "bg-gray-200 text-gray-600",
  REVERSED: "bg-gray-200 text-gray-700",

};

export function Badge({ value }: { value: string }) {
  return (
    <span
      className={clsx(
        "inline-block px-2 py-1 text-xs font-medium rounded",
        COLORS[value] ?? "bg-gray-100 text-gray-800"
      )}
    >
      {value.replace("_", " ")}
    </span>
  );
}