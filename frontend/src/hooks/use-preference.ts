import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useImportPreferences(classroomId: string, termId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      type,
      file,
    }: {
      type: 'teacher' | 'student';
      file: File;
    }) => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiClient.post(
        `/classrooms/${classroomId}/terms/${termId}/preferences/${type}/import`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      return res.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['master-status', classroomId, termId] });
    },
  });
}
