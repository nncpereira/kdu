import { api } from "./client";

export interface TrialBalanceRow {
  account_code: string;
  account_name: string;
  account_type: string;
  debit: string;
  credit: string;
  net: string;
}

export interface IncomeStatement {
  revenue: TrialBalanceRow[];
  expenses: TrialBalanceRow[];
  total_revenue: string;
  total_expenses: string;
  net_surplus: string;
}

export interface BalanceSheet {
  assets: TrialBalanceRow[];
  liabilities: TrialBalanceRow[];
  equity: TrialBalanceRow[];
  total_assets: string;
  total_liabilities: string;
  total_equity: string;
  balanced: boolean;
}

export interface SurplusDistribution {
  reserva_legal_amt: string;
  admin_fund_amt: string;
  jasa_simpanan_amt: string;
  jasa_bunga_amt: string;
  status: string;
}

export interface DashboardSummary {
  members: { active: number; pending: number; dormant: number };
  savings: { voluntary_total: string };
  loans: { disbursed: number; outstanding_total: string };
  pipeline: { pending_check: number; pending_certify: number };
  recent_activity: {
    type: string;
    amount: string;
    member_number: string;
    created_at: string;
  }[];
}

export async function getDashboard(): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>("/reports/dashboard/");
  return data;
}

export async function getTrialBalance(asOf: string): Promise<TrialBalanceRow[]> {
  const { data } = await api.get<TrialBalanceRow[]>("/reports/trial-balance/", {
    params: { as_of: asOf },
  });
  return data;
}

export async function getIncomeStatement(
  start: string,
  end: string
): Promise<IncomeStatement> {
  const { data } = await api.get<IncomeStatement>(
    "/reports/income-statement/",
    { params: { start, end } }
  );
  return data;
}

export async function getBalanceSheet(asOf: string): Promise<BalanceSheet> {
  const { data } = await api.get<BalanceSheet>("/reports/balance-sheet/", {
    params: { as_of: asOf },
  });
  return data;
}

export async function getSurplusDistribution(
  fyId: string
): Promise<SurplusDistribution | null> {
  try {
    const { data } = await api.get<SurplusDistribution>(
      `/reports/surplus-distribution/${fyId}/`
    );
    return data;
  } catch (err: any) {
    if (err?.response?.status === 404) return null;
    throw err;
  }
}