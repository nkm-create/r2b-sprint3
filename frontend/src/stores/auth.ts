import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * ユーザー情報の型
 */
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'system_admin' | 'area_manager' | 'classroom_manager';
  status: 'active' | 'inactive' | 'pending';
  force_password_change: boolean;
  classroom_ids?: string[];
  area_ids?: string[];
}

/**
 * 認証状態の型
 */
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // アクション
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  login: (user: User) => void;
  logout: () => void;
}

/**
 * 認証ストア
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,

      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
        }),

      setLoading: (loading) =>
        set({
          isLoading: loading,
        }),

      login: (user) =>
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
        }),

      logout: () => {
        // ローカルストレージからトークンを削除
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setLoading(false);
      },
    }
  )
);
