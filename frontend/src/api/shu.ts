import { api } from "./client";

export type FiscalYearStatus = "OPEN" | "CLOSED";

export type CalcStatus =
  | "DRAFT"
  | "PENDING_CHECK"
  | "PENDING_CERTIFY"
  | "CERTIFIED"
  | "PAYOUT_COMPLETE"
  | "REJECTED";

export interface FiscalYear {
  id: string;
  year_start: string;
  year_end: string;
  status: FiscalYearStatus;
  net_surplus: string;
  kapital_sosial: string;
  accumulated_reserva_legal: string;
  created_at: string;
}

export interface ShuCalculation {
  id: string;
  fy: string;
  net_surplus: string;
  reserva_legal_pct: string;
  admin_fund_pct: string;
  jasa_simpanan_pct: string;
  jasa_bunga_pct: string;
  reserva_legal_amt: string;
  admin_fund_amt: string;
  jasa_simpanan_amt: string;
  jasa_bunga_amt: string;
  status: CalcStatus;
  created_at: string;
}

export interface ShuPayout {
  id: string;
  member: string;
  member_number: string;
  full_name: string;
  jasa_simpanan_gross: string;
  jasa_bunga_gross: string;
  net_payout: string;
  status: string;
}

export async function listFiscalYears(): Promise<FiscalYear[]> {
  const { data } = await api.get<FiscalYear[]>("/shu/fiscal-years/");
  return data;
}

export async function getFiscalYear(id: string): Promise<FiscalYear> {
  const { data } = await api.get<FiscalYear>(`/shu/fiscal-years/${id}/`);
  return data;
}

export async function createFiscalYear(payload: {
  year_start: string;
  year_end: string;
}): Promise<FiscalYear> {
  const { data } = await api.post<FiscalYear>("/shu/fiscal-years/", payload);
  return data;
}

export async function calculateShu(fyId: string): Promise<ShuCalculation> {
  const { data } = await api.post<ShuCalculation>("/shu/calculate/", {
    fy_id: fyId,
  });
  return data;
}

export async function getCalculationForFiscalYear(
  fyId: string
): Promise<ShuCalculation | null> {
  try {
    const { data } = await api.get<ShuCalculation>(
      `/shu/fiscal-years/${fyId}/calculation/`
    );
    return data;
  } catch (err: any) {
    if (err?.response?.status === 404) return null;
    throw err;
  }
}

export async function getCalculation(id: string): Promise<ShuCalculation> {
  const { data } = await api.get<ShuCalculation>(`/shu/${id}/`);
  return data;
}

export async function cancelCalculation(id: string): Promise<ShuCalculation> {
  const { data } = await api.post<ShuCalculation>(`/shu/${id}/cancel/`);
  return data;
}

export async function listPayouts(calcId: string): Promise<ShuPayout[]> {
  const { data } = await api.get<ShuPayout[]>(`/shu/${calcId}/payouts/`);
  return data;
}

export async function runSnapshot(): Promise<{ rows_created: number }> {
  const { data } = await api.post("/shu/snapshot/");
  return data;
}

export async function runAggregation(fyId: string): Promise<{ rows_created: number }> {
  const { data } = await api.post("/shu/aggregate/", { fy_id: fyId });
  return data;
}

export async function backfillSnapshots(
  fyId: string
): Promise<{ rows_created: number }> {
  const { data } = await api.post("/shu/backfill/", { fy_id: fyId });
  return data;
}
