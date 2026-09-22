import { api } from "./client";

export type NotificationQueue =
  | "PENDING_CHECK"
  | "PENDING_CERTIFY"
  | "REJECTED";

export interface Notification {
  id: string;
  kind: string;
  transaction_type: string;
  status: string;
  queue?: NotificationQueue;
  label: string;
  action?: string;
  reason?: string;
  maker_username: string | null;
  updated_at: string;
  link: string;
}

export interface NotificationsResponse {
  count: number;
  items: Notification[];
}

export async function getNotifications(): Promise<NotificationsResponse> {
  const { data } = await api.get<NotificationsResponse>(
    "/audit/notifications/"
  );
  return data;
}