import { api } from "./client";

export type ReversalStatus =
  | "PENDING_CHECK"
  | "PENDING_CERTIFY"
  | "COMPLETED"
  | "REJECTED";

export type ReversalSourceType =
  | "SAVINGS_TRANSACTION"
  | "LOAN_REPAYMENT"
  | "EXPENSE"
  | "OTHER";

export interface ReversalRequest {
  id: string;
  original_journal_entry: string;
  original_description: string;
  original_entry_date: string;
  reversal_journal_entry: string | null;
  source_type: ReversalSourceType;
  source_id: string | null;
  reason: string;
  status: ReversalStatus;
  maker_username: string | null;
  created_at: string;
}

export interface CreateReversalPayload {
  original_journal_entry: string;
  source_type: ReversalSourceType;
  source_id?: string;
  reason: string;
}

export async function listReversals(): Promise<ReversalRequest[]> {
  const { data } = await api.get<ReversalRequest[]>("/ledger/reversals/");
  return data;
}

export async function createReversal(
  payload: CreateReversalPayload
): Promise<ReversalRequest> {
  const { data } = await api.post<ReversalRequest>(
    "/ledger/reversals/",
    payload
  );
  return data;
}

export async function getReversal(id: string): Promise<ReversalRequest> {
  const { data } = await api.get<ReversalRequest>(`/ledger/reversals/${id}/`);
  return data;
}