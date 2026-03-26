/**
 * ダッシュボード用カスタムフック
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDashboard,
  getNotifications,
  markNotificationAsRead,
  type DashboardResponse,
  type NotificationResponse,
} from '@/lib/api/dashboard';

export const dashboardKeys = {
  all: ['dashboard'] as const,
  detail: (classroomId: string) => [...dashboardKeys.all, classroomId] as const,
  notifications: (classroomId: string) =>
    [...dashboardKeys.detail(classroomId), 'notifications'] as const,
};

export function useDashboard(classroomId: string | undefined) {
  return useQuery<DashboardResponse>({
    queryKey: dashboardKeys.detail(classroomId ?? ''),
    queryFn: () => getDashboard(classroomId!),
    enabled: !!classroomId,
    staleTime: 30 * 1000, // 30秒間はキャッシュを使用
    refetchInterval: 60 * 1000, // 1分ごとに自動更新
  });
}

export function useNotifications(classroomId: string | undefined) {
  return useQuery<NotificationResponse>({
    queryKey: dashboardKeys.notifications(classroomId ?? ''),
    queryFn: () => getNotifications(classroomId!),
    enabled: !!classroomId,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}

export function useMarkNotificationAsRead(classroomId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) =>
      markNotificationAsRead(classroomId, notificationId),
    onSuccess: () => {
      // 通知とダッシュボードのキャッシュを無効化
      queryClient.invalidateQueries({
        queryKey: dashboardKeys.notifications(classroomId),
      });
      queryClient.invalidateQueries({
        queryKey: dashboardKeys.detail(classroomId),
      });
    },
  });
}
