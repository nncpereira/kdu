import { api } from "./client";

export type ExpenseStatus =
  | "PENDING_CHECK"
  | "PENDING_CERTIFY"
  | "COMPLETED"
  | "REJECTED"
  | "REVERSED";

export interface Expense {
  id: string;
  description: string;
  amount: string;
  expense_account_code: string;
  payment_date: string;
  status: ExpenseStatus;
  journal_entry: string | null;
  receipt: string | null;          // ← new
  receipt_url: string | null;      // ← new
  created_at: string;
}

export interface CreateExpensePayload {
  description: string;
  amount: string;
  expense_account_code: string;
  payment_date?: string;
  receipt?: File | null;           // ← new
}

export async function listExpenses(params?: {
  expense_account_code?: string;
}): Promise<Expense[]> {
  const { data } = await api.get<Expense[]>("/expenses/", { params });
  return data;
}

export async function getExpense(id: string): Promise<Expense> {
  const { data } = await api.get<Expense>(`/expenses/${id}/`);
  return data;
}

export async function recordExpense(
  payload: CreateExpensePayload
): Promise<Expense> {
  // If a receipt file is attached, send as multipart. Otherwise JSON.
  if (payload.receipt instanceof File) {
    const fd = new FormData();
    fd.append("description", payload.description);
    fd.append("amount", payload.amount);
    fd.append("expense_account_code", payload.expense_account_code);
    if (payload.payment_date) {
      fd.append("payment_date", payload.payment_date);
    }
    fd.append("receipt", payload.receipt);

    const { data } = await api.post<Expense>("/expenses/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  }

  // No receipt — send JSON to keep it simple.
  const { receipt, ...jsonPayload } = payload;
  const { data } = await api.post<Expense>("/expenses/", jsonPayload);
  return data;
}
