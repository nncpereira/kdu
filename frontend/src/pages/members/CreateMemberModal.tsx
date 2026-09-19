import { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input, Select } from "@/components/Input";
import { createMember, CreateMemberPayload } from "@/api/members";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated?: (memberId: string) => void;
}

const SALUTATIONS = ["Mr", "Mrs", "Ms", "Dr", "Prof", "Rev"];

export function CreateMemberModal({ open, onClose, onCreated }: Props) {
  const qc = useQueryClient();
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
      onClose();
      onCreated?.(member.id);
    },
  });

  async function onSubmit(data: CreateMemberPayload) {
    await mutation.mutateAsync(data);
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

        {mutation.isError && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
            Failed to create member. Check the fields and try again.
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