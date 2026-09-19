import { api } from "./client";

export type ExpenseStatus =
  | "PENDING_CHECK"
  | "PENDING_CERTIFY"
  | "COMPLETED"
  | "REJECTED";

export interface Expense {
  id: string;
  description: string;
  amount: string;
  expense_account_code: string;
  payment_date: string;
  status: ExpenseStatus;
  created_at: string;
}

export interface CreateExpensePayload {
  description: string;
  amount: string;
  expense_account_code: string;
  payment_date?: string;
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
  const { data } = await api.post<Expense>("/expenses/", payload);
  return data;
}