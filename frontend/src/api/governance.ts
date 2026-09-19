import { api } from "./client";

export interface GlobalConfig {
  id: string;
  parameter_key: string;
  parameter_value: Record<string, unknown>;
  effective_from: string;
  status: string;
}

export interface ConfigChange {
  id: string;
  parameter_key: string;
  proposed_value: Record<string, unknown>;
  effective_from: string;
  status: "PENDING_CHECK" | "PENDING_CERTIFY" | "CERTIFIED" | "REJECTED";
  created_at: string;
}

export async function listActiveConfig(): Promise<GlobalConfig[]> {
  const { data } = await api.get<GlobalConfig[]>("/governance/config/");
  return data;
}

export async function proposeChange(payload: {
  parameter_key: string;
  proposed_value: Record<string, unknown>;
  effective_from: string;
}): Promise<ConfigChange> {
  const { data } = await api.post<ConfigChange>(
    "/governance/config/propose/",
    payload
  );
  return data;
}

export async function certifyChange(id: string): Promise<ConfigChange> {
  const { data } = await api.post<ConfigChange>(
    `/governance/config/certify/${id}/`
  );
  return data;
}

export async function listChanges(): Promise<ConfigChange[]> {
  const { data } = await api.get<ConfigChange[]>("/governance/changes/");
  return data;
}