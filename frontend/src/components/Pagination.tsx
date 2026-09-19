interface Props {
  count: number;
  page: number;
  pageSize: number;
  onChange: (page: number) => void;
}

export function Pagination({ count, page, pageSize, onChange }: Props) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  if (totalPages === 1) return null;

  return (
    <div className="flex items-center justify-between mt-4 text-sm">
      <p className="text-gray-500">
        Page {page} of {totalPages} · {count} total
      </p>
      <div className="space-x-2">
        <button
          disabled={page === 1}
          onClick={() => onChange(page - 1)}
          className="px-3 py-1 border border-gray-300 rounded disabled:opacity-50"
        >
          Previous
        </button>
        <button
          disabled={page === totalPages}
          onClick={() => onChange(page + 1)}
          className="px-3 py-1 border border-gray-300 rounded disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}