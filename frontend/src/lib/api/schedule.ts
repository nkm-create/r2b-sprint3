/**
 * 時間割作成API
 */
import { apiClient } from './client';

// 問題分析
export interface ScaleDetails {
  teacher_count: number;
  student_count: number;
  weekly_slots: number;
}

export interface Bottleneck {
  type: string;
  day_of_week?: string;
  slot_number?: number;
  subject?: string;
  demand: number;
  supply: number;
  gap: number;
}

export interface ProblemAnalysis {
  scale: string;
  scale_details: ScaleDetails;
  difficulty: string;
  difficulty_reasons: string[];
  bottlenecks: Bottleneck[];
}

export interface RecommendedStrategy {
  initial_strategy: string;
  timeout: number;
  reason: string;
}

export interface AnalyzeResponse {
  analysis: ProblemAnalysis;
  recommended_strategy: RecommendedStrategy;
}

export interface JourneyStepStatus {
  is_ready: boolean;
  message: string;
}

export interface ScheduleJourneyStatus {
  is_ready_to_generate: boolean;
  steps: Record<string, JourneyStepStatus>;
  counts: {
    teacher_preferences: number;
    student_preferences: number;
    policies: number;
    enabled_policies: number;
    constraints: number;
  };
  missing_requirements: string[];
}

// 生成
export interface GenerateOptions {
  max_timeout_seconds?: number;
  progress_channel?: string;
}

export interface GenerateRequest {
  options?: GenerateOptions;
}

export interface GenerationResult {
  soft_constraint_rate: number;
  one_to_two_rate: number;
  unplaced_students: number;
}

export interface OrchestratorDecision {
  time_ms: number;
  decision: string;
  current_rate: number;
  reason: string;
}

export interface SolverStats {
  strategy_used: string;
  solve_time_ms: number;
  solutions_found: number;
  optimality_gap?: number;
  termination_reason: string;
}

export interface GenerateSuccessResponse {
  schedule_id: string;
  version: number;
  status: string;
  solution_status: string;
  result: GenerationResult;
  solver_stats: SolverStats;
  orchestrator_decisions: OrchestratorDecision[];
  next_action: string;
}

// 説明
export interface ExplanationSummary {
  overall: string;
  key_points: string[];
}

export interface BottleneckExplanation {
  main_bottleneck: string;
  detail: string;
  structural_cause: boolean;
}

export interface TradeOff {
  description: string;
  pros: string[];
  cons: string[];
  recommendation: string;
}

export interface ExplanationResponse {
  summary: ExplanationSummary;
  bottleneck_explanation: BottleneckExplanation;
  trade_offs: TradeOff[];
}

// What-if
export interface WhatIfRequest {
  question: string;
}

export interface WhatIfResponse {
  analysis: {
    feasible: boolean;
    impact: Record<string, unknown>;
  };
  explanation: string;
}

// カレンダービュー
export interface ScheduleMetrics {
  soft_constraint_rate: number;
  one_to_two_rate: number;
  unplaced_count: number;
}

export interface PersonInfo {
  id: string;
  name: string;
  subject?: string;
}

export interface SlotInfo {
  slot_id: string;
  teacher: PersonInfo;
  student1: PersonInfo;
  student2?: PersonInfo;
  slot_type: string;
  status: string;
  has_issue: boolean;
  issues?: string[];
}

export interface CellInfo {
  day_of_week: string;
  slot_number: number;
  slots: SlotInfo[];
  status: string;
  issues: string[];
}

export interface UnplacedStudent {
  student_id: string;
  student_name: string;
  subject: string;
  required_slots: number;
  reason: string;
}

export interface CalendarViewResponse {
  schedule_id: string;
  status: string;
  solution_status: string;
  metrics: ScheduleMetrics;
  time_slots: Record<string, { slot_number: number; start_time: string; end_time: string }[]>;
  cells: CellInfo[];
  unplaced_students: UnplacedStudent[];
}

// 移動
export interface MovableTarget {
  day_of_week: string;
  slot_number: number;
  feasibility: string;
  violations: string[];
  impact: Record<string, unknown>;
}

export interface GenerationProgressEvent {
  type: 'progress' | 'complete' | 'error';
  solutions_found?: number;
  current_rate?: number;
  elapsed_ms?: number;
  strategy?: string;
  status?: string;
  final_rate?: number;
  termination_reason?: string;
  error?: string;
}

export interface MovableTargetsResponse {
  targets: MovableTarget[];
}

