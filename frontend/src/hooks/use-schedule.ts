import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useScheduleJourneyStatus(
  classroomId: string | undefined,
  termId: string | undefined
) {
  return useQuery({
    queryKey: ['schedule-journey-status', classroomId, termId],
    queryFn: async () => {
      const res = await apiClient.get(
        `/classrooms/${classroomId}/terms/${termId}/schedules/journey-status`
      );
      return res.data;
    },
    enabled: !!classroomId && !!termId,
  });
}

export function useScheduleList(classroomId: string | undefined, termId: string | undefined) {
  return useQuery({
    queryKey: ['schedules', classroomId, termId],
    queryFn: async () => {
      const res = await apiClient.get(
        `/classrooms/${classroomId}/terms/${termId}/schedules`
      );
      return res.data;
    },
    enabled: !!classroomId && !!termId,
  });
}

export function useAnalyzeSchedule(classroomId: string, termId: string) {
  return useMutation({
    mutationFn: async () => {
      const res = await apiClient.post(
        `/classrooms/${classroomId}/terms/${termId}/schedules/analyze`
      );
      return res.data;
    },
  });
}

export function useGenerateSchedule(classroomId: string, termId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: Record<string, unknown>) => {
      const res = await apiClient.post(
        `/classrooms/${classroomId}/terms/${termId}/schedules/generate`,
        params
      );
      return res.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['schedules', classroomId, termId] });
    },
  });
}

export function useCalendarView(scheduleId: string | undefined) {
  return useQuery({
    queryKey: ['calendar-view', scheduleId],
    queryFn: async () => {
      const res = await apiClient.get(`/schedules/${scheduleId}/calendar-view`);
      return res.data;
    },
    enabled: !!scheduleId,
  });
}

export function useExplanation(scheduleId: string | undefined) {
  return useQuery({
    queryKey: ['explanation', scheduleId],
    queryFn: async () => {
      const res = await apiClient.get(`/schedules/${scheduleId}/explanation`);
      return res.data;
    },
    enabled: !!scheduleId,
  });
}

export function useConfirmSchedule(classroomId: string, termId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (scheduleId: string) => {
      const res = await apiClient.post(`/schedules/${scheduleId}/confirm`);
      return res.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['schedules', classroomId, termId] });
    },
  });
}

export function useExportSchedule() {
  return useMutation({
    mutationFn: async ({
      scheduleId,
      format,
    }: {
      scheduleId: string;
      format: string;
    }) => {
      const res = await apiClient.post(
        `/schedules/${scheduleId}/export`,
        { format },
        { responseType: 'blob' }
      );
      return res.data;
    },
  });
}

export function useMoveSlot(scheduleId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: Record<string, unknown>) => {
      const res = await apiClient.post(`/schedules/${scheduleId}/slots/move`, params);
      return res.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['calendar-view', scheduleId] });
    },
  });
}

export function useWhatIfAnalysis(scheduleId: string | undefined) {
  return useMutation({
    mutationFn: async (params: Record<string, unknown>) => {
      const res = await apiClient.post(`/schedules/${scheduleId}/what-if`, params);
      return res.data;
    },
  });
}
