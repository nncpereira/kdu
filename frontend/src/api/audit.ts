import { api } from "./client";

export type AuditAction =
  | "LOGIN_SUCCESS"
  | "LOGIN_FAILURE"
  | "LOGOUT"
  | "USER_CREATED"
  | "USER_DISABLED"
  | "USER_ENABLED"
  | "USER_PASSWORD_RESET"
  | "USER_UPDATED"
  | "MEMBER_LOGIN_CREATED"
  | "MEMBER_LOGIN_RESET"
  | "CONFIG_PROPOSED"
  | "CONFIG_CERTIFIED"
  | "CONFIG_REJECTED"
  | "MEMBER_EXIT_REQUESTED"
  | "MEMBER_EXIT_COMPLETED"
  | "REVERSAL_REQUESTED"
  | "REVERSAL_COMPLETED"
  | "OTHER";

export interface AuditEntry {
  id: string;
  actor: string | null;
  actor_username: string | null;
  actor_role: string | null;
  action: AuditAction;
  target_type: string;
  target_id: string | null;
  target_repr: string;
  description: string;
  metadata: Record<string, unknown>;
  ip_address: string | null;
  user_agent: string;
  created_at: string;
}

export interface AuditListResponse {
  count: number;
  limit: number;
  results: AuditEntry[];
}

export interface LedgerActivity {
  id: string;
  entry_date: string;
  description: string;
  maker_username: string | null;
  certifier_username: string | null;
  status: string;
  line_count: number;
  total_amount: string;
  is_reversal: boolean;
  created_at: string;
}

export interface LedgerActivityResponse {
  count: number;
  limit: number;
  results: LedgerActivity[];
}

export interface JournalLine {
  id: string;
  account_code: string;
  account_name: string;
  entry_type: "DEBIT" | "CREDIT";
  amount: string;
  member_id: string | null;
  member_number: string | null;
  member_name: string | null;
}

export interface JournalEntryDetail {
  id: string;
  entry_date: string;
  description: string;
  status: string;
  maker_username: string | null;
  certifier_username: string | null;
  is_reversal: boolean;
  original_journal_entry: string | null;
  created_at: string;
  lines: JournalLine[];
}

export interface AuditFilters {
  start?: string;
  end?: string;
  action?: string;
  actor?: string;
  target_type?: string;
  limit?: number;
}

function buildQuery(filters: AuditFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== "") params.set(k, String(v));
  });
  return params.toString();
}

export async function listAuditEntries(
  filters: AuditFilters = {}
): Promise<AuditListResponse> {
  const { data } = await api.get<AuditListResponse>(
    `/audit/log/?${buildQuery(filters)}`
  );
  return data;
}

export async function listLedgerActivity(
  filters: AuditFilters & { status?: string; reversals_only?: string } = {}
): Promise<LedgerActivityResponse> {
  const { data } = await api.get<LedgerActivityResponse>(
    `/audit/ledger/?${buildQuery(filters)}`
  );
  return data;
}

export function auditExportUrl(filters: AuditFilters = {}): string {
  return `/audit/log/export/?${buildQuery(filters)}`;
}

export async function getJournalEntry(id: string): Promise<JournalEntryDetail> {
  const { data } = await api.get<JournalEntryDetail>(`/audit/ledger/${id}/`);
  return data;
}