export interface MoveSlotRequest {
  target_day_of_week: string;
  target_slot_number: number;
  force?: boolean;
}

export interface MoveSlotResponse {
  success: boolean;
  new_slot_id?: string;
  updated_metrics?: ScheduleMetrics;
  error?: string;
}

// 確定
export interface ConfirmRequest {
  force?: boolean;
}

export interface ConfirmResponse {
  schedule_id: string;
  status: string;
  confirmed_at: string;
  message: string;
}

// 出力
export interface ExportRequest {
  format: 'pdf' | 'csv';
  type?: string;
  options?: {
    paper_size?: string;
    orientation?: string;
  };
}

export interface ExportResponse {
  download_url: string;
  expires_at: string;
  file_name: string;
}

// 一覧
export interface ScheduleListItem {
  schedule_id: string;
  version: number;
  status: string;
  soft_constraint_rate?: number;
  one_to_two_rate?: number;
  created_at: string;
  confirmed_at?: string;
}

export interface ScheduleListResponse {
  data: ScheduleListItem[];
}

// API関数
export async function analyzeSchedule(
  classroomId: string,
  termId: string
): Promise<AnalyzeResponse> {
  const response = await apiClient.post<AnalyzeResponse>(
    `/classrooms/${classroomId}/terms/${termId}/schedules/analyze`
  );
  return response.data;
}

export async function getScheduleJourneyStatus(
  classroomId: string,
  termId: string
): Promise<ScheduleJourneyStatus> {
  const response = await apiClient.get<ScheduleJourneyStatus>(
    `/classrooms/${classroomId}/terms/${termId}/schedules/journey-status`
  );
  return response.data;
}

export async function generateSchedule(
  classroomId: string,
  termId: string,
  data?: GenerateRequest
): Promise<GenerateSuccessResponse> {
  const response = await apiClient.post<GenerateSuccessResponse>(
    `/classrooms/${classroomId}/terms/${termId}/schedules/generate`,
    data || {}
  );
  return response.data;
}

export async function listSchedules(
  classroomId: string,
  termId: string
): Promise<ScheduleListResponse> {
  const response = await apiClient.get<ScheduleListResponse>(
    `/classrooms/${classroomId}/terms/${termId}/schedules`
  );
  return response.data;
}

export async function getExplanation(
  scheduleId: string
): Promise<ExplanationResponse> {
  const response = await apiClient.get<ExplanationResponse>(
    `/schedules/${scheduleId}/explanation`
  );
  return response.data;
}

export async function whatIfAnalysis(
  scheduleId: string,
  data: WhatIfRequest
): Promise<WhatIfResponse> {
  const response = await apiClient.post<WhatIfResponse>(
    `/schedules/${scheduleId}/what-if`,
    data
  );
  return response.data;
}

export async function getCalendarView(
  scheduleId: string,
  viewType?: string,
  filterId?: string
): Promise<CalendarViewResponse> {
  const params = new URLSearchParams();
  if (viewType) params.append('view_type', viewType);
  if (filterId) params.append('filter_id', filterId);

  const response = await apiClient.get<CalendarViewResponse>(
    `/schedules/${scheduleId}/calendar-view?${params.toString()}`
  );
  return response.data;
}

export async function getMovableTargets(
  scheduleId: string,
  slotId: string
): Promise<MovableTargetsResponse> {
  const response = await apiClient.get<MovableTargetsResponse>(
    `/schedules/${scheduleId}/slots/${slotId}/movable-targets`
  );
  return response.data;
}

export async function moveSlot(
  scheduleId: string,
  slotId: string,
  data: MoveSlotRequest
): Promise<MoveSlotResponse> {
  const response = await apiClient.put<MoveSlotResponse>(
    `/schedules/${scheduleId}/slots/${slotId}/move`,
    data
  );
  return response.data;
}

export async function confirmSchedule(
  scheduleId: string,
  data?: ConfirmRequest
): Promise<ConfirmResponse> {
  const response = await apiClient.post<ConfirmResponse>(
    `/schedules/${scheduleId}/confirm`,
    data || {}
  );
  return response.data;
}

export async function exportSchedule(
  scheduleId: string,
  data: ExportRequest
): Promise<ExportResponse> {
  const response = await apiClient.post<ExportResponse>(
    `/schedules/${scheduleId}/export`,
    data
  );
  return response.data;
}

export function createGenerationProgressSocket(
  progressId: string
): WebSocket {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsBase = apiUrl.replace(/^http/, 'ws');
  return new WebSocket(`${wsBase}/api/schedules/${progressId}/progress`);
}
