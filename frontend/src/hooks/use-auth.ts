'use client';

import { useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, getErrorMessage } from '@/lib/api/client';
import { useAuthStore, User } from '@/stores/auth';
import { useToast } from '@/hooks/use-toast';

/**
 * ログインリクエストの型
 */
interface LoginRequest {
  email: string;
  password: string;
}

/**
 * ログインレスポンスの型
 */
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  force_password_change: boolean;
}

/**
 * パスワード変更リクエストの型
 */
interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

/**
 * 認証フック
 */
export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { user, isAuthenticated, isLoading, login, logout, setLoading } =
    useAuthStore();

  /**
   * 現在のユーザー情報を取得
   */
  const { refetch: fetchCurrentUser } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await apiClient.get<User>('/auth/me');
      return response.data;
    },
    enabled: false, // 手動で実行
    retry: false,
  });

  /**
   * 初期化時にユーザー情報を取得
   */
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const result = await fetchCurrentUser();
        if (result.data) {
          login(result.data);
        }
      } catch {
        logout();
      }
    };

    initAuth();
  }, [fetchCurrentUser, login, logout, setLoading]);

  /**
   * ログイン処理
   */
  const loginMutation = useMutation({
    mutationFn: async (data: LoginRequest) => {
      const response = await apiClient.post<LoginResponse>('/auth/login', data);
      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      login(data.user);

      toast({
        title: 'ログイン成功',
        description: `${data.user.name}さん、ようこそ`,
      });

      if (data.force_password_change) {
        router.push('/password/change');
      } else {
        router.push('/dashboard');
      }
    },
    onError: (error) => {
      toast({
        variant: 'destructive',
        title: 'ログインエラー',
        description: getErrorMessage(error),
      });
    },
  });

  /**
   * ログアウト処理
   */
  const logoutMutation = useMutation({
    mutationFn: async () => {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      }
    },
    onSuccess: () => {
      logout();
      queryClient.clear();
      router.push('/login');
      toast({
        title: 'ログアウトしました',
      });
    },
    onError: () => {
      // エラーでもログアウト処理を実行
      logout();
      queryClient.clear();
      router.push('/login');
    },
  });

  /**
   * パスワード変更処理
   */
  const changePasswordMutation = useMutation({
    mutationFn: async (data: ChangePasswordRequest) => {
      await apiClient.post('/auth/password/change', data);
    },
    onSuccess: () => {
      toast({
        title: 'パスワードを変更しました',
        description: '新しいパスワードでログインしてください',
      });
      logout();
      router.push('/login');
    },
    onError: (error) => {
      toast({
        variant: 'destructive',
        title: 'パスワード変更エラー',
        description: getErrorMessage(error),
      });
    },
  });

  return {
    user,
    isAuthenticated,
    isLoading,
    login: loginMutation.mutate,
    logout: logoutMutation.mutate,
    changePassword: changePasswordMutation.mutate,
    isLoginPending: loginMutation.isPending,
    isLogoutPending: logoutMutation.isPending,
    isChangePasswordPending: changePasswordMutation.isPending,
  };
}

/**
 * 認証必須ページ用フック
 */
export function useRequireAuth() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  return { isAuthenticated, isLoading };
}

/**
 * 特定のロールが必要なページ用フック
 */
export function useRequireRole(allowedRoles: User['role'][]) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const { toast } = useToast();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.replace('/login');
      } else if (user && !allowedRoles.includes(user.role)) {
        toast({
          variant: 'destructive',
          title: 'アクセス権限がありません',
          description: 'このページにアクセスする権限がありません',
        });
        router.replace('/dashboard');
      }
    }
  }, [isAuthenticated, isLoading, user, allowedRoles, router, toast]);

  return { user, isAuthenticated, isLoading };
}
