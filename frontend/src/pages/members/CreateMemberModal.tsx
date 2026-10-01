import { FormEvent, useState } from "react";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input, Select } from "@/components/Input";
import { createMember, CreateMemberPayload } from "@/api/members";
import { MemberPicker } from "../savings/MemberPicker";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated?: (memberId: string) => void;
}

const SALUTATIONS = ["Mr", "Mrs", "Ms", "Dr", "Prof", "Rev"];

export function CreateMemberModal({ open, onClose, onCreated }: Props) {
  const qc = useQueryClient();
  const [endorser1Id, setEndorser1Id] = useState("");
  const [endorser2Id, setEndorser2Id] = useState("");
  const [endorserError, setEndorserError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateMemberPayload>({
    defaultValues: {
      salutation: "Mr",
      municipio: "Dili",
    },
  });

  const mutation = useMutation({
    mutationFn: createMember,
    onSuccess: (member) => {
      qc.invalidateQueries({ queryKey: ["members"] });
      reset();
      setEndorser1Id("");
      setEndorser2Id("");
      onClose();
      onCreated?.(member.id);
    },
    onError: (err: any) => {
      toast.error(
        err?.response?.data?.detail ?? "Failed to create member."
      );
    },
  });

  async function onSubmit(data: CreateMemberPayload) {
    setEndorserError(null);
    if (!endorser1Id || !endorser2Id) {
      setEndorserError("Two endorsers are required to onboard a new member.");
      return;
    }
    await mutation.mutateAsync({
      ...data,
      endorser_1: endorser1Id,
      endorser_2: endorser2Id,
    });
  }

  return (
    <Modal open={open} onClose={onClose} title="Onboard New Member" size="lg">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Select label="Salutation" {...register("salutation")}>
            {SALUTATIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
          <div />
          <Input
            label="First Name *"
            {...register("first_name", { required: "Required" })}
            error={errors.first_name?.message}
          />
          <Input label="Middle Name" {...register("middle_name")} />
          <Input
            label="Last Name *"
            {...register("last_name", { required: "Required" })}
            error={errors.last_name?.message}
          />
          <Input
            label="Phone *"
            {...register("phone_number", { required: "Required" })}
            error={errors.phone_number?.message}
          />
          <Input
            label="Date of Birth *"
            type="date"
            {...register("date_of_birth", { required: "Required" })}
            error={errors.date_of_birth?.message}
          />
          <Input label="Email" type="email" {...register("email")} />
          <Input label="National ID" {...register("national_id")} />
          <Input label="Profession" {...register("profession")} />
          <Input label="Aldeia" {...register("aldeia")} />
          <Input label="Suco" {...register("suco")} />
          <Input label="Posto" {...register("posto")} />
          <Input label="Municipio" {...register("municipio")} />
        </div>

        <div className="pt-2 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-3">
            Two existing active members must endorse this application.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <MemberPicker
              label="Endorser 1"
              status="Active"
              value={endorser1Id}
              onChange={(id) => setEndorser1Id(id)}
              excludeIds={endorser2Id ? [endorser2Id] : undefined}
            />
            <MemberPicker
              label="Endorser 2"
              status="Active"
              value={endorser2Id}
              onChange={(id) => setEndorser2Id(id)}
              excludeIds={endorser1Id ? [endorser1Id] : undefined}
            />
          </div>
        </div>

        {endorserError && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
            {endorserError}
          </div>
        )}

        {mutation.isError && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
            {(mutation.error as any)?.response?.data?.detail ??
              "Failed to create member. Check the fields and try again."}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={isSubmitting}>
            Create Member
          </Button>
        </div>
      </form>
    </Modal>
  );
}