import { InputHTMLAttributes, forwardRef, SelectHTMLAttributes } from "react";
import clsx from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...rest }, ref) => (
    <div>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <input
        ref={ref}
        {...rest}
        className={clsx(
          "w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500",
          error ? "border-red-400" : "border-gray-300",
          className
        )}
      />
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
);
Input.displayName = "Input";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, className, children, ...rest }, ref) => (
    <div>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <select
        ref={ref}
        {...rest}
        className={clsx(
          "w-full border rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500",
          error ? "border-red-400" : "border-gray-300",
          className
        )}
      >
        {children}
      </select>
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
);
Select.displayName = "Select";