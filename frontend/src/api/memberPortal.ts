import { api } from "./client";

// ====================================================================
// Types
//====================================================================
export interface PortalMemberSummary {
  membership_number: string;
  full_name: string;
  status: string;
  date_joined: string;
}

export interface PortalRecentActivity {
  id: string;
  type: string;
  amount: string;
  status: string;
  created_at: string;
}

export interface PortalDashboard {
  member: PortalMemberSummary;
  capital: string;
  voluntary: string;
  voluntary_held: string;
  total_savings: string;
  loans: {
    active_count: number;
    outstanding_total: string;
  };
  recent_activity: PortalRecentActivity[];
}

export interface PortalProfile {
  id: string;
  membership_number: string;
  salutation: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  full_name: string;
  national_id: string | null;
  phone_number: string;
  email: string | null;
  date_of_birth: string;
  aldeia: string;
  suco: string;
  posto: string;
  municipio: string;
  profession: string;
  status: string;
  kapital_sosial_balance: string;
  date_joined: string;
}

export interface PortalSavings {
  kapital_sosial_balance: string;
  voluntary: {
    member: string;
    balance_available: string;
    balance_held_pipeline: string;
    updated_at: string | null;
  };
}

export interface PortalTransaction {
  id: string;
  transaction_type: "DEPOSIT" | "WITHDRAWAL";
  requested_amount: string;
  obligatory_portion: string;
  voluntary_portion: string;
  status: string;
  created_at: string;
}

export interface PortalLoan {
  id: string;
  principal_original: string;
  principal_outstanding: string;
  monthly_rate: string;
  term_months: number;
  purpose: string;
  status: string;
  disbursed_date: string | null;
  created_at: string;
}

export interface PortalShuPayout {
  id: string;
  fiscal_year_start: string;
  fiscal_year_end: string;
  jasa_simpanan_gross: string;
  jasa_bunga_gross: string;
  net_payout: string;
  status: string;
}

// ====================================================================
// API functions
// ====================================================================
export async function getMyDashboard(): Promise<PortalDashboard> {
  const { data } = await api.get<PortalDashboard>("/members/me/dashboard/");
  return data;
}

export async function getMyProfile(): Promise<PortalProfile> {
  const { data } = await api.get<PortalProfile>("/members/me/");
  return data;
}

export async function updateMyMemberProfile(payload: {
  phone_number?: string;
  email?: string;
  aldeia?: string;
  suco?: string;
  posto?: string;
  municipio?: string;
  profession?: string;
}): Promise<PortalProfile> {
  const { data } = await api.patch<PortalProfile>("/members/me/", payload);
  return data;
}

export async function getMySavings(): Promise<PortalSavings> {
  const { data } = await api.get<PortalSavings>("/members/me/savings/");
  return data;
}

export async function getMyTransactions(): Promise<PortalTransaction[]> {
  const { data } = await api.get<PortalTransaction[]>(
    "/members/me/transactions/"
  );
  return data;
}

export async function getMyLoans(): Promise<PortalLoan[]> {
  const { data } = await api.get<PortalLoan[]>("/members/me/loans/");
  return data;
}

export async function getMyShuStatement(): Promise<PortalShuPayout[]> {
  const { data } = await api.get<PortalShuPayout[]>("/members/me/shu/");
  return data;
}