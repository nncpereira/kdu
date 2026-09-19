interface Props {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  max?: string;
  min?: string;
}

export function DatePicker({ label, value, onChange, max, min }: Props) {
  return (
    <div>
      {label && (
        <label className="block text-xs font-medium text-gray-600 mb-1">
          {label}
        </label>
      )}
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        max={max}
        min={min}
        className="border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
      />
    </div>
  );
}