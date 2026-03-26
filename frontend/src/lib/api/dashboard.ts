/**
 * ダッシュボードAPI
 */
import { apiClient } from './client';

// 型定義
export type HeatmapStatus = 'surplus' | 'balanced' | 'tight' | 'shortage';
export type CoverageStatus = 'sufficient' | 'partial' | 'insufficient';

export interface FulfillmentSummary {
  fulfillment_rate: number;
  total_slots: number;
  one_to_two_slots: number;
  one_to_one_slots: number;
}

export interface PersonnelSummary {
  teacher_count: number;
  student_count: number;
}

export interface HeatmapCell {
  day_of_week: string;
  slot_number: number;
  supply: number;
  demand: number;
  balance: number;
  status: HeatmapStatus;
}

export interface HeatmapResponse {
  cells: HeatmapCell[];
}

export interface SubjectCoverage {
  subject_id: string;
  subject_name: string;
  grade_category: string;
  coverage_rate: number;
  status: CoverageStatus;
}

export interface SubjectCoverageResponse {
  items: SubjectCoverage[];
}

export interface SupplyDemandBalance {
  category: string;
  demand: number;
  supply: number;
  difference: number;
}

export interface SupplyDemandResponse {
  items: SupplyDemandBalance[];
}

export interface TermInfo {
  term_id: string;
  term_name: string;
  start_date: string;
  end_date: string;
  status: string;
  is_current: boolean;
}

export interface NotificationItem {
  notification_id: string;
  notification_type: string;
  severity: string;
  title: string;
  message: string;
  link_url: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationResponse {
  items: NotificationItem[];
  unread_count: number;
}

export interface DashboardResponse {
  classroom_id: string;
  classroom_name: string;
  fulfillment: FulfillmentSummary;
  personnel: PersonnelSummary;
  heatmap: HeatmapResponse;
  subject_coverage: SubjectCoverageResponse;
  supply_demand: SupplyDemandResponse;
  current_term: TermInfo | null;
  next_term: TermInfo | null;
  notifications: NotificationResponse;
}

// API関数
export async function getDashboard(classroomId: string): Promise<DashboardResponse> {
  const response = await apiClient.get<DashboardResponse>(
    `/classrooms/${classroomId}/dashboard`
  );
  return response.data;
}

export async function getNotifications(classroomId: string): Promise<NotificationResponse> {
  const response = await apiClient.get<NotificationResponse>(
    `/classrooms/${classroomId}/dashboard/notifications`
  );
  return response.data;
}

export async function markNotificationAsRead(
  classroomId: string,
  notificationId: string
): Promise<void> {
  await apiClient.post(
    `/classrooms/${classroomId}/dashboard/notifications/${notificationId}/read`
  );
}
