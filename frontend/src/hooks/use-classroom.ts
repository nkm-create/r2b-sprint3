import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export interface Classroom {
  classroom_id: string;
  classroom_name: string;
  classroom_code: string;
}

export function useClassrooms() {
  return useQuery<Classroom[]>({
    queryKey: ['classrooms'],
    queryFn: async () => {
      const res = await apiClient.get('/classrooms');
      return res.data;
    },
  });
}
