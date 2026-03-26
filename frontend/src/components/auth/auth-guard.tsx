'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';

// 開発モード: 認証をバイパス
const DEV_BYPASS_AUTH = process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true';

interface AuthGuardProps {
  children: React.ReactNode;
  requiredRoles?: Array<'system_admin' | 'area_manager' | 'classroom_manager'>;
}

/**
 * 認証保護コンポーネント
 * 認証が必要なページをラップして使用
 */
export function AuthGuard({ children, requiredRoles }: AuthGuardProps) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();

  // 開発モードでバイパスが有効な場合は認証チェックをスキップ
  if (DEV_BYPASS_AUTH) {
    return <>{children}</>;
  }

  useEffect(() => {
    if (!isLoading) {
      // 未認証の場合はログインページへ
      if (!isAuthenticated) {
        router.replace('/login');
        return;
      }

      // ロール制限がある場合
      if (requiredRoles && user && !requiredRoles.includes(user.role)) {
        router.replace('/dashboard');
      }
    }
  }, [isAuthenticated, isLoading, user, requiredRoles, router]);

  // ローディング中
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">読み込み中...</p>
        </div>
      </div>
    );
  }

  // 未認証の場合は何も表示しない（リダイレクト中）
  if (!isAuthenticated) {
    return null;
  }

  // ロール制限に引っかかる場合は何も表示しない
  if (requiredRoles && user && !requiredRoles.includes(user.role)) {
    return null;
  }

  return <>{children}</>;
}

/**
 * ゲスト専用コンポーネント
 * 未認証ユーザーのみアクセス可能なページをラップして使用
 */
export function GuestGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // ローディング中
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  // 認証済みの場合は何も表示しない
  if (isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
