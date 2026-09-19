import { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

type Variant = "primary" | "secondary" | "danger";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

export function Button({
  variant = "primary",
  loading,
  className,
  children,
  ...rest
}: Props) {
  const base =
    "px-4 py-2 rounded-md font-medium transition disabled:opacity-50 disabled:cursor-not-allowed";
  const variants: Record<Variant, string> = {
    primary: "bg-brand-600 text-white hover:bg-brand-700",
    secondary: "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50",
    danger: "bg-red-600 text-white hover:bg-red-700",
  };
  return (
    <button
      {...rest}
      disabled={rest.disabled || loading}
      className={clsx(base, variants[variant], className)}
    >
      {loading ? "..." : children}
    </button>
  );
}