import { api } from "./client";

export interface PipelineActor {
  id: string;
  transaction_type: string;
  target_record_id: string;
  maker: string;
  maker_username: string;
  checker: string | null;
  checker_username: string | null;
  certifier: string | null;
  certifier_username: string | null;
  status: "PENDING_CHECK" | "PENDING_CERTIFY" | "COMPLETED" | "REJECTED";
  updated_at: string;
}

export interface TargetSummary {
  label: string;
  kind: string;
  member_number?: string;
  member_name?: string;
  amount?: string;
  [key: string]: unknown;
}

export interface PipelineActor {
  id: string;
  transaction_type: string;
  target_record_id: string;
  maker: string;
  maker_username: string;
  checker: string | null;
  checker_username: string | null;
  certifier: string | null;
  certifier_username: string | null;
  status: "PENDING_CHECK" | "PENDING_CERTIFY" | "COMPLETED" | "REJECTED";
  updated_at: string;
  target_summary: TargetSummary | null;   // ← new
}

export async function listPendingCheck(): Promise<PipelineActor[]> {
  const { data } = await api.get("/pipeline/pending-check/");
  return data;
}

export async function listPendingCertify(): Promise<PipelineActor[]> {
  const { data } = await api.get("/pipeline/pending-certify/");
  return data;
}

export async function checkActor(id: string): Promise<PipelineActor> {
  const { data } = await api.post(`/pipeline/${id}/check/`);
  return data;
}

export async function certifyActor(id: string): Promise<PipelineActor> {
  const { data } = await api.post(`/pipeline/${id}/certify/`);
  return data;
}

export async function rejectActor(
  id: string,
  reason: string
): Promise<PipelineActor> {
  const { data } = await api.post(`/pipeline/${id}/reject/`, { reason });
  return data;
}