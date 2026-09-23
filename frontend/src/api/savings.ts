import { api } from "./client";

export type SavingsTxnType = "DEPOSIT" | "WITHDRAWAL" | "LOAN_REPAYMENT_SWEEP";
export type SavingsTxnStatus =
  | "DRAFT"
  | "PENDING_CHECK"
  | "PENDING_CERTIFY"
  | "COMPLETED"
  | "REJECTED"
  | "REVERSED";

export interface SavingsTransaction {
  id: string;
  member: string;
  member_number: string;
  transaction_type: SavingsTxnType;
  requested_amount: string;
  obligatory_portion: string;
  voluntary_portion: string;
  status: SavingsTxnStatus;
  pipeline_actor: string | null;
  journal_entry: string | null;
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface VoluntaryBalance {
  member: string;
  balance_available: string;
  balance_held_pipeline: string;
  updated_at: string;
}

export interface PipelineResponse {
  pipeline_actor_id?: string;
  [k: string]: unknown;
}

export async function deposit(
  memberId: string,
  amount: string
): Promise<SavingsTransaction> {
  const { data } = await api.post<SavingsTransaction>(
    "/savings/deposit/",
    { member: memberId, amount }
  );
  return data;
}

export async function withdraw(
  memberId: string,
  amount: string
): Promise<SavingsTransaction> {
  const { data } = await api.post<SavingsTransaction>(
    "/savings/withdraw/",
    { member: memberId, amount }
  );
  return data;
}

export async function listTransactions(params?: {
  member?: string;
  type?: SavingsTxnType;
  page?: number;
  page_size?: number;
}): Promise<Paginated<SavingsTransaction>> {
  const { data } = await api.get<Paginated<SavingsTransaction>>(
    "/savings/transactions/",
    { params }
  );
  return data;
}

export async function getVoluntaryBalance(
  memberId: string
): Promise<VoluntaryBalance> {
  const { data } = await api.get<VoluntaryBalance>(
    `/savings/members/${memberId}/voluntary/`
  );
  return data;
}