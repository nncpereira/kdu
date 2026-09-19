import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { proposeChange } from "@/api/governance";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function ProposeSplitModal({ open, onClose }: Props) {
  const qc = useQueryClient();
  const [reserva, setReserva] = useState("25");
  const [admin, setAdmin] = useState("25");
  const [simpanan, setSimpanan] = useState("25");
  const [bunga, setBunga] = useState("25");
  const [effectiveFrom, setEffectiveFrom] = useState(() => {
    const y = new Date().getFullYear();
    return `${y + 1}-01-01`;
  });
  const [error, setError] = useState<string | null>(null);

  const r = parseFloat(reserva) || 0;
  const a = parseFloat(admin) || 0;
  const s = parseFloat(simpanan) || 0;
  const b = parseFloat(bunga) || 0;
  const total = r + a + s + b;
  const reservaTooLow = r < 25; // Must be >= 25% until reserve = 100% capital

  const mutation = useMutation({
    mutationFn: () =>
      proposeChange({
        parameter_key: "shu_split",
        proposed_value: {
          reserva_legal_pct: r,
          admin_fund_pct: a,
          jasa_simpanan_pct: s,
          jasa_bunga_pct: b,
        },
        effective_from: effectiveFrom,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["governance"] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      onClose();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail ?? "Proposal failed.");
    },
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (total !== 100) {
      setError("The four percentages must sum to exactly 100.");
      return;
    }
    await mutation.mutateAsync();
  }

  return (
    <Modal open={open} onClose={onClose} title="Propose New SHU Split" size="md">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3">
          <p className="font-medium mb-1">DL 76/2022 Art. 69</p>
          <p>
            Reserva Legal must be at least 25% of net surplus until the
            accumulated reserve reaches 100% of social capital. Once the
            threshold is met, the AGM may approve a lower percentage.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Reserva Legal (%)"
            type="number"
            step="0.01"
            min="0"
            max="100"
            value={reserva}
            onChange={(e) => setReserva(e.target.value)}
          />
          <Input
            label="Admin & Operational Fund (%)"
            type="number"
            step="0.01"
            min="0"
            max="100"
            value={admin}
            onChange={(e) => setAdmin(e.target.value)}
          />
          <Input
            label="Jasa Simpanan (%)"
            type="number"
            step="0.01"
            min="0"
            max="100"
            value={simpanan}
            onChange={(e) => setSimpanan(e.target.value)}
          />
          <Input
            label="Jasa Bunga (%)"
            type="number"
            step="0.01"
            min="0"
            max="100"
            value={bunga}
            onChange={(e) => setBunga(e.target.value)}
          />
        </div>

        <div className="text-sm">
          <span className="text-gray-500">Total: </span>
          <span className={total === 100 ? "text-green-700 font-semibold" : "text-red-600 font-semibold"}>
            {total}%
          </span>
        </div>

        <Input
          label="Effective From"
          type="date"
          value={effectiveFrom}
          onChange={(e) => setEffectiveFrom(e.target.value)}
        />

        {reservaTooLow && (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs rounded p-3">
            Reserva Legal is below 25%. This will be rejected unless the
            cooperative's accumulated reserve already exceeds 100% of social
            capital.
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={mutation.isPending}
            disabled={total !== 100}
          >
            Propose Change
          </Button>
        </div>
      </form>
    </Modal>
  );
}