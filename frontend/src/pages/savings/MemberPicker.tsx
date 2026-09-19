import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listMembers, Member } from "@/api/members";

interface Props {
  value: string;
  onChange: (memberId: string, member: Member | null) => void;
  label?: string;
}

export function MemberPicker({ value, onChange, label = "Member" }: Props) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ["members", "picker", search],
    queryFn: () =>
      listMembers({ search: search || undefined, page_size: 20 }),
    enabled: open || search.length > 0,
  });

  // Reset search when closing
  useEffect(() => {
    if (!open) setSearch("");
  }, [open]);

  const results = data?.results ?? [];

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label} *
      </label>

      {value ? (
        <SelectedMember
          memberId={value}
          onClear={() => onChange("", null)}
        />
      ) : (
        <>
          <input
            type="text"
            placeholder="Search by name, member #, phone…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          {open && results.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded shadow-lg max-h-64 overflow-y-auto">
              {results.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => {
                    onChange(m.id, m);
                    setOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-0"
                >
                  <p className="text-sm font-medium">{m.full_name}</p>
                  <p className="text-xs text-gray-500 font-mono">
                    {m.membership_number} · {m.phone_number}
                  </p>
                </button>
              ))}
            </div>
          )}
          {open && search && results.length === 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded shadow-lg px-3 py-2 text-sm text-gray-500">
              No members found.
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SelectedMember({
  memberId,
  onClear,
}: {
  memberId: string;
  onClear: () => void;
}) {
  const { data } = useQuery({
    queryKey: ["member", memberId],
    queryFn: async () => {
      const { getMember } = await import("@/api/members");
      return getMember(memberId);
    },
  });

  if (!data) {
    return <p className="text-sm text-gray-500">Loading member…</p>;
  }

  return (
    <div className="flex items-center justify-between border border-gray-300 rounded px-3 py-2 bg-gray-50">
      <div>
        <p className="text-sm font-medium">{data.full_name}</p>
        <p className="text-xs text-gray-500 font-mono">
          {data.membership_number}
        </p>
      </div>
      <button
        type="button"
        onClick={onClear}
        className="text-xs text-brand-600 hover:underline"
      >
        Change
      </button>
    </div>
  );
}