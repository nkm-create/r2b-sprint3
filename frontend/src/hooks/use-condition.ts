import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import {
  getPolicies,
  updatePolicies,
  getConstraints,
  createConstraints,
  getMasterStatus,
  type Policy,
  type ConstraintValue,
} from '@/lib/api/condition';

export interface Term {
  term_id: string;
  term_name: string;
  start_date: string;
  end_date: string;
  status: string;
}

export function useTerms(classroomId: string | undefined) {
  return useQuery<Term[]>({
    queryKey: ['terms', classroomId],
    queryFn: async () => {
      const res = await apiClient.get(`/classrooms/${classroomId}/terms`);
      return res.data;
    },
    enabled: !!classroomId,
  });
}

export function usePolicies(classroomId: string | undefined, termId: string | undefined) {
  return useQuery<Policy>({
    queryKey: ['policies', classroomId, termId],
    queryFn: () => getPolicies(classroomId!, termId!),
    enabled: !!classroomId && !!termId,
  });
}

export function useUpdatePolicies(classroomId: string, termId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Policy) => updatePolicies(classroomId, termId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['policies', classroomId, termId] });
    },
  });
}

export function useConstraints(classroomId: string | undefined, termId: string | undefined) {
  return useQuery({
    queryKey: ['constraints', classroomId, termId],
    queryFn: () => getConstraints(classroomId!, termId!),
    enabled: !!classroomId && !!termId,
  });
}

export function useCreateConstraints(classroomId: string, termId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ConstraintValue[]) => createConstraints(classroomId, termId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['constraints', classroomId, termId] });
    },
  });
}

export function useMasterStatus(classroomId: string | undefined, termId: string | undefined) {
  return useQuery({
    queryKey: ['master-status', classroomId, termId],
    queryFn: () => getMasterStatus(classroomId!, termId!),
    enabled: !!classroomId && !!termId,
  });
}
