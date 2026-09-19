import { api } from "./client";

export type MemberStatus =
  | "Pending"
  | "Active"
  | "Dormant"
  | "Suspended"
  | "Closed";

export interface Member {
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
  status: MemberStatus;
  kapital_sosial_balance: string;
  date_joined: string;
  last_transaction_at: string | null;
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CreateMemberPayload {
  first_name: string;
  middle_name?: string;
  last_name: string;
  salutation?: string;
  national_id?: string;
  phone_number: string;
  email?: string;
  date_of_birth: string;
  aldeia?: string;
  suco?: string;
  posto?: string;
  municipio?: string;
  profession?: string;
}

export interface PipelineResponse {
  onboarding_id?: string;
  exit_request_id?: string;
  pipeline_actor_id: string;
}

export async function listMembers(params?: {
  status?: string;
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<Paginated<Member>> {
  const { data } = await api.get<Paginated<Member>>("/members/", { params });
  return data;
}

export async function getMember(id: string): Promise<Member> {
  const { data } = await api.get<Member>(`/members/${id}/`);
  return data;
}

export async function createMember(
  payload: CreateMemberPayload
): Promise<Member> {
  const { data } = await api.post<Member>("/members/", payload);
  return data;
}

export async function payInitialCapital(
  memberId: string,
  amount: string
): Promise<PipelineResponse> {
  const { data } = await api.post<PipelineResponse>(
    `/members/${memberId}/initial-capital/`,
    { amount }
  );
  return data;
}

export async function requestMemberExit(
  memberId: string,
  reason: string
): Promise<PipelineResponse> {
  const { data } = await api.post<PipelineResponse>(
    `/members/${memberId}/exit/`,
    { reason }
  );
  return data;
}