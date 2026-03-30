import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export interface Teacher {
  teacher_id: string;
  name: string;
}

export function useTeachers(classroomId: string | undefined) {
  return useQuery<Teacher[]>({
    queryKey: ['teachers', classroomId],
    queryFn: async () => {
      const res = await apiClient.get(`/classrooms/${classroomId}/teachers`);
      return res.data;
    },
    enabled: !!classroomId,
  });
}
