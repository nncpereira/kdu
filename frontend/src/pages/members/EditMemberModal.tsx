import { useEffect } from "react";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input, Select } from "@/components/Input";
import { updateMember, UpdateMemberPayload, Member } from "@/api/members";

interface Props {
  member: Member | null;
  open: boolean;
  onClose: () => void;
}

const SALUTATIONS = ["Mr", "Mrs", "Ms", "Dr", "Prof", "Rev"];

export function EditMemberModal({ member, open, onClose }: Props) {
  const qc = useQueryClient();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UpdateMemberPayload>();

  useEffect(() => {
    if (member && open) {
      reset({
        salutation: member.salutation,
        first_name: member.first_name,
        middle_name: member.middle_name,
        last_name: member.last_name,
        national_id: member.national_id ?? "",
        phone_number: member.phone_number,
        email: member.email ?? "",
        date_of_birth: member.date_of_birth,
        aldeia: member.aldeia,
        suco: member.suco,
        posto: member.posto,
        municipio: member.municipio,
        profession: member.profession,
      });
    }
  }, [member, open, reset]);

  const mutation = useMutation({
    mutationFn: (payload: UpdateMemberPayload) =>
      updateMember(member!.id, payload),
    onSuccess: () => {
      toast.success("Member details updated.");
      qc.invalidateQueries({ queryKey: ["members"] });
      qc.invalidateQueries({ queryKey: ["member", member!.id] });
      onClose();
    },
    onError: (err: any) => {
      toast.error(
        err?.response?.data?.detail ?? "Failed to update member."
      );
    },
  });

  if (!member) return null;

  async function onSubmit(data: UpdateMemberPayload) {
    await mutation.mutateAsync(data);
  }

  return (
    <Modal open={open} onClose={onClose} title="Edit Member Details" size="lg">
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
            {(mutation.error as any)?.response?.data?.detail ??
              "Failed to update member. Check the fields and try again."}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={isSubmitting}>
            Save Changes
          </Button>
        </div>
      </form>
    </Modal>
  );
}
