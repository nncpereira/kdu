import { api } from "./client";

export type LoanStatus =
  | "DRAFT"
  | "DISBURSED"
  | "FULLY_REPAID"
  | "WRITTEN_OFF";

export type RepaymentMode = "MANUAL" | "SCHEDULED";

export type RepaymentStatus =
  | "PENDING_CHECK"
  | "PENDING_CERTIFY"
  | "COMPLETED"
  | "REJECTED";

export interface Loan {
  id: string;
  member: string;
  member_number: string;
  principal_original: string;
  principal_outstanding: string;
  monthly_rate: string;
  term_months: number;
  purpose: string;
  disbursed_date: string | null;
  status: LoanStatus;
  created_at: string;
}

export interface LoanRepayment {
  id: string;
  loan: string;
  principal_paid: string;
  interest_paid: string;
  payment_date: string;
  mode: RepaymentMode;
  status: RepaymentStatus;
  journal_entry: string | null;
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface OriginateLoanPayload {
  member: string;
  principal: string;
  term_months: number;
  monthly_rate: string;
  purpose?: string;
}

export async function listLoans(params?: {
  member?: string;
  status?: LoanStatus;
  page?: number;
  page_size?: number;
}): Promise<Paginated<Loan>> {
  const { data } = await api.get<Paginated<Loan>>("/loans/", { params });
  return data;
}

export async function getLoan(id: string): Promise<Loan> {
  const { data } = await api.get<Loan>(`/loans/${id}/`);
  return data;
}

export async function originateLoan(
  payload: OriginateLoanPayload
): Promise<Loan> {
  const { data } = await api.post<Loan>("/loans/", payload);
  return data;
}

export async function manualRepayment(
  loanId: string,
  payload: {
    principal_paid: string;
    interest_paid: string;
    payment_date?: string;
  }
): Promise<LoanRepayment> {
  const { data } = await api.post<LoanRepayment>(
    `/loans/${loanId}/repay/manual/`,
    payload
  );
  return data;
}

export async function scheduledRepayment(
  loanId: string,
  payload: {
    cash_amount: string;
    scheduled_principal: string;
    payment_date?: string;
  }
): Promise<LoanRepayment> {
  const { data } = await api.post<LoanRepayment>(
    `/loans/${loanId}/repay/scheduled/`,
    payload
  );
  return data;
}

export async function listRepayments(
  loanId: string
): Promise<LoanRepayment[]> {
  const { data } = await api.get<LoanRepayment[]>(
    `/loans/${loanId}/repayments/`
  );
  return data;
}
