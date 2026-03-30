/**
 * 条件設定API（スタブ）
 */
import { apiClient } from './client';

export interface ConstraintValue {
  type: string;
  target_id?: string;
  value: unknown;
}

export interface Policy {
  use_preferred_teacher: boolean;
  use_gender_preference: boolean;
}

export interface Constraint {
  constraint_id: string;
  type: string;
  target_id?: string;
  value: unknown;
}

export interface MasterStatus {
  teacher_count: number;
  student_count: number;
  teacher_preferences: number;
  student_preferences: number;
}

export async function getPolicies(classroomId: string, termId: string): Promise<Policy> {
  const res = await apiClient.get(`/classrooms/${classroomId}/terms/${termId}/policies`);
  return res.data;
}

export async function updatePolicies(
  classroomId: string,
  termId: string,
  data: Policy
): Promise<Policy> {
  const res = await apiClient.put(`/classrooms/${classroomId}/terms/${termId}/policies`, data);
  return res.data;
}

export async function getConstraints(classroomId: string, termId: string): Promise<Constraint[]> {
  const res = await apiClient.get(`/classrooms/${classroomId}/terms/${termId}/constraints`);
  return res.data;
}

export async function createConstraints(
  classroomId: string,
  termId: string,
  data: ConstraintValue[]
): Promise<void> {
  await apiClient.post(`/classrooms/${classroomId}/terms/${termId}/constraints`, data);
}

export async function getMasterStatus(
  classroomId: string,
  termId: string
): Promise<MasterStatus> {
  const res = await apiClient.get(`/classrooms/${classroomId}/terms/${termId}/master-status`);
  return res.data;
}
